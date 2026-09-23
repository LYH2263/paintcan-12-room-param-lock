class RoomLockedError(Exception):
    """房间已锁定：对尺寸/开洞的写入须整单拒绝。"""
    def __init__(self, room_id, readonly_fields):
        self.room_id = room_id
        self.readonly_fields = readonly_fields
        super().__init__(f"room {room_id} is locked; read-only fields: {','.join(readonly_fields)}")
