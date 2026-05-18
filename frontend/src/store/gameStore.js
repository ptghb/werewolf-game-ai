import { create } from "zustand";

const useGameStore = create((set, get) => ({
  inGame: false,
  roomCode: "",
  playerId: "",
  isHost: false,
  players: [],
  hostId: "",
  phase: "lobby",
  day: 0,
  deadlineTs: null,
  chat: [],          // [{channel, from, text, last_words?}]
  systemLog: [],     // announcements
  messageLog: [],    // unified timeline: [{type:"chat"|"system", ...}]
  myRole: null,
  wolfTeammates: [],
  seerResults: [],   // [{target_id, is_wolf}]
  witchInfo: null,
  gameOver: null,
  promptAction: null, // {action, options, deadline_ts, hint}
  ws: null,

  setConnection({ ws, roomCode, playerId, isHost }) {
    set({ ws, roomCode, playerId, isHost, inGame: true });
  },

  handleEvent(msg) {
    const { type, payload } = msg;
    if (type === "room_state") {
      set({ players: payload.players, hostId: payload.host_id });
    } else if (type === "role_assigned") {
      set({ myRole: payload.role, wolfTeammates: payload.wolf_teammates || [] });
    } else if (type === "phase_change") {
      set({ phase: payload.phase, deadlineTs: payload.deadline_ts || null,
            day: payload.day ?? get().day });
    } else if (type === "prompt_action") {
      set({ promptAction: payload });
    } else if (type === "chat_message") {
      set((s) => ({ chat: [...s.chat, payload],
                    messageLog: [...s.messageLog, { type: "chat", ...payload }] }));
    } else if (type === "system_announce") {
      set((s) => ({ systemLog: [...s.systemLog, payload.text],
                    messageLog: [...s.messageLog, { type: "system", text: payload.text }] }));
    } else if (type === "death_announce") {
      const names = payload.dead.map((id) => get().players.find((p) => p.id === id)?.nickname || id);
      set((s) => {
        const updatedPlayers = s.players.map((p) => payload.dead.includes(p.id) ? { ...p, alive: false } : p);
        const aliveNames = updatedPlayers.filter((p) => p.alive).map((p) => p.nickname);
        const line = names.length
          ? `死亡：${names.join(", ")}  |  存活：${aliveNames.join(", ")}`
          : `昨夜平安夜  |  存活：${aliveNames.join(", ")}`;
        return {
          systemLog: [...s.systemLog, line],
          messageLog: [...s.messageLog, { type: "system", text: line }],
          players: updatedPlayers,
        };
      });
    } else if (type === "seer_result") {
      set((s) => ({ seerResults: [...s.seerResults, payload] }));
    } else if (type === "witch_info") {
      set({ witchInfo: payload });
    } else if (type === "game_over") {
      set({ gameOver: payload, phase: "game_over" });
    }
  },

  sendAction(action) {
    get().ws?.send("action", action);
    set({ promptAction: null });
  },
  sendChat(channel, text) {
    get().ws?.send("chat", { channel, text });
  },
  startGame() {
    get().ws?.send("start_game", {});
  },
}));

export default useGameStore;