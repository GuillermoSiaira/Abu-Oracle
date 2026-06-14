from __future__ import annotations
import os
import requests
from datetime import timedelta

def publish_instagram(
    text: str,
    image_bytes: bytes | None = None,
    image_gcs_uri: str | None = None,
    config_type: str = "",
) -> dict:
    access_token = os.environ.get("IG_ACCESS_TOKEN")
    account_id = os.environ.get("IG_ACCOUNT_ID")

    if not all([access_token, account_id]):
        print("[instagram] Faltan credenciales API (IG_ACCESS_TOKEN o IG_ACCOUNT_ID) — simulando")
        return {"status": "dry_run", "detail": "Missing IG credentials"}

    image_url = None
    
    # 1. Resolver imagen y obtener URL pública temporal (requerida por Meta Graph)
    if image_gcs_uri:
        try:
            from google.cloud import storage
            storage_client = storage.Client()
            bucket_name = image_gcs_uri.split("/")[2]
            blob_name = "/".join(image_gcs_uri.split("/")[3:])
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            image_url = blob.generate_signed_url(version="v4", expiration=timedelta(hours=1), method="GET")
        except Exception as exc:
            return {"status": "error", "detail": f"Error firmando URL: {exc}"}
    elif image_bytes:
        try:
            from google.cloud import storage
            import uuid
            bucket_name = os.environ.get("GCS_DRAFTS_BUCKET")
            if not bucket_name:
                return {"status": "error", "detail": "GCS_DRAFTS_BUCKET missing for direct upload"}
                
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob_name = f"direct/{uuid.uuid4()}.png"
            blob = bucket.blob(blob_name)
            blob.upload_from_string(image_bytes, content_type="image/png")
            image_url = blob.generate_signed_url(version="v4", expiration=timedelta(hours=1), method="GET")
        except Exception as exc:
            return {"status": "error", "detail": f"Error subiendo bytes a GCS: {exc}"}
        
    if not image_url:
        return {"status": "error", "detail": "Instagram requires an image"}

    # 2. Meta Graph API
    base_url = "https://graph.facebook.com/v19.0"
    
    try:
        create_url = f"{base_url}/{account_id}/media"
        create_payload = {
            "image_url": image_url,
            "caption": text,
            "access_token": access_token
        }
        resp = requests.post(create_url, data=create_payload, timeout=15)
        if not resp.ok:
            return {"status": "error", "detail": f"Error creating media: {resp.text}"}
            
        creation_id = resp.json().get("id")
        
        publish_url = f"{base_url}/{account_id}/media_publish"
        publish_payload = {
            "creation_id": creation_id,
            "access_token": access_token
        }
        resp2 = requests.post(publish_url, data=publish_payload, timeout=15)
        if not resp2.ok:
            return {"status": "error", "detail": f"Error publishing media: {resp2.text}"}
            
        published_id = resp2.json().get("id")
        print(f"[instagram] Publicado OK: {published_id}")
        return {"status": "published", "id": published_id}
        
    except Exception as e:
        print(f"[instagram] Error: {e}")
        return {"status": "error", "detail": str(e)}
