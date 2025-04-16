# app/processing.py
import logging
from datetime import datetime
from app.firebase_client import db  # Firebase Firestore client

logger = logging.getLogger("processing")

def process_message(topic, data):
    """
    Process the incoming MQTT message.
    This version writes the message to Firebase Firestore.
    """
    logger.info("Processing message from '%s': %s", topic, data)

    try:
        # Prepare a document to store in Firestore.
        # You can organize by topic (e.g., each topic can be a collection) or save all
        doc = {
            "topic": topic,
            "data": data,
            "received_at": datetime.utcnow(),  # Firestore accepts Python datetime objects.
        }
        # Save the document in the 'iot_data' collection with an auto-generated ID.
        db.collection("iot_data").add(doc)
        logger.info("Data saved to Firestore.")
    except Exception as e:
        logger.exception("Error saving data to Firestore: %s", e)


# def process_message(topic, data):
#     logger.info("Processing message from '%s': %s", topic, data)
