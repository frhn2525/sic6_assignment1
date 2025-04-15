# app/mqtt_client.py
import json
import logging
import paho.mqtt.client as mqtt

from .config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC
from .processing import process_message

logger = logging.getLogger("mqtt_client")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected successfully to MQTT Broker")
        client.subscribe(MQTT_TOPIC)
    else:
        logger.error("Failed to connect with result code %d", rc)


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)
        logger.info("Received message on topic '%s': %s", msg.topic, data)
        process_message(msg.topic, data)
    except Exception as e:
        logger.exception("Error processing message: %s", e)


def get_mqtt_client():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    return client
