import React, { useRef, useState, useEffect } from "react";
import PlayerSeat from "./PlayerSeat.jsx";

const SEAT_SIZE = 72;
const SEAT_OFFSET = SEAT_SIZE / 2;

export default function RoundTable({ players, myId }) {
  const containerRef = useRef(null);
  const [dims, setDims] = useState({ w: 600, h: 600 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      setDims({ w: width, h: height });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const size = Math.min(dims.w, dims.h);
  const radius = size * 0.38;
  const cx = size / 2;
  const cy = size / 2;
  const tableSize = size * 0.33;

  return (
    <div ref={containerRef} className="card" style={{
      position: "relative",
      width: "100%",
      flex: 1,
      minHeight: 0,
      overflow: "hidden",
    }}>
      <div style={{
        position: "absolute",
        left: "50%", top: "50%",
        transform: "translate(-50%, -50%)",
        width: size, height: size,
      }}>
        {/* 桌子 - 发光圆环 */}
        <div style={{
          position: "absolute",
          width: tableSize, height: tableSize,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(124,92,252,0.08) 0%, rgba(12,13,23,0.6) 60%, transparent 100%)",
          border: "1px solid var(--border)",
          boxShadow: "inset 0 0 60px rgba(124,92,252,0.06)",
          top: "50%", left: "50%",
          transform: "translate(-50%, -50%)",
          zIndex: 0,
        }} />

        {/* 中心文字 */}
        <div style={{
          position: "absolute",
          top: "50%", left: "50%",
          transform: "translate(-50%, -50%)",
          zIndex: 0,
          textAlign: "center",
          pointerEvents: "none",
        }}>
          <div style={{ fontSize: Math.max(14, size * 0.03), opacity: 0.15, fontWeight: 700, letterSpacing: 2 }}>
            狼人杀
          </div>
        </div>

        {/* 座位 */}
        {players.map((p, i) => {
          const angle = (i / players.length) * 2 * Math.PI - Math.PI / 2;
          const x = cx + radius * Math.cos(angle) - SEAT_OFFSET;
          const y = cy + radius * Math.sin(angle) - SEAT_OFFSET;
          return (
            <div
              key={p.id}
              style={{
                position: "absolute",
                left: x, top: y,
                zIndex: 1,
                transition: "all 0.3s ease",
              }}
            >
              <PlayerSeat player={p} isMe={p.id === myId} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
