# app/firebase_client.py
import os
import firebase_admin
from firebase_admin import credentials, firestore, db

# Read credentials and database URL from environment variables.
SERVICE_ACCOUNT_PATH = os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_PATH", "./serviceAccountKey.json"
)
DATABASE_URL = os.getenv(
    "FIREBASE_DATABASE_URL", "https://your-database-name.firebaseio.com"
)

if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})
    except Exception as e:
        raise Exception(f"Firebase initialization error: {e}")

# Firestore client.
firestore_client = firestore.client()

# For the realtime database, we use the db module.
# You can create references anywhere in your database.
root_ref = db.reference("/")
