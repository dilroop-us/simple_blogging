from fastapi import UploadFile
from google.cloud import storage
from google.oauth2 import service_account
import os
import base64
import json
from dotenv import load_dotenv

load_dotenv()

FIREBASE_CREDENTIALS_STR = os.getenv("FIREBASE_CREDENTIALS")
FIREBASE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")

# ✅ Decode the base64 credentials
firebase_credentials_dict = json.loads(base64.b64decode(FIREBASE_CREDENTIALS_STR).decode())

# ✅ Create Google-auth-compatible credentials
gcs_credentials = service_account.Credentials.from_service_account_info(firebase_credentials_dict)

def upload_to_firebase(file: UploadFile, path: str) -> str:
    storage_client = storage.Client(credentials=gcs_credentials)
    bucket = storage_client.bucket(FIREBASE_BUCKET)

    blob = bucket.blob(path)
    blob.upload_from_file(file.file, content_type=file.content_type)
    blob.make_public()

    return blob.public_url
