from pydantic import BaseModel
class EstimateRequest(BaseModel):
    room_id: int
    coats: int | None = None
    coverage: float | None = None
    persist: bool = True
class LockRequest(BaseModel):
    locked: bool
class DimensionsRequest(BaseModel):
    length: float | None = None
    width: float | None = None
    height: float | None = None
class OpeningCreateRequest(BaseModel):
    kind: str
    w: float
    h: float
class OpeningUpdateRequest(BaseModel):
    kind: str | None = None
    w: float | None = None
    h: float | None = None
