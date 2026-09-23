from fastapi import APIRouter, HTTPException
from app.schemas.estimate import DimensionsRequest, LockRequest, OpeningCreateRequest, OpeningUpdateRequest
from app.services.errors import RoomLockedError
from app.services.paint_service import PaintService
router = APIRouter()

def _locked_response(e: RoomLockedError):
    # 409：整单拒绝，并点名只读的尺寸/开洞字段
    return HTTPException(status_code=409, detail={
        "error": "room_locked",
        "room_id": e.room_id,
        "readonly_fields": e.readonly_fields,
        "message": f"房间已锁定，以下字段只读不可改：{', '.join(e.readonly_fields)}",
    })

@router.get("/rooms")
def list_rooms():
    with PaintService() as s: return {"items": s.list_rooms()}
@router.get("/rooms/{room_id}")
def room_detail(room_id: int):
    with PaintService() as s:
        d = s.room_detail(room_id)
        if not d: raise HTTPException(404)
        return d
@router.post("/rooms/{room_id}/lock")
def lock_room(room_id: int, body: LockRequest):
    with PaintService() as s:
        r = s.set_locked(room_id, body.locked)
        if not r: raise HTTPException(404)
        return r
@router.patch("/rooms/{room_id}/dimensions")
def patch_dimensions(room_id: int, body: DimensionsRequest):
    with PaintService() as s:
        try:
            r = s.update_dimensions(room_id, body.model_dump(exclude_none=True))
        except RoomLockedError as e:
            raise _locked_response(e)
        if not r: raise HTTPException(404)
        return r
@router.post("/rooms/{room_id}/openings")
def add_opening(room_id: int, body: OpeningCreateRequest):
    with PaintService() as s:
        try:
            o = s.add_opening(room_id, body.kind, body.w, body.h)
        except RoomLockedError as e:
            raise _locked_response(e)
        if not o: raise HTTPException(404)
        return o
@router.patch("/openings/{opening_id}")
def patch_opening(opening_id: int, body: OpeningUpdateRequest):
    with PaintService() as s:
        try:
            o = s.update_opening(opening_id, body.model_dump(exclude_none=True))
        except RoomLockedError as e:
            raise _locked_response(e)
        if not o: raise HTTPException(404)
        return o
@router.delete("/openings/{opening_id}")
def delete_opening(opening_id: int):
    with PaintService() as s:
        try:
            ok = s.delete_opening(opening_id)
        except RoomLockedError as e:
            raise _locked_response(e)
        if not ok: raise HTTPException(404)
        return {"ok": True}
