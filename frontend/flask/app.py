# app.py
from flask import Flask, render_template, jsonify, request
import firebase_admin
from firebase_admin import credentials, db
import os
import json
from datetime import datetime,timezone,timedelta
from pymongo import MongoClient
from bson import ObjectId
import math

app = Flask(__name__)



# Initialize Firebase
# For production, use environment variables or secure storage for credentials
# In this example, we'll use a JSON config file
try:
    # Use the application default credentials or specify path to service account file
    cred = credentials.Certificate("firebase-credentials.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://muqsithfirebase-default-rtdb.asia-southeast1.firebasedatabase.app/'
    })
except Exception as e:
    # For development without credentials file, we'll use a mock
    print(f"Firebase initialization error: {e}")
    # Sample data for development without Firebase
    # SAMPLE_DATA = {
    #     "esp32_accident_detection": {
    #         "status": {
    #             "location": {
    #                 "lat": 0,
    #                 "lon": 0,
    #                 "valid": False
    #             },
    #             "sensor": {
    #                 "accelerometer": {
    #                     "magnitude": 0.87,
    #                     "x": 0.109,
    #                     "y": -0.035,
    #                     "z": 0.863
    #                 },
    #                 "gyroscope": {
    #                     "magnitude": 3.249,
    #                     "x": -3.115,
    #                     "y": 0.611,
    #                     "z": -0.695
    #                 }
    #             },
    #             "system": {
    #                 "movement": False,
    #                 "state": "PARK"
    #             },
    #             "timestamp": 798147759
    #         }
    #     }
    # }

# Initialize MongoDB connection
try:
    mongo_client = MongoClient("mongodb+srv://UNI022:UNI022@cluster0.ac7up.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    mongo_db = mongo_client["accident_detection"]
    mongo_collection = mongo_db["sensor_data"]
    print("MongoDB connection successful")
except Exception as e:
    print(f"MongoDB connection error: {e}")
    mongo_collection = None

def convert_objectid(data):
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = convert_objectid(value)
    elif isinstance(data, list):
        for index, item in enumerate(data):
            data[index] = convert_objectid(item)
    elif isinstance(data, ObjectId):
        return str(data)  # Convert ObjectId ke string
    return data

def save_to_mongodb(data):
    """Save data to MongoDB database"""
    try:
        if mongo_collection is not None:
            # Add a timestamp for when the data was saved to MongoDB
            data['mongodb_saved_at'] = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=7))).isoformat()
            # Insert the document
            result = mongo_collection.insert_one(data)
            print(f"Data saved to MongoDB with ID: {result.inserted_id}")
            return True
        else:
            print("MongoDB collection is not initialized.")
            return False
    except Exception as e:
        print(f"Error saving to MongoDB: {e}")
        return False


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/data')
def get_data():
    try:
        # Try to get real data from Firebase
        ref = db.reference('esp32_accident_detection/status')
        data = ref.get()
        utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        wib_now = datetime.now(timezone(timedelta(hours=7)))
        data['formatted_time'] = wib_now.strftime('%Y-%m-%d %H:%M:%S')

        # Save to MongoDB
        save_to_mongodb(data)

        # Convert ObjectId before returning
        data = convert_objectid(data)
        
        return jsonify(data)
    except Exception as e:
        # return jsonify(sample_data)
        print(f"Error fetching data: {e}")
        return jsonify({"error": "Failed to fetch data from Firebase"}), 500


@app.route('/api/history')
def get_history():
    """Retrieve historical data from MongoDB"""
    try:
        if mongo_collection is None:
            return jsonify({"error": "MongoDB connection not available"}), 503
        
        # Get pagination parameters from request
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        
        # Ensure valid pagination values
        page = max(1, page)
        limit = min(50, max(1, limit))
        
        # Calculate skip value for pagination
        skip = (page - 1) * limit
        
        # Get total count of records
        total_records = mongo_collection.count_documents({})
        total_pages = math.ceil(total_records / limit)
        
        # Query MongoDB for historical data
        cursor = mongo_collection.find().sort('mongodb_saved_at', -1).skip(skip).limit(limit)
        
        # Convert MongoDB cursor to list and sanitize ObjectId
        records = list(cursor)
        sanitized_records = [convert_objectid(record) for record in records]
        
        return jsonify({
            "page": page,
            "limit": limit,
            "total_records": total_records,
            "total_pages": total_pages,
            "records": sanitized_records
        })
    except Exception as e:
        print(f"Error fetching history data: {e}")
        return jsonify({"error": f"Failed to fetch history data: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)