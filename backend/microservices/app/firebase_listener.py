# app/firebase_listener.py
import threading
import time
import logging
from datetime import datetime
from app.firebase_client import root_ref, firestore_client

logger = logging.getLogger("firebase_listener")

# Global variables to store the latest data and a lock for thread safety.
latest_data = None
data_lock = threading.Lock()


def firebase_event_listener(event):
    """
    Callback function to handle realtime database events.
    When the data at the specified reference changes, this function will be called.
    """
    global latest_data
    with data_lock:
        latest_data = event.data
    logger.info("Realtime event received: %s", event.data)


def start_firebase_listener():
    """
    Start listening to the 'esp32_accident_detection' node in the database.
    """
    ref = root_ref.child("esp32_accident_detection")
    # Attach the listener. The .listen() method opens a persistent connection.
    ref.listen(firebase_event_listener)


def periodic_backup():
    """
    Every 5 minutes, backup the last received value from the realtime database to Firestore.
    """
    while True:
        time.sleep(300)  # Sleep for 5 minutes.
        with data_lock:
            data_to_backup = latest_data

        if data_to_backup is not None:
            doc = {"data": data_to_backup, "backed_up_at": datetime.utcnow()}
            try:
                # Save the document in the Firestore collection "iot_data_backup"
                firestore_client.collection("iot_data_backup").add(doc)
                logger.info("Data backup saved to Firestore.")
            except Exception as e:
                logger.exception("Error backing up data to Firestore: %s", e)
        else:
            logger.info("No new data available for backup.")
