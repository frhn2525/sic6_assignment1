# app/config.py
import os
from dotenv import load_dotenv

load_dotenv() 

# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt.example.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "iot/sensors/#")

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
