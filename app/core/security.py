import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)


def verify_webhook_signature(payload_bytes: bytes, signature_header: str, app_secret: str) -> bool:
    """
    Verifies the SHA256 HMAC signature sent by Meta in the 'X-Hub-Signature-256' header.
    
    Args:
        payload_bytes (bytes): The raw request body bytes.
        signature_header (str): The value of the 'X-Hub-Signature-256' header (format: 'sha256=...').
        app_secret (str): Your Meta App Secret from the Developer Portal.
        
    Returns:
        bool: True if signature is valid or if secret is not set (dev mode), False otherwise.
    """
    if not app_secret:
        # If APP_SECRET is not configured, bypass verification for local testing
        return True

    if not signature_header or not signature_header.startswith("sha256="):
        logger.warning("Missing or malformed X-Hub-Signature-256 header.")
        return False

    expected_hash = signature_header.split("sha256=")[1]
    
    # Calculate HMAC-SHA256 hash using the raw bytes and app secret
    calculated_hash = hmac.new(
        key=app_secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()

    # Compare hashes safely against timing attacks
    is_valid = hmac.compare_digest(calculated_hash, expected_hash)
    if not is_valid:
        logger.warning("Meta webhook signature mismatch!")
    return is_valid