import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import base64
from dotenv import load_dotenv

# ✅ Load environment variables from .env file
load_dotenv()

firebase_credentials_str = os.getenv("FIREBASE_CREDENTIALS")
if not firebase_credentials_str:
    raise ValueError("FIREBASE_CREDENTIALS environment variable is missing!")

try:
    firebase_credentials_json = base64.b64decode(firebase_credentials_str).decode()
    FIREBASE_CREDENTIALS = json.loads(firebase_credentials_json)
except Exception as e:
    raise ValueError(f"Failed to decode FIREBASE_CREDENTIALS: {e}")

# ✅ Initialize Firebase
cred = credentials.Certificate(FIREBASE_CREDENTIALS)
firebase_admin.initialize_app(cred)
db = firestore.client()

# ✅ Predefined Blog Categories
PREDEFINED_CATEGORIES = ["Technology", "Health", "Business", "Education", "Society", "Lifestyle", "Sports", "Culture", "Work" ]

def initialize_global_data():
    """
    Ensure predefined blog categories exist in Firestore.
    """
    for category in PREDEFINED_CATEGORIES:
        category_ref = db.collection("categories").document(category)
        if not category_ref.get().exists:
            category_ref.set({"name": category})

# ✅ Run at startup
initialize_global_data()
