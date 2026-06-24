import os
import logging
from supabase import create_client, Client
from config import settings

logger = logging.getLogger(__name__)

supabase_client: Client = None

# Initialize Supabase Client if credentials are provided
if settings.SUPABASE_URL and settings.SUPABASE_KEY:
    try:
        supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info("Supabase client initialized successfully for storage.")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
else:
    logger.info("Supabase URL or Key not set. Storage service will use local disk storage.")

class StorageService:
    @staticmethod
    async def upload_file(filename: str, file_data: bytes) -> str:
        """Uploads a file to Supabase storage or falls back to local disk storage."""
        # Standardize safe filename
        safe_filename = "".join([c if c.isalnum() or c in ['.', '_', '-'] else '_' for c in filename])

        if supabase_client:
            try:
                # Ensure the bucket name is loaded
                bucket = settings.SUPABASE_BUCKET
                
                # Check / create path inside bucket
                storage_path = f"documents/{safe_filename}"
                
                # Upload to Supabase bucket. We use upsert=True to allow overwriting if it exists
                response = supabase_client.storage.from_(bucket).upload(
                    path=storage_path,
                    file=file_data,
                    file_options={"x-upsert": "true", "content-type": "application/octet-stream"}
                )
                
                # Get the public URL of the uploaded file
                public_url_resp = supabase_client.storage.from_(bucket).get_public_url(storage_path)
                logger.info(f"Successfully uploaded {safe_filename} to Supabase bucket '{bucket}'. URL: {public_url_resp}")
                return public_url_resp
            except Exception as e:
                logger.warning(f"Supabase storage upload failed: {e}. Falling back to local disk storage.")
        
        # Local fallback storage
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        local_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
        try:
            with open(local_path, "wb") as f:
                f.write(file_data)
            logger.info(f"Saved file {safe_filename} to local directory: {local_path}")
            # Normalize to forward slashes for URL pathing
            return local_path.replace("\\", "/")
        except Exception as e:
            logger.error(f"Failed to save file to local disk: {e}")
            raise e
