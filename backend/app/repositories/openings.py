import sqlite3
def for_room(conn, room_id):
    return [dict(r) for r in conn.execute("SELECT * FROM openings WHERE room_id=?", (room_id,)).fetchall()]
def get(conn, oid):
    row = conn.execute("SELECT * FROM openings WHERE id=?", (oid,)).fetchone()
    return dict(row) if row else None
def insert(conn, room_id, kind, w, h):
    cur = conn.execute("INSERT INTO openings(room_id,kind,w,h) VALUES (?,?,?,?)", (room_id, kind, w, h))
    conn.commit(); return int(cur.lastrowid)
def update(conn, oid, fields: dict):
    cols = [c for c in ("kind", "w", "h") if fields.get(c) is not None]
    if not cols: return
    sets = ", ".join(f"{c}=?" for c in cols)
    conn.execute(f"UPDATE openings SET {sets} WHERE id=?", (*(fields[c] for c in cols), oid))
    conn.commit()
def delete(conn, oid):
    conn.execute("DELETE FROM openings WHERE id=?", (oid,))
    conn.commit()
