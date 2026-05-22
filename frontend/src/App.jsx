import React from "react";
import useGameStore from "./store/gameStore.js";
import AuthPage from "./pages/AuthPage.jsx";
import Lobby from "./pages/Lobby.jsx";
import Game from "./pages/Game.jsx";
import Review from "./pages/Review.jsx";

export default function App() {
  const user = useGameStore((s) => s.user);
  const token = useGameStore((s) => s.token);
  const inGame = useGameStore((s) => s.inGame);
  const reviewRoom = useGameStore((s) => s.reviewRoom);

  if (!user || !token) return <AuthPage />;
  if (reviewRoom) return <Review />;
  return inGame ? <Game /> : <Lobby />;
}