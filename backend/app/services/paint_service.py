from app.db import connect
from app.engines.estimate import estimate_room
from app.repositories import openings, rooms, runs, settings
from app.services.errors import RoomLockedError

# 锁定后只读的字段
DIMENSION_FIELDS = ("length", "width", "height")
OPENING_FIELDS = ("kind", "w", "h")

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

    def _require_unlocked(self, room, readonly_fields):
        if room.get("locked"):
            raise RoomLockedError(room["id"], readonly_fields)

    def set_locked(self, rid, locked):
        r = rooms.get(self._c, rid)
        if not r: return None
        if bool(r.get("locked")) != bool(locked):
            rooms.set_locked(self._c, rid, locked)
        return rooms.get(self._c, rid)

    def update_dimensions(self, rid, fields):
        r = rooms.get(self._c, rid)
        if not r: return None
        changes = [f for f in DIMENSION_FIELDS if fields.get(f) is not None]
        self._require_unlocked(r, changes)
        rooms.update_dimensions(self._c, rid, fields)
        return rooms.get(self._c, rid)

    def add_opening(self, rid, kind, w, h):
        r = rooms.get(self._c, rid)
        if not r: return None
        self._require_unlocked(r, list(OPENING_FIELDS))
        oid = openings.insert(self._c, rid, kind, w, h)
        return openings.get(self._c, oid)

    def update_opening(self, oid, fields):
        o = openings.get(self._c, oid)
        if not o: return None
        r = rooms.get(self._c, o["room_id"])
        changes = [f for f in OPENING_FIELDS if fields.get(f) is not None]
        self._require_unlocked(r, changes)
        openings.update(self._c, oid, fields)
        return openings.get(self._c, oid)

    def delete_opening(self, oid):
        o = openings.get(self._c, oid)
        if not o: return None
        r = rooms.get(self._c, o["room_id"])
        self._require_unlocked(r, list(OPENING_FIELDS))
        openings.delete(self._c, oid)
        return True

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
    def dashboard(self):
        rs = rooms.list_all(self._c)
        return {"room_count": len(rs), "clean": len([x for x in rs if "种子" not in x["name"] and "多种" not in x["name"]]), "dirty": len([x for x in rs if "多种" in x["name"]])}
