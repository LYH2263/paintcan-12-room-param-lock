from fastapi import APIRouter, HTTPException
from app.schemas.room import (
    DimensionsRequest, LockRequest, OpeningCreateRequest, OpeningUpdateRequest,
)
from app.services.paint_service import PaintService, RoomLockedError
router = APIRouter()

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
        d = s.set_locked(room_id, body.locked)
        if not d: raise HTTPException(404)
        return d

@router.put("/rooms/{room_id}/dimensions")
def update_dimensions(room_id: int, body: DimensionsRequest):
    with PaintService() as s:
        try:
            d = s.update_dimensions(room_id, body.length, body.width, body.height)
        except RoomLockedError as e:
            raise HTTPException(status_code=409, detail=str(e))
        if not d: raise HTTPException(404)
        return d

@router.post("/rooms/{room_id}/openings")
def add_opening(room_id: int, body: OpeningCreateRequest):
    with PaintService() as s:
        try:
            d = s.add_opening(room_id, body.kind, body.w, body.h)
        except RoomLockedError as e:
            raise HTTPException(status_code=409, detail=str(e))
        if not d: raise HTTPException(404)
        return d

@router.patch("/openings/{opening_id}")
def update_opening(opening_id: int, body: OpeningUpdateRequest):
    with PaintService() as s:
        try:
            d = s.update_opening(opening_id, kind=body.kind, w=body.w, h=body.h)
        except RoomLockedError as e:
            raise HTTPException(status_code=409, detail=str(e))
        if not d: raise HTTPException(404)
        return d

@router.delete("/openings/{opening_id}")
def delete_opening(opening_id: int):
    with PaintService() as s:
        try:
            d = s.delete_opening(opening_id)
        except RoomLockedError as e:
            raise HTTPException(status_code=409, detail=str(e))
        if not d: raise HTTPException(404)
        return d
