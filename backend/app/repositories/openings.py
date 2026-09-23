def for_room(conn, room_id):
    return [dict(r) for r in conn.execute(
        "SELECT * FROM openings WHERE room_id=? ORDER BY id", (room_id,)).fetchall()]

def get(conn, oid):
    row = conn.execute("SELECT * FROM openings WHERE id=?", (oid,)).fetchone()
    return dict(row) if row else None

def insert(conn, room_id, kind, w, h):
    cur = conn.execute("INSERT INTO openings(room_id,kind,w,h) VALUES (?,?,?,?)",
                       (room_id, kind, w, h))
    conn.commit()
    return get(conn, int(cur.lastrowid))

def update(conn, oid, kind=None, w=None, h=None):
    fields, vals = [], []
    for col, val in (("kind", kind), ("w", w), ("h", h)):
        if val is not None:
            fields.append(f"{col}=?")
            vals.append(val)
    if not fields:
        return get(conn, oid)
    vals.append(oid)
    conn.execute(f"UPDATE openings SET {', '.join(fields)} WHERE id=?", vals)
    conn.commit()
    return get(conn, oid)

def delete(conn, oid):
    row = get(conn, oid)
    conn.execute("DELETE FROM openings WHERE id=?", (oid,))
    conn.commit()
    return row
