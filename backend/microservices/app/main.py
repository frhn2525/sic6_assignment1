# app/main.py
import threading
import signal
import sys
import logging
import uvicorn
from fastapi import FastAPI

from app.routes import router as api_router
from app.firebase_listener import start_firebase_listener, periodic_backup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI()
app.include_router(api_router)


def start_background_threads():
    """
    Starts background threads for the Firebase realtime listener and the periodic backup.
    """
    logger.info("Starting Firebase listener background thread.")
    listener_thread = threading.Thread(target=start_firebase_listener, daemon=True)
    listener_thread.start()

    logger.info("Starting periodic backup background thread.")
    backup_thread = threading.Thread(target=periodic_backup, daemon=True)
    backup_thread.start()


@app.on_event("startup")
async def startup_event():
    logger.info("Starting background threads via FastAPI startup event.")
    start_background_threads()


def signal_handler(sig, frame):
    logger.info("Shutting down IoT microservice...")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # Update API_HOST and API_PORT in your app/config.py as needed.
    uvicorn.run(app, host="0.0.0.0", port=8000)
