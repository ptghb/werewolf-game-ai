from fastapi.testclient import TestClient

from app.main import app


def test_healthz():
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200


def test_create_room_http():
    client = TestClient(app)
    r = client.post("/api/rooms", json={"nickname": "alice", "human_slots": 1, "ai_slots": 5})
    assert r.status_code == 200
    body = r.json()
    assert "room_code" in body
    assert body["host_id"].startswith("h_")


def test_join_room_http():
    client = TestClient(app)
    r = client.post("/api/rooms", json={"nickname": "alice", "human_slots": 2, "ai_slots": 4})
    code = r.json()["room_code"]
    r2 = client.post(f"/api/rooms/{code}/join", json={"nickname": "bob"})
    assert r2.status_code == 200
    assert r2.json()["player_id"].startswith("h_")


def test_join_unknown_room_404():
    client = TestClient(app)
    r = client.post("/api/rooms/NOPE/join", json={"nickname": "bob"})
    assert r.status_code == 404