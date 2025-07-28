import firebase_admin
from firebase_admin import credentials, firestore, storage
import os

def initialize_firebase():
    # Check if Firebase app is already initialized
    if not firebase_admin._apps:
        # Get the base64 encoded service account from the environment variable
        firebase_credentials_base64 = os.getenv('FIREBASE_CREDENTIALS_BASE64')

        if firebase_credentials_base64:
            import base64
            import json

            # Decode the base64 string
            firebase_credentials_json = base64.b64decode(firebase_credentials_base64).decode('utf-8')
            
            # Load the credentials from the JSON string
            cred = credentials.Certificate(json.loads(firebase_credentials_json))
        else:
            # Fallback to a local file if the environment variable is not set
            cred = credentials.Certificate('path/to/your/serviceAccountKey.json')

        # Initialize the app with the credentials
        firebase_admin.initialize_app(cred, {
            'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
        })

    # Get the Firestore client
    db = firestore.client()
    
    # Get the storage bucket
    bucket = storage.bucket()

    return db, bucket

# Initialize Firebase and get the db and bucket objects
db, bucket = initialize_firebase()
