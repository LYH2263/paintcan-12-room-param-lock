from app.db import connect
from app.engines.estimate import estimate_room
from app.repositories import openings, rooms, runs, settings

class RoomLockedError(Exception):
    """房间锁定后对只读尺寸/开洞字段发起写操作时抛出。"""

def _locked(msg):
    return RoomLockedError(msg)

class PaintService:
    def __init__(self): self._c = connect()
    def close(self): self._c.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    def list_rooms(self): return rooms.list_all(self._c)
    def room_detail(self, rid):
        r = rooms.get(self._c, rid)
        if not r: return None
        return {"room": r, "openings": openings.for_room(self._c, rid)}
    def settings(self): return settings.get_map(self._c)
    def history(self, limit=50): return runs.list_recent(self._c, limit)
    def estimate(self, room_id, persist, coats=None, coverage=None):
        detail = self.room_detail(room_id)
        if not detail: return None
        r = detail["room"]
        cov, ct = settings.coverage_coats(self._c)
        cov = float(coverage or cov)
        ct = int(coats or ct)
        ops = [{"w": o["w"], "h": o["h"]} for o in detail["openings"]]
        result = estimate_room(r["length"], r["width"], r["height"], ops, cov, ct)
        rid = runs.insert(self._c, "estimate", {"room_id": room_id, "coats": ct, "coverage": cov}, result, room_id) if persist else None
        return {"run_id": rid, "room_id": room_id, **result}
    def set_locked(self, room_id, locked):
        r = rooms.get(self._c, room_id)
        if not r: return None
        rooms.set_locked(self._c, room_id, locked)
        return self.room_detail(room_id)
    def update_dimensions(self, room_id, length, width, height):
        r = rooms.get(self._c, room_id)
        if not r: return None
        if r["locked"]:
            raise _locked("房间已锁定：尺寸字段 length、width、height 为只读，无法修改")
        rooms.update_dimensions(self._c, room_id, length, width, height)
        return self.room_detail(room_id)
    def add_opening(self, room_id, kind, w, h):
        r = rooms.get(self._c, room_id)
        if not r: return None
        if r["locked"]:
            raise _locked("房间已锁定：开洞字段 openings.kind、openings.w、openings.h 为只读，无法新增门窗")
        openings.insert(self._c, room_id, kind, w, h)
        return self.room_detail(room_id)
    def _opening_room(self, opening_id):
        o = openings.get(self._c, opening_id)
        if not o: return None, None
        return o, rooms.get(self._c, o["room_id"])
    def update_opening(self, opening_id, kind=None, w=None, h=None):
        _, r = self._opening_room(opening_id)
        if r is None: return None
        if r["locked"]:
            raise _locked("房间已锁定：开洞字段 openings.kind、openings.w、openings.h 为只读，无法修改门窗")
        openings.update(self._c, opening_id, kind=kind, w=w, h=h)
        return self.room_detail(r["id"])
    def delete_opening(self, opening_id):
        _, r = self._opening_room(opening_id)
        if r is None: return None
        if r["locked"]:
            raise _locked("房间已锁定：开洞字段 openings.kind、openings.w、openings.h 为只读，无法删除门窗")
        openings.delete(self._c, opening_id)
        return {"ok": True}
    def dashboard(self):
        rs = rooms.list_all(self._c)
        return {"room_count": len(rs), "clean": len([x for x in rs if "种子" not in x["name"] and "多种" not in x["name"]]), "dirty": len([x for x in rs if "多种" in x["name"]])}
