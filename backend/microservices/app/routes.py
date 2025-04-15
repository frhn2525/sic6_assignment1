# app/routes.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

messages = []


@router.get("/messages")
async def get_messages():
    return JSONResponse(content=messages)


@router.post("/messages")
async def post_message(topic: str, data: dict):
    messages.append({"topic": topic, "data": data})
    return {"status": "Message stored", "message": {"topic": topic, "data": data}}
