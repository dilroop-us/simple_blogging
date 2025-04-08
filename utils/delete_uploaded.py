from google.cloud import storage
from utils.firebase_upload import upload_to_firebase, gcs_credentials
import os


def delete_from_firebase(file_url: str):
    """
    Deletes a file from Firebase Storage using the public URL.
    """
    if not file_url or "firebase" not in file_url:
        return  # Invalid or local image

    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
    file_path = file_url.split(f"/o/")[1].split("?")[0]  # Extract path from URL (URL-encoded)
    file_path = file_path.replace("%2F", "/")  # Decode path

    storage_client = storage.Client(credentials=gcs_credentials)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_path)

    if blob.exists():
        blob.delete()
