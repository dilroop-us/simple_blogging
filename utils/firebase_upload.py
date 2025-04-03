from fastapi import UploadFile
from google.cloud import storage
from firebase_admin import credentials
import os
from dotenv import load_dotenv
import base64
import json

load_dotenv()

# ✅ Load and decode credentials
firebase_credentials_str = os.getenv("FIREBASE_CREDENTIALS")
firebase_credentials_json = json.loads(base64.b64decode(firebase_credentials_str).decode())
bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")

# ✅ Create credentials object
firebase_cred = credentials.Certificate(firebase_credentials_json)

def upload_to_firebase(file: UploadFile, folder: str) -> str:
    storage_client = storage.Client(credentials=firebase_cred)
    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(f"{folder}/{file.filename}")
    blob.upload_from_file(file.file, content_type=file.content_type)
    blob.make_public()

    return blob.public_url
