const $ = (selector) => document.querySelector(selector);
const state = { players: [], role: "All", search: "", socket: null, roomCode: "", token: "", timerTotal: 20, lastPhase: "" };
const money = (lakh) => `₹${(lakh / 100).toFixed(2)}`;

function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(showToast.timeout);
  showToast.timeout = setTimeout(() => toast.classList.remove("show"), 2200);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character]);
}

function renderPlayers() {
  const needle = state.search.trim().toLowerCase();
  const matches = state.players.filter((player) => {
    const roleMatch = state.role === "All" || player.role === state.role;
    const searchMatch = !needle || `${player.name} ${player.country} ${player.style} ${player.role}`.toLowerCase().includes(needle);
    return roleMatch && searchMatch;
  });
  $("#player-count").textContent = matches.length;
  $("#player-grid").innerHTML = matches.map((player) => `<article class="player-item"><div class="player-item-top"><span class="player-role-tag">${escapeHtml(player.role)}</span><span class="player-price">${money(player.base_price_lakh)} cr base</span></div><h3 title="${escapeHtml(player.name)}">${escapeHtml(player.name)}</h3><div class="player-style">${escapeHtml(player.style)}</div><div class="player-country">${escapeHtml(player.country)}</div></article>`).join("");
  $("#empty-search").hidden = matches.length > 0;
}

async function loadPlayers() {
  try {
    const response = await fetch("/api/players");
    if (!response.ok) throw new Error("Could not load players");
    const data = await response.json();
    state.players = data.players;
    renderPlayers();
  } catch {
    $("#player-grid").innerHTML = '<p class="muted-copy">The player list could not be loaded. Refresh to try again.</p>';
  }
}

async function loadPublicRooms() {
  try {
    const response = await fetch("/api/rooms");
    if (!response.ok) throw new Error("Could not load rooms");
    const data = await response.json();
    $("#public-room-count").textContent = `${data.count} ${data.count === 1 ? "ROOM" : "ROOMS"}`;
    $("#public-room-list").innerHTML = data.rooms.length ? data.rooms.map((room) => `<article class="public-room"><div class="public-room-info"><h3>${escapeHtml(room.host)}'s room</h3><p>${room.players_online} playing · ${room.phase === "lobby" ? "Waiting" : room.phase === "paused" ? "Paused" : "Auction live"} · ${room.bid_seconds}s bids</p><span class="public-room-code">${room.code}</span></div><button class="button button-secondary public-join" data-room-code="${room.code}">Join room <span class="arrow">↗</span></button></article>`).join("") : '<p class="muted-copy">No public rooms yet.</p>';
  } catch {
    $("#public-room-list").innerHTML = '<p class="muted-copy">Public rooms could not be loaded. Try refreshing.</p>';
  }
}

function openRoom(code, name, token = "") {
  state.roomCode = code.toUpperCase();
  state.token = token || localStorage.getItem(`boundary:${state.roomCode}`) || "";
  $("#lobby-view").hidden = true;
  $("#room-view").hidden = false;
  $("#room-code-display").textContent = state.roomCode;
  $("#room-title").textContent = "Room " + state.roomCode;
  history.replaceState(null, "", `#room-${state.roomCode}`);
  const scheme = location.protocol === "https:" ? "wss:" : "ws:";
  const params = new URLSearchParams({ name, token: state.token });
  const socket = new WebSocket(`${scheme}//${location.host}/ws/${state.roomCode}?${params}`);
  state.socket = socket;
  socket.addEventListener("open", () => { $("#connection-status").textContent = "CONNECTED"; });
  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.type === "identity") {
      state.token = message.token;
      localStorage.setItem(`boundary:${state.roomCode}`, state.token);
    } else if (message.type === "state") renderRoom(message.state);
  });
  socket.addEventListener("close", (event) => {
    $("#connection-status").textContent = event.code === 4404 ? "ROOM NOT FOUND" : "DISCONNECTED";
    if (event.code === 4404) showToast("That room code was not found.");
    if (event.code === 4409) showToast("That team name is already in this room.");
  });
  socket.addEventListener("error", () => { $("#connection-status").textContent = "RECONNECT NEEDED"; });
}

function renderRoom(room) {
  const wasResult = state.lastPhase === "result_sold" || state.lastPhase === "result_unsold";
  state.lastPhase = room.phase;
  $("#room-subtitle").textContent = `${room.players_online} playing now · ${room.participants.length} teams · ${money(room.participants[0]?.budget_lakh || 0)} crore purse · ${room.bid_seconds}s bids`;
  $("#room-visibility-badge").textContent = room.visibility.toUpperCase();
  $("#host-controls").hidden = !room.is_host;
  if (document.activeElement !== $("#room-visibility")) $("#room-visibility").value = room.visibility;
  $("#save-visibility").disabled = $("#room-visibility").value === room.visibility;
  $("#toggle-pause").hidden = !room.is_host || !["auction", "paused"].includes(room.phase);
  $("#toggle-pause").dataset.action = room.phase === "paused" ? "resume" : "pause";
  $("#toggle-pause").textContent = room.phase === "paused" ? "Resume room" : "Pause room";
  $("#start-auction").hidden = !room.is_host || room.phase !== "lobby";
  $("#lobby-waiting").hidden = room.phase !== "lobby";
  $("#paused-banner").hidden = room.phase !== "paused";
  $("#auction-card").hidden = !["auction", "paused", "result_sold", "result_unsold"].includes(room.phase);
  $("#complete-state").hidden = room.phase !== "complete";
  $("#lot-label").textContent = room.phase === "lobby" ? "ROOM LOBBY" : room.phase === "complete" ? "AUCTION COMPLETE" : room.phase === "paused" ? "AUCTION PAUSED" : "PLAYER ON THE BLOCK";
  $("#lot-count").textContent = room.lot_number ? `LOT ${String(room.lot_number).padStart(2, "0")} / ${room.total_lots}` : "";
  $("#lobby-teams").innerHTML = room.participants.map((team) => `<span class="team-chip">${escapeHtml(team.name)}</span>`).join("");
  $("#team-count").textContent = room.participants.length;
  $("#team-list").innerHTML = room.participants.map((team) => `<div class="team-row"><div class="team-main"><div class="team-name">${escapeHtml(team.name)}${team.is_host ? " · HOST" : ""}</div><div class="team-sub">${team.online ? "ONLINE" : "OFFLINE"} · ${team.squad.length} PLAYERS</div></div><div class="team-purse">${money(team.remaining_lakh)}</div></div>`).join("");
  $("#sold-count").textContent = room.sold.length;
  const recentSold = room.sold.slice(-12).reverse();
  $("#sold-list").innerHTML = recentSold.length ? recentSold.map((entry) => `<div class="sold-row"><div class="sold-main"><div class="sold-name">${escapeHtml(entry.name)}</div><div class="sold-sub">${entry.winner ? escapeHtml(entry.winner) : "UNSOLD"}</div></div><div class="sold-price">${entry.winner ? `${money(entry.price_lakh)} cr` : "—"}</div></div>`).join("") : '<p class="muted-copy">The best picks will show up here.</p>';
  if (!room.player) return;
  $("#auction-role").textContent = room.player.role.toUpperCase();
  $("#auction-name").textContent = room.player.name;
  $("#auction-meta").textContent = `${room.player.country}  ·  ${room.player.style}`;
  $("#bid-amount").innerHTML = `${money(room.current_bid_lakh)}<span> cr</span>`;
  $("#bid-caption").textContent = ["auction", "paused"].includes(room.phase) ? "CURRENT BID" : room.phase === "result_sold" ? "SOLD FOR" : "BASE PRICE";
  $("#bid-leader").textContent = room.highest_bidder ? `Leading: ${room.highest_bidder}` : ["auction", "paused"].includes(room.phase) ? "Opening price · be the first to bid" : "No bids · player goes unsold";
  $("#timer-value").textContent = room.seconds_left;
  $("#timer-fill").style.width = `${Math.max(0, room.seconds_left / room.bid_seconds * 100)}%`;
  $("#timer-fill").classList.toggle("warning", room.seconds_left <= 5);
  $("#next-bid").textContent = `${money(room.next_bid_lakh)} cr`;
  const canBid = room.phase === "auction" && state.token && !room.is_highest_bidder && room.viewer_remaining_lakh >= room.next_bid_lakh;
  $("#bid-button").disabled = !canBid;
  $("#bid-button").hidden = room.phase !== "auction";
  $("#next-lot").hidden = !room.is_host || !["result_sold", "result_unsold"].includes(room.phase);
  $("#result-banner").hidden = !["result_sold", "result_unsold"].includes(room.phase);
  if (["result_sold", "result_unsold"].includes(room.phase)) {
    $("#result-banner").textContent = room.phase === "result_sold" ? `${room.highest_bidder} wins ${room.player.name} for ${money(room.current_bid_lakh)} crore.` : `${room.player.name} goes unsold.`;
    if (!wasResult) showToast(room.phase === "result_sold" ? "SOLD. The squad gets stronger." : "Unsold. The auction moves on.");
  }
}

function sendAction(type, values = {}) {
  if (state.socket?.readyState === WebSocket.OPEN) state.socket.send(JSON.stringify({ type, ...values }));
}

$("#role-filters").addEventListener("click", (event) => {
  const button = event.target.closest("button[data-role]");
  if (!button) return;
  state.role = button.dataset.role;
  document.querySelectorAll(".filter").forEach((item) => item.classList.toggle("active", item === button));
  renderPlayers();
});
$("#player-search").addEventListener("input", (event) => { state.search = event.target.value; renderPlayers(); });
$("#room-code").addEventListener("input", (event) => { event.target.value = event.target.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 6); });
$("#public-room-list").addEventListener("click", (event) => {
  const button = event.target.closest("button[data-room-code]");
  if (!button) return;
  const name = $("#join-name").value.trim();
  if (!name) {
    $("#join-error").textContent = "Enter a team name before joining a public room.";
    $("#join-name").focus();
    return;
  }
  $("#join-error").textContent = "";
  openRoom(button.dataset.roomCode, name);
});
$("#refresh-rooms").addEventListener("click", loadPublicRooms);
$("#create-room").addEventListener("click", async () => {
  const error = $("#create-error");
  error.textContent = "";
  const button = $("#create-room");
  button.disabled = true;
  try {
    const response = await fetch("/api/rooms", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: $("#host-name").value, visibility: $("#create-visibility").value, budget_crores: $("#budget").value, bid_seconds: $("#bid-time").value }) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Could not create room");
    openRoom(data.code, $("#host-name").value.trim(), data.token);
  } catch (reason) { error.textContent = reason.message; }
  finally { button.disabled = false; }
});
$("#join-room").addEventListener("click", () => {
  const code = $("#room-code").value.trim();
  if (!$("#join-name").value.trim()) { $("#join-error").textContent = "Enter a team name first."; return; }
  if (code.length !== 6) { $("#join-error").textContent = "Room codes are six characters long."; return; }
  $("#join-error").textContent = "";
  openRoom(code, $("#join-name").value.trim());
});
$("#start-auction").addEventListener("click", () => sendAction("start"));
$("#save-visibility").addEventListener("click", () => sendAction("visibility", { visibility: $("#room-visibility").value }));
$("#toggle-pause").addEventListener("click", (event) => sendAction(event.currentTarget.dataset.action));
$("#bid-button").addEventListener("click", () => sendAction("bid"));
$("#next-lot").addEventListener("click", () => sendAction("next"));
$("#leave-room").addEventListener("click", () => {
  state.socket?.close();
  state.socket = null;
  $("#room-view").hidden = true;
  $("#lobby-view").hidden = false;
  history.replaceState(null, "", location.pathname);
});
$("#copy-code").addEventListener("click", async () => {
  try { await navigator.clipboard.writeText(state.roomCode); showToast("Room code copied."); }
  catch { showToast(`Room code: ${state.roomCode}`); }
});
loadPlayers();
loadPublicRooms();
setInterval(loadPublicRooms, 10000);