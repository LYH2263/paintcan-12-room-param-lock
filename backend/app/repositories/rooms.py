import sqlite3
def list_all(conn): return [dict(r) for r in conn.execute("SELECT * FROM rooms ORDER BY id").fetchall()]
def get(conn, rid):
    row = conn.execute("SELECT * FROM rooms WHERE id=?", (rid,)).fetchone()
    return dict(row) if row else None
def set_locked(conn, rid, locked: bool):
    conn.execute("UPDATE rooms SET locked=? WHERE id=?", (1 if locked else 0, rid))
    conn.commit()
def update_dimensions(conn, rid, fields: dict):
    cols = [c for c in ("length", "width", "height") if fields.get(c) is not None]
    if not cols: return
    sets = ", ".join(f"{c}=?" for c in cols)
    conn.execute(f"UPDATE rooms SET {sets} WHERE id=?", (*(fields[c] for c in cols), rid))
    conn.commit()
