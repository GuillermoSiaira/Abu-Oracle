from __future__ import annotations
import os
import tweepy
from io import BytesIO

def publish_twitter(
    text: str,
    image_bytes: bytes | None = None,
    image_gcs_uri: str | None = None,
    config_type: str = "",
) -> dict:
    """
    Publica directamente en X usando la API v2.
    """
    api_key = os.environ.get("TWITTER_API_KEY")
    api_secret = os.environ.get("TWITTER_API_SECRET")
    access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")

    if not all([api_key, api_secret, access_token, access_token_secret]):
        print("[twitter] Faltan credenciales API — solo simulando")
        return {"status": "dry_run", "detail": "Missing Twitter credentials"}

    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
    api = tweepy.API(auth)
    client = tweepy.Client(
        consumer_key=api_key, consumer_secret=api_secret,
        access_token=access_token, access_token_secret=access_token_secret
    )

    media_id = None
    try:
        final_bytes = image_bytes
        if not final_bytes and image_gcs_uri:
            from google.cloud import storage
            storage_client = storage.Client()
            bucket_name = image_gcs_uri.split("/")[2]
            blob_name = "/".join(image_gcs_uri.split("/")[3:])
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            final_bytes = blob.download_as_bytes()

        if final_bytes:
            media = api.media_upload(filename="sky.png", file=BytesIO(final_bytes))
            media_id = media.media_id

        if media_id:
            response = client.create_tweet(text=text, media_ids=[media_id])
        else:
            response = client.create_tweet(text=text)

        print(f"[twitter] Publicado OK: {response.data}")
        return {"status": "published", "id": response.data['id']}

    except Exception as e:
        print(f"[twitter] Error publicando: {e}")
        return {"status": "error", "detail": str(e)}
