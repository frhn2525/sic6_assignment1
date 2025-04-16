# app/firebase_client.py
import os
import firebase_admin
from firebase_admin import credentials, firestore

# Read the path to the service account key from the environment.
SERVICE_ACCOUNT_PATH = os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_PATH", "./serviceAccountKey.json"
)

if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        raise Exception(f"Firebase initialization error: {e}")

# Get a Firestore client.
db = firestore.client()
