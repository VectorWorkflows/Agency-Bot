import uvicorn
import logging
import re
from fastapi import FastAPI, Request, Response, BackgroundTasks
from app.core.config import settings
from app.core import security
from app.logic import state_machine
from app.services import whatsapp

# Configure logging for production visibility
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Vector Workflows Agency Bot (Omni-Channel)")

# ==========================================
# WHATSAPP WEBHOOKS
# ==========================================

@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Handles Meta's initial webhook verification requirement.
    Matches the VERIFY_TOKEN in your .env file.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.VERIFY_TOKEN:
        logger.info("Webhook successfully verified by Meta.")
        return Response(content=challenge, media_type="text/plain")
    
    logger.warning("Webhook verification failed. Token mismatch.")
    return Response(status_code=403, content="Verification failed")


@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives incoming WhatsApp events, verifies the security signature, 
    and offloads processing to a background task to ensure a fast 200 OK response.
    """
    payload_bytes = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    
    # Security Check: Ensure the payload actually came from Meta
    if not security.verify_webhook_signature(payload_bytes, signature, settings.META_APP_SECRET):
        logger.warning("Dropped unauthorized webhook payload.")
        return Response(status_code=401, content="Invalid signature")

    payload = await request.json()
    
    # Pass the payload to the async worker
    background_tasks.add_task(process_whatsapp_payload, payload)
    
    # Instantly return 200 OK to Meta to prevent timeout retries
    return {"status": "ok"}


async def process_whatsapp_payload(payload: dict):
    """
    Isolates 'messages' from status receipts and passes them to the router.
    """
    try:
        entry = payload.get("entry", [])
        if not entry:
            return

        changes = entry[0].get("changes", [])
        if not changes:
            return

        value = changes[0].get("value", {})
        
        # We only care about user messages, not read/delivery receipts
        if "messages" in value:
            message = value["messages"][0]
            sender_phone = message["from"]
            
            logger.info(f"Incoming WA message received from {sender_phone}.")
            await state_machine.process_message(sender_phone, message)
            
    except Exception as e:
        logger.error(f"Error processing WA webhook payload: {e}", exc_info=True)


# ==========================================
# TELEGRAM WEBHOOKS (THE RELAY)
# ==========================================

@app.post("/webhook/telegram")
async def receive_telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives messages sent by the admin inside the Telegram Ops Group.
    """
    payload = await request.json()
    background_tasks.add_task(process_telegram_payload, payload)
    return {"status": "ok"}


async def process_telegram_payload(payload: dict):
    """
    Extracts the phone number from the replied-to message and pushes 
    the admin's text back to the WhatsApp API.
    """
    try:
        message = payload.get("message", {})
        chat = message.get("chat", {})
        text = message.get("text", "")

        # 1. Security constraint: Only process messages from your specific Ops Group
        if str(chat.get("id")) != str(getattr(settings, "TELEGRAM_OPS_GROUP_ID", "")):
            return

        # 2. Only process messages that are direct replies to the Bot's forwarded alerts
        reply_to = message.get("reply_to_message", {})
        if not reply_to or not text:
            return

        original_text = reply_to.get("text", "")
        
        # 3. Extract the WhatsApp phone number from the original bot message
        # Matches patterns like "+1234567890" or "Phone: +1234567890"
        match = re.search(r"\+?(\d{10,15})", original_text)
        
        if not match:
            logger.warning("Could not extract a valid WA phone number from the Telegram reply.")
            return
        
        target_wa_number = match.group(1)
        
        # 4. Push the reply to the Meta API
        await whatsapp.send_text_message(target_wa_number, text)
        logger.info(f"Successfully relayed Telegram response to WA: {target_wa_number}")

    except Exception as e:
        logger.error(f"Error processing Telegram payload: {e}", exc_info=True)


if __name__ == "__main__":
    # This lets you start the server just by running the python file
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)