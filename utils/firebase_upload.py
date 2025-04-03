from fastapi import UploadFile
from google.cloud import storage
import os
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = os.getenv("FIREBASE_STORAGE_BUCKET")

def upload_to_firebase(file: UploadFile, folder: str) -> str:
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"{folder}/{file.filename}")

    blob.upload_from_file(file.file, content_type=file.content_type)
    blob.make_public()

    return blob.public_url
