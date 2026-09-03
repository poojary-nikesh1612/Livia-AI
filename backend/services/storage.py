"""services/storage.py: Handles file uploads to Supabase Storage."""

import base64
import logging
import uuid

from config.settings import settings
from supabase import Client, create_client

logger = logging.getLogger(__name__)

# Initialize Supabase Client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
BUCKET_NAME = "crop_images"


def _get_mime_and_ext(b64_string: str) -> tuple[str, str]:
    """Inspects the leading base64 magic bytes to determine image MIME type and file extension."""
    if b64_string.startswith("/9j/"):
        return "image/jpeg", ".jpg"
    elif b64_string.startswith("iVBORw0KGgo"):
        return "image/png", ".png"
    elif b64_string.startswith("UklGR"):
        return "image/webp", ".webp"
    elif b64_string.startswith("R0lGOD"):
        return "image/gif", ".gif"
    return "image/jpeg", ".jpg"


async def upload_base64_images(base64_strings: list[str]) -> list[str]:
    """
    Uploads a list of base64 image strings to Supabase and returns their public URLs.
    """
    if not base64_strings:
        return []

    uploaded_urls = []

    for b64_str in base64_strings:
        try:
            if "," in b64_str:
                b64_str = b64_str.split(",")[1]

            # Detect the exact MIME type and extension from the raw base64 string
            mime_type, file_ext = _get_mime_and_ext(b64_str)

            image_bytes = base64.b64decode(b64_str)
            file_name = f"{uuid.uuid4()}{file_ext}"

            # Upload to Supabase Storage with dynamic content-type
            supabase.storage.from_(BUCKET_NAME).upload(
                file=image_bytes,
                path=file_name,
                file_options={"content-type": mime_type},
            )

            # Get public URL
            public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_name)
            uploaded_urls.append(public_url)

        except Exception:
            logger.exception("Failed to upload image to Supabase.")
            continue

    return uploaded_urls
