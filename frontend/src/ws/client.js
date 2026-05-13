// Tiny WebSocket client with seq dedupe + auto-reconnect + ack.
// Intentionally untested — behavior is covered by end-to-end manual smoke.
export function createWSClient({ url, room, playerId, onMessage }) {
  let ws = null;
  let lastAckSeq = 0;
  let shouldReconnect = true;
  let reconnectDelay = 500;

  function connect() {
    ws = new WebSocket(url);
    ws.onopen = () => {
      reconnectDelay = 500;
      ws.send(JSON.stringify({
        type: "hello", room, player_id: playerId, last_ack_seq: lastAckSeq,
      }));
    };
    ws.onmessage = (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch { return; }
      if (typeof msg.seq === "number") {
        if (msg.seq <= lastAckSeq) return;  // dedupe
        lastAckSeq = msg.seq;
        try { ws.send(JSON.stringify({ type: "ack", payload: { seq: msg.seq } })); } catch {}
      }
      onMessage?.(msg);
    };
    ws.onclose = () => {
      if (!shouldReconnect) return;
      setTimeout(connect, reconnectDelay);
      reconnectDelay = Math.min(reconnectDelay * 2, 5000);
    };
    ws.onerror = () => ws.close();
  }

  connect();

  return {
    send(type, payload) {
      if (!ws || ws.readyState !== WebSocket.OPEN) return;
      ws.send(JSON.stringify({ type, payload, room }));
    },
    close() {
      shouldReconnect = false;
      try { ws?.close(); } catch {}
    },
  };
}