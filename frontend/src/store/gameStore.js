import { create } from "zustand";

const TOKEN_KEY = "werewolf_token";
const USER_KEY = "werewolf_user";

const useGameStore = create((set, get) => ({
  // 用户认证
  token: localStorage.getItem(TOKEN_KEY) || null,
  user: JSON.parse(localStorage.getItem(USER_KEY) || "null"),

  setAuth(user, token) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    set({ user, token });
  },

  logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    set({ user: null, token: null });
  },

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
  revealedRoles: {}, // {[playerId]: roleLabel}  公开的角色信息
  witchInfo: null,
  gameOver: null,
  promptAction: null, // {action, options, deadline_ts, hint}
  reviewRoom: null,
  ws: null,

  setReview(room) {
    set({ reviewRoom: room, inGame: false });
  },
  clearReview() {
    set({ reviewRoom: null });
  },

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
      set((s) => ({
        seerResults: [...s.seerResults, payload],
        revealedRoles: { ...s.revealedRoles, [payload.target_id]: payload.is_wolf ? "狼人" : "好人" },
      }));
    } else if (type === "witch_info") {
      set({ witchInfo: payload });
    } else if (type === "idiot_reveal") {
      set((s) => ({
        revealedRoles: { ...s.revealedRoles, [payload.player_id]: "白痴" },
      }));
    } else if (type === "hunter_shot") {
      if (payload.shooter) {
        set((s) => ({
          revealedRoles: { ...s.revealedRoles, [payload.shooter]: "猎人" },
        }));
      }
    } else if (type === "game_over") {
      const RLABEL = { werewolf: "狼人", witch: "女巫", seer: "预言家", villager: "平民", hunter: "猎人", idiot: "白痴" };
      const roles = {};
      for (const [id, role] of Object.entries(payload.roles)) {
        roles[id] = RLABEL[role] || role;
      }
      set({ gameOver: payload, phase: "game_over", revealedRoles: roles });
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