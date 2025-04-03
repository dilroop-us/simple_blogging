import firebase_admin
from firebase_admin import credentials, firestore, storage
import os
import json
import base64
from dotenv import load_dotenv

load_dotenv()

firebase_credentials_str = os.getenv("FIREBASE_CREDENTIALS")
if not firebase_credentials_str:
    raise ValueError("FIREBASE_CREDENTIALS environment variable is missing!")

try:
    firebase_credentials_json = base64.b64decode(firebase_credentials_str).decode()
    FIREBASE_CREDENTIALS = json.loads(firebase_credentials_json)
except Exception as e:
    raise ValueError(f"Failed to decode FIREBASE_CREDENTIALS: {e}")

# ✅ Initialize Firebase Admin with Storage
cred = credentials.Certificate(FIREBASE_CREDENTIALS)
firebase_admin.initialize_app(cred, {
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET")
})

db = firestore.client()
bucket = storage.bucket()

PREDEFINED_CATEGORIES = [
    "Technology", "Health", "Business", "Education", "Society",
    "Lifestyle", "Sports", "Culture", "Work"
]

def initialize_global_data():
    for category in PREDEFINED_CATEGORIES:
        category_ref = db.collection("categories").document(category)
        if not category_ref.get().exists:
            category_ref.set({"name": category})
