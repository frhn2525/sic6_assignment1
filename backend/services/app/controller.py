from fastapi import APIRouter, HTTPException
from app.schemas import HistoryQuery, HistoryResponse
from app.services import query_history

router = APIRouter(prefix="/api/v1")


@router.post("/history", response_model=HistoryResponse)
async def get_history(q: HistoryQuery):
    events = await query_history(
        device_id=q.device_id, start=q.start, end=q.end, limit=q.limit
    )
    return {"events": events}
