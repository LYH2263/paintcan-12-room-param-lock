from typing import Literal
from pydantic import BaseModel, Field

class DimensionsRequest(BaseModel):
    length: float = Field(gt=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)

class OpeningCreateRequest(BaseModel):
    kind: Literal["door", "window"]
    w: float = Field(gt=0)
    h: float = Field(gt=0)

class OpeningUpdateRequest(BaseModel):
    kind: Literal["door", "window"] | None = None
    w: float | None = Field(default=None, gt=0)
    h: float | None = Field(default=None, gt=0)

class LockRequest(BaseModel):
    locked: bool
