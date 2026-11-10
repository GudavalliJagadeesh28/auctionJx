import asyncio
import json
import secrets
import string
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from players import PLAYERS, public_player


BASE_DIR = Path(__file__).resolve().parent
ROOM_CODE_ALPHABET = string.ascii_uppercase + string.digits


@dataclass(slots=True)
class Participant:
    token: str
    name: str
    budget_lakh: int
    is_host: bool = False
    spent_lakh: int = 0
    squad: list[dict] = field(default_factory=list)


@dataclass(slots=True)
class Room:
    code: str
    budget_lakh: int
    bid_seconds: int
    host_token: str
    visibility: str = "private"
    participants: dict[str, Participant] = field(default_factory=dict)
    connections: dict[str, WebSocket] = field(default_factory=dict)
    phase: str = "lobby"
    lot_index: int = -1
    seconds_left: int = 0
    current_bid_lakh: int = 0
    highest_bidder: str | None = None
    sold: list[dict] = field(default_factory=list)
    timer_task: asyncio.Task | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class AuctionManager:
    def __init__(self) -> None:
        self.rooms: dict[str, Room] = {}
        self.lock = asyncio.Lock()

    async def create_room(
        self, host_name: str, budget_lakh: int, bid_seconds: int, visibility: str
    ) -> tuple[Room, str]:
        async with self.lock:
            code = self._new_code()
            token = secrets.token_urlsafe(24)
            room = Room(code, budget_lakh, bid_seconds, token, visibility)
            room.participants[token] = Participant(token, host_name, budget_lakh, is_host=True)
            self.rooms[code] = room
            return room, token

    def _new_code(self) -> str:
        while True:
            code = "".join(secrets.choice(ROOM_CODE_ALPHABET) for _ in range(6))
            if code not in self.rooms:
                return code

    @staticmethod
    def bid_increment(current_lakh: int) -> int:
        return 5 if current_lakh < 100 else 10 if current_lakh < 500 else 20

    def state(self, room: Room, viewer_token: str) -> dict:
        player = PLAYERS[room.lot_index] if 0 <= room.lot_index < len(PLAYERS) else None
        participants = [{
            "name": participant.name,
            "budget_lakh": participant.budget_lakh,
            "spent_lakh": participant.spent_lakh,
            "remaining_lakh": participant.budget_lakh - participant.spent_lakh,
            "squad": participant.squad,
            "is_host": participant.is_host,
            "online": participant.token in room.connections,
        } for participant in room.participants.values()]
        viewer = room.participants.get(viewer_token)
        return {
            "code": room.code, "phase": room.phase, "bid_seconds": room.bid_seconds,
            "visibility": room.visibility,
            "seconds_left": room.seconds_left, "lot_number": room.lot_index + 1 if player else 0,
            "total_lots": len(PLAYERS), "player": public_player(player) if player else None,
            "current_bid_lakh": room.current_bid_lakh,
            "next_bid_lakh": room.current_bid_lakh + self.bid_increment(room.current_bid_lakh),
            "highest_bidder": next((person.name for person in room.participants.values() if person.token == room.highest_bidder), None),
            "participants": participants, "sold": room.sold,
            "is_host": bool(viewer and viewer.is_host),
            "viewer_name": viewer.name if viewer else "",
            "viewer_remaining_lakh": viewer.budget_lakh - viewer.spent_lakh if viewer else 0,
            "is_highest_bidder": room.highest_bidder == viewer_token,
            "players_online": len(room.connections),
        }

    def public_rooms(self) -> list[dict]:
        return [{
            "code": room.code,
            "host": room.participants[room.host_token].name,
            "players_online": len(room.connections),
            "phase": room.phase,
            "bid_seconds": room.bid_seconds,
        } for room in self.rooms.values() if room.visibility == "public" and room.phase != "complete"]

    async def broadcast(self, room: Room) -> None:
        async def send_state(token: str, websocket: WebSocket) -> str | None:
            try:
                await websocket.send_json({"type": "state", "state": self.state(room, token)})
                return None
            except Exception:
                return token

        failed_tokens = await asyncio.gather(*(
            send_state(token, websocket) for token, websocket in list(room.connections.items())
        ))
        for token in failed_tokens:
            if token:
                room.connections.pop(token, None)

    async def finish_lot(self, room: Room) -> None:
        player = PLAYERS[room.lot_index]
        winner = room.participants.get(room.highest_bidder) if room.highest_bidder else None
        if winner:
            winner.spent_lakh += room.current_bid_lakh
            winner.squad.append({"name": player.name, "role": player.role, "price_lakh": room.current_bid_lakh})
            room.sold.append({"name": player.name, "role": player.role, "price_lakh": room.current_bid_lakh, "winner": winner.name})
            room.phase = "result_sold"
        else:
            room.sold.append({"name": player.name, "role": player.role, "price_lakh": 0, "winner": None})
            room.phase = "result_unsold"
        room.seconds_left = 0

    async def run_timer(self, room: Room, lot_index: int) -> None:
        try:
            while True:
                await asyncio.sleep(1)
                async with room.lock:
                    if room.phase != "auction" or room.lot_index != lot_index:
                        return
                    room.seconds_left -= 1
                    if room.seconds_left <= 0:
                        await self.finish_lot(room)
                        await self.broadcast(room)
                        return
                    await self.broadcast(room)
        except asyncio.CancelledError:
            return


manager = AuctionManager()
app = FastAPI(title="Boundary Auction", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/")
async def home() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/players")
async def get_players() -> dict:
    return {"players": [public_player(player) for player in PLAYERS], "count": len(PLAYERS)}


@app.get("/api/rooms")
async def get_public_rooms() -> dict:
    rooms = manager.public_rooms()
    return {"rooms": rooms, "count": len(rooms)}


@app.post("/api/rooms")
async def create_room(payload: dict) -> dict:
    name = str(payload.get("name", "")).strip()[:24]
    try:
        budget_crores = float(payload.get("budget_crores", 100))
        bid_seconds = int(payload.get("bid_seconds", 20))
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Budget and timer must be valid numbers") from None
    if not name:
        raise HTTPException(status_code=422, detail="Enter a team name")
    if not 1 <= budget_crores <= 200:
        raise HTTPException(status_code=422, detail="Budget must be between 1 and 200 crore")
    if not 5 <= bid_seconds <= 90:
        raise HTTPException(status_code=422, detail="Bid timer must be between 5 and 90 seconds")
    visibility = str(payload.get("visibility", "private")).lower()
    if visibility not in {"private", "public"}:
        raise HTTPException(status_code=422, detail="Room must be public or private")
    room, token = await manager.create_room(name, round(budget_crores * 100), bid_seconds, visibility)
    return {"code": room.code, "token": token}


@app.websocket("/ws/{code}")
async def room_socket(websocket: WebSocket, code: str, name: str = "", token: str = "") -> None:
    room = manager.rooms.get(code.upper())
    await websocket.accept()
    if not room:
        await websocket.close(code=4404, reason="Room not found")
        return
    participant_token = token if token in room.participants else secrets.token_urlsafe(24)
    if participant_token not in room.participants:
        participant_name = name.strip()[:24] or "Team owner"
        if any(existing.name.casefold() == participant_name.casefold() for existing in room.participants.values()):
            await websocket.close(code=4409, reason="Team name already in use")
            return
        room.participants[participant_token] = Participant(participant_token, participant_name, room.budget_lakh)
    participant = room.participants[participant_token]
    room.connections[participant_token] = websocket
    await websocket.send_json({"type": "identity", "token": participant_token})
    async with room.lock:
        await manager.broadcast(room)
    try:
        while True:
            message = json.loads(await websocket.receive_text())
            async with room.lock:
                action = message.get("type")
                if action == "start" and participant.is_host and room.phase == "lobby":
                    room.phase = "auction"
                    room.lot_index = 0
                    room.current_bid_lakh = PLAYERS[0].base_price_lakh
                    room.seconds_left = room.bid_seconds
                    room.timer_task = asyncio.create_task(manager.run_timer(room, room.lot_index))
                elif action == "pause" and participant.is_host and room.phase == "auction":
                    room.phase = "paused"
                    if room.timer_task and not room.timer_task.done():
                        room.timer_task.cancel()
                elif action == "resume" and participant.is_host and room.phase == "paused":
                    room.phase = "auction"
                    room.timer_task = asyncio.create_task(manager.run_timer(room, room.lot_index))
                elif action == "visibility" and participant.is_host and message.get("visibility") in {"public", "private"}:
                    room.visibility = message["visibility"]
                elif action == "bid" and room.phase == "auction" and room.highest_bidder != participant_token:
                    next_bid = room.current_bid_lakh + manager.bid_increment(room.current_bid_lakh)
                    if participant.budget_lakh - participant.spent_lakh >= next_bid:
                        room.current_bid_lakh = next_bid
                        room.highest_bidder = participant_token
                        room.seconds_left = room.bid_seconds
                elif action == "next" and participant.is_host and room.phase in {"result_sold", "result_unsold"}:
                    if room.timer_task and not room.timer_task.done():
                        room.timer_task.cancel()
                    room.lot_index += 1
                    if room.lot_index >= len(PLAYERS):
                        room.phase = "complete"
                    else:
                        room.phase = "auction"
                        room.current_bid_lakh = PLAYERS[room.lot_index].base_price_lakh
                        room.highest_bidder = None
                        room.seconds_left = room.bid_seconds
                        room.timer_task = asyncio.create_task(manager.run_timer(room, room.lot_index))
                await manager.broadcast(room)
    except (WebSocketDisconnect, json.JSONDecodeError):
        pass
    finally:
        if room.connections.get(participant_token) is websocket:
            room.connections.pop(participant_token, None)
            async with room.lock:
                await manager.broadcast(room)