import json

import pytest

from app.db import connect
from app.services.errors import RoomLockedError
from app.services.paint_service import PaintService


def test_list_and_detail_share_same_locked_field(svc):
    """列表与详情读取锁定状态走同一字段：未锁两侧均为 0。"""
    listed = {r["id"]: r["locked"] for r in svc.list_rooms()}
    assert listed[1] == 0
    detail = svc.room_detail(1)
    assert detail["room"]["locked"] == listed[1]

    svc.set_locked(1, True)
    listed = {r["id"]: r["locked"] for r in svc.list_rooms()}
    detail = svc.room_detail(1)
    assert listed[1] == 1 and detail["room"]["locked"] == 1


def test_lock_blocks_dimensions_and_names_readonly_fields(svc):
    svc.set_locked(1, True)
    with pytest.raises(RoomLockedError) as ei:
        svc.update_dimensions(1, {"length": 6.0, "height": 3.0})
    # 点名只读的尺寸字段
    assert set(ei.value.readonly_fields) == {"length", "height"}
    # 整单拒绝：未给出的字段不变，给出的也未生效
    r = svc.room_detail(1)["room"]
    assert (r["length"], r["width"], r["height"]) == (5.0, 4.0, 2.8)


def test_lock_blocks_opening_create_update_delete(svc):
    svc.set_locked(1, True)
    with pytest.raises(RoomLockedError) as ei:
        svc.add_opening(1, "window", 1.0, 1.0)
    assert ei.value.readonly_fields == ["kind", "w", "h"]

    with pytest.raises(RoomLockedError):
        svc.update_opening(1, {"w": 2.0})
    with pytest.raises(RoomLockedError):
        svc.delete_opening(1)

    # 开洞集合原样
    ops = svc.room_detail(1)["openings"]
    assert [(o["id"], o["w"], o["h"]) for o in ops] == [(1, 0.9, 2.1), (2, 1.5, 1.4)]


def test_unlock_restores_editing(svc):
    svc.set_locked(1, True)
    svc.set_locked(1, False)
    assert svc.room_detail(1)["room"]["locked"] == 0
    svc.update_dimensions(1, {"length": 6.0})
    assert svc.room_detail(1)["room"]["length"] == 6.0
    oid = svc.add_opening(1, "window", 1.0, 1.0)["id"]
    svc.update_opening(oid, {"w": 1.2})
    assert svc.room_detail(1)["openings"][-1]["w"] == 1.2
    svc.delete_opening(oid)
    assert all(o["id"] != oid for o in svc.room_detail(1)["openings"])


def test_estimate_while_locked_uses_snapshot_and_persists(svc):
    # 锁定前先记一条基线 run
    before = svc.estimate(1, persist=True)
    svc.set_locked(1, True)

    # persist=False 允许
    dry = svc.estimate(1, persist=False)
    assert dry["run_id"] is None
    assert dry["liters"] == before["liters"] == 11.6
    assert dry["net_m2"] == before["net_m2"]

    # persist=True 在锁定期不得被拒绝，且正常写入
    persisted = svc.estimate(1, persist=True)
    assert persisted["run_id"] is not None
    assert persisted["liters"] == 11.6

    # 锁定期间尝试改尺寸被拒 → 估算仍按锁定当时尺寸计算
    with pytest.raises(RoomLockedError):
        svc.update_dimensions(1, {"length": 9.0})
    again = svc.estimate(1, persist=False)
    assert again["liters"] == 11.6
    assert again["net_m2"] == before["net_m2"]


def test_lock_unlock_does_not_rewrite_calc_runs(svc):
    svc.estimate(1, persist=True)
    conn = connect()
    rows = conn.execute("SELECT id, result_json FROM calc_runs WHERE room_id=1 ORDER BY id").fetchall()
    conn.close()
    snapshot = [(r["id"], r["result_json"]) for r in rows]
    assert snapshot, "应至少存在种子/估算 run"

    svc.set_locked(1, True)
    svc.set_locked(1, False)

    conn = connect()
    rows = conn.execute("SELECT id, result_json FROM calc_runs WHERE room_id=1 ORDER BY id").fetchall()
    conn.close()
    assert [(r["id"], r["result_json"]) for r in rows] == snapshot
    # 升数与净面积未被改写
    for _, payload in snapshot:
        result = json.loads(payload)
        assert result["liters"] == 11.6 and result["net_m2"] == 46.41


def test_relock_then_estimate_still_uses_new_snapshot(svc):
    """解锁后修改 → 重新锁定 → 估算按新的锁定时数据。"""
    svc.set_locked(1, False)
    svc.update_dimensions(1, {"length": 6.0})
    svc.set_locked(1, True)
    r = svc.estimate(1, persist=False)
    # 周长 2*(6+4)=20, 墙毛 56, 扣 1.89+2.1=3.99, 净 52.01, 升 52.01*2/8 = 13.0025
    assert r["gross_m2"] == 56.0 and r["net_m2"] == 52.01
    assert r["liters"] == 13.0
