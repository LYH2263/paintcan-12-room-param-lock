def list_all(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM rooms ORDER BY id").fetchall()]

def get(conn, rid):
    row = conn.execute("SELECT * FROM rooms WHERE id=?", (rid,)).fetchone()
    return dict(row) if row else None

def update_dimensions(conn, rid, length, width, height):
    conn.execute("UPDATE rooms SET length=?, width=?, height=? WHERE id=?",
                 (length, width, height, rid))
    conn.commit()
    return get(conn, rid)

def set_locked(conn, rid, locked):
    conn.execute("UPDATE rooms SET locked=? WHERE id=?", (1 if locked else 0, rid))
    conn.commit()
    return get(conn, rid)
