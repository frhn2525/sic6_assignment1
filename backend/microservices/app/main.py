# app/main.py
import threading
import signal
import sys
import logging
import uvicorn
from fastapi import FastAPI

from app.config import API_HOST, API_PORT, MQTT_BROKER, MQTT_PORT
from app.mqtt_client import get_mqtt_client, logger as mqtt_logger
from app.routes import router as api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI()
app.include_router(api_router)


def mqtt_loop():
    mqtt_logger.info("Starting MQTT client loop.")
    client = get_mqtt_client()
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    except Exception as e:
        mqtt_logger.exception("Failed to connect to MQTT Broker: %s", e)
    client.loop_forever()


@app.on_event("startup")
async def startup_event():
    logger.info("Starting MQTT background thread via FastAPI startup event.")
    mqtt_thread = threading.Thread(target=mqtt_loop, daemon=True)
    mqtt_thread.start()


def signal_handler(sig, frame):
    logger.info("Shutting down IoT microservice...")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    uvicorn.run(app, host=API_HOST, port=API_PORT)
