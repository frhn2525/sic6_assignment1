from pymongo import MongoClient, ASCENDING
from app.configuration import settings
from app.model import Event
from datetime import datetime

client = MongoClient(settings.MONGO_URI)
db = client[settings.DB_NAME]
# Ensure time-series collection created once
collection = (
    db.create_collection(
        "events", timeseries={"timeField": "timestamp", "metaField": "device_id"}
    )
    if "events" not in db.list_collection_names()
    else db["events"]
)

# index on device_id + timestamp
collection.create_index([("device_id", ASCENDING), ("timestamp", ASCENDING)])


async def save_events(batch: list[Event]):
    docs = [e.dict(by_alias=True, exclude_none=True) for e in batch]
    result = collection.insert_many(docs)
    return result.inserted_ids

async def query_history(device_id=None, start=None, end=None, limit=100):
    query = {}
    if device_id:
        query["device_id"] = device_id
    if start or end:
        query["timestamp"] = {}
        if start:
            query["timestamp"]["$gte"] = start
        if end:
            query["timestamp"]["$lte"] = end
    cursor = collection.find(query).sort("timestamp", ASCENDING).limit(limit)
    return [Event(**doc) for doc in await cursor.to_list(length=limit)]
