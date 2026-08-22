from pydantic import BaseModel, Field
from typing import Literal
from uuid import UUID, uuid4

class StoryPoint(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    label: str
    category: str = "custom"
    symbol: str = "custom"
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)
    coordinateSource: Literal["geocoder", "map_click", "import"]
    providerPlaceId: str | None = None
    visible: bool = True
    size: float = Field(default=1.0, ge=.25, le=4)
    notes: str | None = None

class ProjectCreate(BaseModel):
    name: str
    rawIntent: str

class Project(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    rawIntent: str
    version: int = 1
    points: list[StoryPoint] = []
    center: tuple[float, float] | None = None
    zoom: float = 10
