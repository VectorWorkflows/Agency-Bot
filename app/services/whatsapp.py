import logging
import httpx
from typing import List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

# Construct the base Meta Graph API URL
BASE_URL = f"https://graph.facebook.com/{settings.META_GRAPH_VERSION}/{settings.PHONE_NUMBER_ID}/messages"


async def _send_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Internal helper to shoot payloads to Meta with strict error handling."""
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(BASE_URL, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            logger.info(f"Message successfully dispatched to {payload.get('to')}")
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Meta Graph API Error [HTTP {e.response.status_code}]: {e.response.text}")
            return {}
        except Exception as e:
            logger.error(f"Network error while calling Meta Graph API: {e}")
            return {}


async def send_text_message(to_phone_number: str, text: str) -> Dict[str, Any]:
    """Sends a standard text message (Used in AI_MODE and general replies)."""
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_phone_number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": text
        }
    }
    return await _send_request(payload)


async def send_button_message(to_phone_number: str, body_text: str, buttons: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Sends an interactive message with up to 3 quick-reply buttons.
    (Used for MAIN_MENU and LEAD_BUDGET states).
    
    Format for buttons list: 
    [{"id": "btn_portfolio", "title": "See Portfolio"}, ...]
    """
    if len(buttons) > 3:
        logger.warning("WhatsApp only supports a maximum of 3 buttons. Truncating.")
        buttons = buttons[:3]

    formatted_buttons = [
        {
            "type": "reply",
            "reply": {
                "id": btn["id"],
                "title": btn["title"]
            }
        }
        for btn in buttons
    ]

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": body_text
            },
            "action": {
                "buttons": formatted_buttons
            }
        }
    }
    return await _send_request(payload)


async def send_list_message(
    to_phone_number: str, 
    body_text: str, 
    button_text: str, 
    sections: List[Dict[str, Any]], 
    header_text: str = None
) -> Dict[str, Any]:
    """
    Sends an interactive list menu (Used for SHOW_PORTFOLIO state).
    
    Format for sections list:
    [
        {
            "title": "Agency Services",
            "rows": [
                {"id": "item_lead_gen", "title": "Lead Gen Bot", "description": "Automate leads"}
            ]
        }
    ]
    """
    interactive_obj = {
        "type": "list",
        "body": {
            "text": body_text
        },
        "action": {
            "button": button_text,
            "sections": sections
        }
    }

    if header_text:
        interactive_obj["header"] = {
            "type": "text",
            "text": header_text
        }

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone_number,
        "type": "interactive",
        "interactive": interactive_obj
    }
    return await _send_request(payload)