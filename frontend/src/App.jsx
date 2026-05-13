import React from "react";
import useGameStore from "./store/gameStore.js";
import Lobby from "./pages/Lobby.jsx";
import Game from "./pages/Game.jsx";

export default function App() {
  const inGame = useGameStore((s) => s.inGame);
  return inGame ? <Game /> : <Lobby />;
}