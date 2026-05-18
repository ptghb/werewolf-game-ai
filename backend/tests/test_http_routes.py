from fastapi.testclient import TestClient

from app.main import app, manager


def test_healthz():
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200


def test_create_room_http():
    client = TestClient(app)
    r = client.post("/api/rooms", json={"nickname": "alice", "mode": "6"})
    assert r.status_code == 200
    body = r.json()
    assert "room_code" in body
    assert body["host_id"].startswith("h_")


def test_join_full_room_returns_409():
    client = TestClient(app)
    r = client.post("/api/rooms", json={"nickname": "alice", "mode": "6"})
    code = r.json()["room_code"]
    r2 = client.post(f"/api/rooms/{code}/join", json={"nickname": "bob"})
    assert r2.status_code == 409


def test_websocket_chat_uses_server_authoritative_sender_identity():
    client = TestClient(app)
    r = client.post("/api/rooms", json={"nickname": "alice", "mode": "6"})
    body = r.json()
    code = body["room_code"]
    player_id = body["host_id"]

    with client.websocket_connect("/ws") as ws:
        ws.send_json({"type": "hello", "room": code, "player_id": player_id})
        ws.receive_json()
        ws.send_json({
            "type": "chat",
            "payload": {
                "channel": "day",
                "text": "hi",
                "from": "spoofed-id",
                "from_name": "spoofed-name",
            },
        })

    room = manager.get_room(code)
    queued = room.queue.get_nowait()
    assert queued["from"] == player_id
    assert queued["from_name"] == "alice"


def test_join_unknown_room_404():
    client = TestClient(app)
    r = client.post("/api/rooms/NOPE/join", json={"nickname": "bob"})
    assert r.status_code == 404