from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class Location(BaseModel):
    lat: float
    lon: float
    valid: bool


class SensorAxis(BaseModel):
    magnitude: float
    x: float
    y: float
    z: float


class SensorData(BaseModel):
    accelerometer: SensorAxis
    gyroscope: SensorAxis


class SystemStatus(BaseModel):
    movement: bool
    state: str


class Event(BaseModel):
    device_id: str
    timestamp: datetime
    location: Location
    sensor: SensorData
    system: SystemStatus
    raw: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True
        json_encoders = {datetime: lambda v: v.isoformat()}
