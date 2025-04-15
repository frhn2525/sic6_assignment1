# app/processing.py
import logging

logger = logging.getLogger("processing")


def process_message(topic, data):
    logger.info("Processing message from '%s': %s", topic, data)
