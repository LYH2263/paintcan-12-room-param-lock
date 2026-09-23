import json
import pytest

from app.db import DB_PATH
from app.seed import init_db


@pytest.fixture(autouse=True)
def reset_db():
    """每个用例前删掉 sqlite 文件并重新建种子库，保证用例互不干扰。"""
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()
    yield


def history_runs(client, room_id):
    items = client.get("/api/history").json()["items"]
    out = []
    for h in items:
        if h["room_id"] == room_id:
            out.append(json.loads(h["result_json"]))
    return out


def test_lock_field_shared_between_list_and_detail(client):
    lst = client.get("/api/rooms").json()["items"]
    assert all(r["locked"] == 0 for r in lst)
    d = client.get("/api/rooms/1").json()
    assert d["room"]["locked"] == 0

    r = client.post("/api/rooms/1/lock", json={"locked": True})
    assert r.status_code == 200
    assert r.json()["room"]["locked"] == 1

    lst = client.get("/api/rooms").json()["items"]
    assert next(r for r in lst if r["id"] == 1)["locked"] == 1
    assert client.get("/api/rooms/1").json()["room"]["locked"] == 1


def test_locked_dimensions_rejected_and_names_fields(client):
    client.post("/api/rooms/1/lock", json={"locked": True})
    before = client.get("/api/rooms/1").json()["room"]

    r = client.put("/api/rooms/1/dimensions",
                   json={"length": 6, "width": 5, "height": 3})
    assert r.status_code == 409
    detail = r.json()["detail"]
    for f in ("length", "width", "height"):
        assert f in detail

    after = client.get("/api/rooms/1").json()["room"]
    assert after == before


def test_locked_openings_rejected_and_names_fields(client):
    client.post("/api/rooms/1/lock", json={"locked": True})
    oid = client.get("/api/rooms/1").json()["openings"][0]["id"]
    before = client.get("/api/rooms/1").json()["openings"]

    r = client.post("/api/rooms/1/openings",
                    json={"kind": "window", "w": 1.0, "h": 1.0})
    assert r.status_code == 409
    assert "openings.kind" in r.json()["detail"]

    r = client.patch(f"/api/openings/{oid}", json={"w": 2.0})
    assert r.status_code == 409
    assert "openings.w" in r.json()["detail"]

    r = client.delete(f"/api/openings/{oid}")
    assert r.status_code == 409
    assert "openings" in r.json()["detail"]

    assert client.get("/api/rooms/1").json()["openings"] == before


def test_locked_estimate_allowed_both_persist_modes(client):
    # 种子房间1：5x4x2.8，门洞 0.9x2.1，窗 1.5x1.4 → net 46.41，8 平米/L、2 遍 → 11.60 L
    client.post("/api/rooms/1/lock", json={"locked": True})

    r = client.post("/api/estimate",
                    json={"room_id": 1, "persist": False})
    assert r.status_code == 200
    body = r.json()
    assert body["run_id"] is None
    assert body["net_m2"] == 46.41
    assert body["liters"] == 11.6

    r = client.post("/api/estimate",
                    json={"room_id": 1, "persist": True})
    assert r.status_code == 200
    body = r.json()
    assert body["run_id"] is not None
    assert body["liters"] == 11.6
    runs = history_runs(client, 1)
    assert any(x["liters"] == 11.6 and x["net_m2"] == 46.41 for x in runs)


def test_lock_uses_snapshot_dimensions_and_openings(client):
    # 未锁时改尺寸 → 升数变化；锁定后拒绝再改，估算仍按锁定当时数据
    r = client.put("/api/rooms/1/dimensions",
                   json={"length": 6, "width": 4, "height": 2.8})
    assert r.status_code == 200
    d = client.post("/api/rooms/1/openings",
                    json={"kind": "window", "w": 1.0, "h": 1.0})
    assert d.status_code == 200

    client.post("/api/rooms/1/lock", json={"locked": True})
    est = client.post("/api/estimate",
                      json={"room_id": 1, "persist": False}).json()
    # walls 56 - 原洞(1.89+2.10) - 新洞 1.0 = 51.01；51.01*2/8 = 12.75
    assert est["net_m2"] == 51.01
    assert est["liters"] == 12.75

    assert client.put("/api/rooms/1/dimensions",
                      json={"length": 7, "width": 7, "height": 3}).status_code == 409
    est2 = client.post("/api/estimate",
                       json={"room_id": 1, "persist": False}).json()
    assert est2["net_m2"] == 51.01
    assert est2["liters"] == 12.75


def test_unlock_restores_editing(client):
    client.post("/api/rooms/1/lock", json={"locked": True})
    client.post("/api/rooms/1/lock", json={"locked": False})
    assert client.get("/api/rooms/1").json()["room"]["locked"] == 0

    r = client.put("/api/rooms/1/dimensions",
                   json={"length": 6, "width": 4, "height": 2.8})
    assert r.status_code == 200
    assert r.json()["room"]["length"] == 6

    r = client.post("/api/rooms/1/openings",
                    json={"kind": "door", "w": 1.0, "h": 2.0})
    assert r.status_code == 200
    oid = r.json()["openings"][-1]["id"]

    r = client.patch(f"/api/openings/{oid}", json={"w": 1.2})
    assert r.status_code == 200
    assert client.get("/api/rooms/1").json()["openings"][-1]["w"] == 1.2

    assert client.delete(f"/api/openings/{oid}").status_code == 200
    assert all(o["id"] != oid for o in client.get("/api/rooms/1").json()["openings"])


def test_lock_actions_do_not_rewrite_calc_runs(client):
    client.post("/api/estimate", json={"room_id": 1, "persist": True})
    before = history_runs(client, 1)
    assert before

    client.post("/api/rooms/1/lock", json={"locked": True})
    client.post("/api/rooms/1/lock", json={"locked": False})

    after = history_runs(client, 1)
    assert after == before


def test_missing_room_and_opening_404(client):
    assert client.post("/api/rooms/999/lock", json={"locked": True}).status_code == 404
    assert client.put("/api/rooms/999/dimensions",
                      json={"length": 1, "width": 1, "height": 1}).status_code == 404
    assert client.post("/api/rooms/999/openings",
                       json={"kind": "door", "w": 1, "h": 1}).status_code == 404
    assert client.patch("/api/openings/999", json={"w": 1}).status_code == 404
    assert client.delete("/api/openings/999").status_code == 404
