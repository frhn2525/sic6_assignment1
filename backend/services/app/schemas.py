from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import app.model as model


class EventResponse(model.Event):
    _id: str


class HistoryQuery(BaseModel):
    device_id: Optional[str]
    start: Optional[datetime]
    end: Optional[datetime]
    limit: int = 100


class HistoryResponse(BaseModel):
    events: List[EventResponse]
