from flask import Flask, request, jsonify
import threading
import requests
import paho.mqtt.client as mqtt
import time
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# MQTT Configuration
MQTT_BROKER = "192.168.18.38"  
MQTT_PORT = 1883
MQTT_TOPIC_CONTROL = "image/control"
MQTT_USERNAME = "UNI022"  
MQTT_PASSWORD = "022"  

# Target endpoints for redirection
FACE_RECOGNITION_ENDPOINT = "http://127.0.0.1:5001/upload"
DROWSINESS_ENDPOINT = "http://127.0.0.1:5002/upload"

# Current active processing mode
current_mode = None
mode_lock = threading.Lock()

# Flag to control the processing thread
running = True

# MQTT client setup
def on_connect(client, userdata, flags, rc):
    logger.info(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(MQTT_TOPIC_CONTROL)

def on_message(client, userdata, msg):
    global current_mode
    control_message = msg.payload.decode()
    logger.info(f"Received control message: {control_message}")
    
    with mode_lock:
        if control_message == "face_recognition":
            current_mode = "face_recognition"
            logger.info("Switched to face recognition mode")
        elif control_message == "drowsiness":
            current_mode = "drowsiness"
            logger.info("Switched to drowsiness detection mode")
        else:
            logger.warning(f"Unknown control message: {control_message}")

def setup_mqtt_client():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        logger.info(f"Connected to MQTT Broker: {MQTT_BROKER}")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {e}")
        return None

# REST API endpoint to receive images from ESP32-CAM
@app.route('/upload', methods=['POST'])
def upload_image():
    try:
        content = request.get_json()
        if not content or 'image' not in content:
            return jsonify({"error": "No image data received"}), 400
        
        with mode_lock:
            mode = current_mode
        
        if mode is None:
            logger.info("No processing mode set, storing image only")
            return jsonify({"status": "success", "message": "Image received but no processing mode is active"})
        
        return forward_request(content, mode)
        
    except Exception as e:
        logger.error(f"Error processing upload request: {str(e)}")
        return jsonify({"error": str(e)}), 500

def forward_request(content, mode):
    """Forward the request to the appropriate processing endpoint"""
    try:
        if mode == "face_recognition":
            target_url = FACE_RECOGNITION_ENDPOINT
        elif mode == "drowsiness":
            target_url = DROWSINESS_ENDPOINT
        else:
            return jsonify({"error": f"Unknown mode: {mode}"}), 400
        
        logger.info(f"Forwarding request to {target_url}")
        
        response = requests.post(
            target_url,
            json=content,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        return jsonify(response.json()), response.status_code
        
    except requests.RequestException as e:
        logger.error(f"Error forwarding request: {str(e)}")
        return jsonify({"error": f"Error forwarding request: {str(e)}"}), 502

def mqtt_loop(client):
    """Run the MQTT client loop in a separate thread"""
    logger.info("Starting MQTT client loop")
    client.loop_start()
    
    try:
        while running:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("MQTT loop interrupted")
    finally:
        client.loop_stop()
        logger.info("MQTT client loop stopped")

def start_server():
    """Start the Flask server"""
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    mqtt_client = setup_mqtt_client()
    if not mqtt_client:
        logger.error("Failed to set up MQTT client. Exiting.")
        exit(1)
    
    mqtt_thread = threading.Thread(target=mqtt_loop, args=(mqtt_client,))
    mqtt_thread.daemon = True
    mqtt_thread.start()
    
    try:
        logger.info("Starting Flask server")
        start_server()
    except KeyboardInterrupt:
        logger.info("Server interrupted")
    finally:
        running = False
        if mqtt_thread.is_alive():
            mqtt_thread.join(timeout=2.0)
        logger.info("Server stopped")
