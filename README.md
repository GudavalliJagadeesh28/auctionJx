# Boundary Auction

A browser-based IPL cricket auction room with a curated 100-player pool, private room codes, configurable team purses and bid timers, and live multiplayer bidding.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000. Create a private room and share its six-character code, or create a public room that appears in the room directory. Rooms have human players only; the app does not create or add bots. The host can switch room visibility, pause/resume the clock, start the auction, and advance to the next lot after each player is sold or goes unsold. The room shows how many players are connected. Bids, purses, and sale results are validated and managed by the server.

The 100-player roster and base prices are starter examples, not current official IPL registrations, live statistics, or official valuations. Player country, role, and playing style are included as roster details.

Room state is held in memory so the app stays lightweight and requires no database setup. Run one Uvicorn worker; rooms are lost when the process restarts. For a public multi-instance deployment, move room state and broadcasts to a shared store such as Redis and add authentication/rate limiting.
