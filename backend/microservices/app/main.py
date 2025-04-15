
import threading
import signal
import sys
import logging

import uvicorn
from fastapi import FastAPI

from .config import API_HOST, API_PORT
from .mqtt_client import get_mqtt_client
from .routes import router as api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI()
app.include_router(api_router)


def mqtt_loop():
    client = get_mqtt_client()
    from .config import MQTT_BROKER, MQTT_PORT

    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_forever()


def signal_handler(sig, frame):
    logger.info("Shutting down IoT microservice...")
    sys.exit(0)


if __name__ == "__main__":
    
    mqtt_thread = threading.Thread(target=mqtt_loop, daemon=True)
    mqtt_thread.start()

    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    
    uvicorn.run(app, host=API_HOST, port=API_PORT)
