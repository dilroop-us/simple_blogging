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


def delete_from_firebase(file_url: str):
    """
    Deletes a file from Firebase Storage using the public or download URL.
    """
    if not file_url or "firebase" not in file_url:
        return  # Skip if not a valid Firebase URL

    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
    storage_client = storage.Client(credentials=gcs_credentials)
    bucket = storage_client.bucket(bucket_name)

    try:
        # Check if it's a download URL (with /o/)
        if "/o/" in file_url:
            file_path = file_url.split("/o/")[1].split("?")[0]
            file_path = file_path.replace("%2F", "/")  # Decode
        else:
            # Fallback: Public URL format
            parts = file_url.split(f"{bucket_name}/")
            if len(parts) != 2:
                return  # Unexpected format
            file_path = parts[1].split("?")[0]  # remove query string if any

        blob = bucket.blob(file_path)
        if blob.exists():
            blob.delete()
    except Exception as e:
        print(f"Failed to delete file from Firebase: {e}")
