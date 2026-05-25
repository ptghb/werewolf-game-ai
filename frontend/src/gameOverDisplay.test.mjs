import assert from "node:assert/strict";

global.localStorage = {
  getItem() { return null; },
  setItem() {},
  removeItem() {},
};

const { default: useGameStore } = await import("./store/gameStore.js");

useGameStore.setState({
  players: [
    { id: "p1", nickname: "一号", alive: false },
    { id: "p2", nickname: "二号", alive: true },
  ],
  phase: "day_vote",
  revealedRoles: {},
  gameOver: null,
  messageLog: [],
  systemLog: [],
});

useGameStore.getState().handleEvent({
  type: "game_over",
  payload: {
    winner: "good",
    roles: { p1: "werewolf", p2: "seer" },
  },
});

const state = useGameStore.getState();
assert.equal(state.phase, "game_over");
assert.equal(state.revealedRoles.p1, "狼人");
assert.equal(state.revealedRoles.p2, "预言家");
assert.deepEqual(state.messageLog.at(-1), {
  type: "system",
  text: "游戏结束：好人阵营胜利",
});
