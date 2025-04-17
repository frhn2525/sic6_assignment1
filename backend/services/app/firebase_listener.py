import threading, time
from firebase_admin import credentials, initialize_app, db
from datetime import datetime
from app.model import Event
from services import save_events
from app.configuration import settings

# Initialize Firebase
cred = credentials.Certificate(settings.FIREBASE_CRED)
initialize_app(cred, {"databaseURL": settings.FIREBASE_DB_URL})

batch: list[Event] = []
last_flush = time.time()
lock = threading.Lock()


def _flush_if_needed():
    global last_flush
    if not batch:
        return
    with lock:
        now = time.time()
        if (
            len(batch) >= settings.BATCH_SIZE
            or now - last_flush >= settings.BATCH_TIMEOUT
        ):
            # async run
            import asyncio

            asyncio.create_task(save_events(batch.copy()))
            batch.clear()
            last_flush = now


def on_change(event):
    data = event.data
    if data is None:
        return
    ev = Event(
        device_id="esp32_accident_detection",
        timestamp=datetime.utcfromtimestamp(data["timestamp"]),
        location=data["location"],
        sensor=data["sensor"],
        system=data["system"],
        raw=data,
    )
    with lock:
        batch.append(ev)
    _flush_if_needed()


# Start stream
ref = db.reference("/esp32_accident_detection/status")
stream = ref.listen(on_change)
