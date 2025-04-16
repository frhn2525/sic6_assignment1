# app.py
from flask import Flask, render_template, jsonify
import firebase_admin
from firebase_admin import credentials, db
import os
import json
from datetime import datetime

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
    SAMPLE_DATA = {
        "esp32_accident_detection": {
            "status": {
                "location": {
                    "lat": 0,
                    "lon": 0,
                    "valid": False
                },
                "sensor": {
                    "accelerometer": {
                        "magnitude": 0.87,
                        "x": 0.109,
                        "y": -0.035,
                        "z": 0.863
                    },
                    "gyroscope": {
                        "magnitude": 3.249,
                        "x": -3.115,
                        "y": 0.611,
                        "z": -0.695
                    }
                },
                "system": {
                    "movement": False,
                    "state": "PARK"
                },
                "timestamp": 798147759
            }
        }
    }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/data')
def get_data():
    try:
        # Try to get real data from Firebase
        ref = db.reference('esp32_accident_detection/status')
        data = ref.get()
        
        # Convert timestamp to readable format
        if data and 'timestamp' in data:
            # Convert Unix timestamp to datetime
            timestamp = data['timestamp']
            dt = datetime.fromtimestamp(timestamp)
            data['formatted_time'] = dt.strftime('%Y-%m-%d %H:%M:%S')
            
        return jsonify(data)
    except Exception as e:
        # If Firebase access fails, return sample data
        print(f"Error fetching data: {e}")
        sample_data = SAMPLE_DATA["esp32_accident_detection"]["status"]
        
        # Add formatted time to sample data
        if 'timestamp' in sample_data:
            timestamp = sample_data['timestamp']
            dt = datetime.fromtimestamp(timestamp)
            sample_data['formatted_time'] = dt.strftime('%Y-%m-%d %H:%M:%S')
            
        return jsonify(sample_data)


if __name__ == '__main__':
    app.run(debug=True)