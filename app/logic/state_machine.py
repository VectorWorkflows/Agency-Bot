import logging
from app.core import config
from app.database import crud
from app.services import whatsapp

logger = logging.getLogger(__name__)

# ==========================================
# STATE HANDLERS (OUTBOUND MESSAGES)
# ==========================================

async def send_state_0_greeting(phone_number: str):
    """State 0: Universal Greeting (Main Menu)"""
    text = (
        "Hey! 👋 Welcome to *Vector Workflows*. We build smart automations, "
        "APIs, and custom software to put your business operations on autopilot.\n\n"
        "How can we help you scale today?"
    )
    buttons = [
        {"id": "btn_products", "title": "📦 View Products"},
        {"id": "btn_custom", "title": "⚙️ Custom Projects"},
        {"id": "btn_human", "title": "🙋‍♂️ Talk to a Human"}
    ]
    await whatsapp.send_button_message(phone_number, text, buttons)
    crud.set_user_state(phone_number, "STATE_0")


async def send_state_1a_products(phone_number: str):
    """State 1a: The Products Menu (List Message)"""
    text = "We have a few battle-tested systems ready to deploy. Tap below to select one:"
    sections = [{
        "title": "Ready-Made Systems",
        "rows": [
            {"id": "prod_scheduler", "title": "🗓️ Dynamic Scheduler", "description": "AI calendar optimization"},
            {"id": "prod_logger", "title": "📋 WA Field Logger", "description": "Turn chats into databases"},
            {"id": "prod_telephony", "title": "📞 Smart Telephony", "description": "Missed call text-backs & IVR"}
        ]
    }]
    await whatsapp.send_list_message(
        phone_number, body_text=text, button_text="Select a Product...", sections=sections
    )
    crud.set_user_state(phone_number, "STATE_1A")


async def send_state_1b_custom(phone_number: str):
    """State 1b: Custom Projects Pitch & Form"""
    text = (
        "Have a specific bottleneck? Whether you need intelligent bots for your preferred messaging apps, "
        "deep CRM integrations, or a completely custom Python backend, we can build it.\n\n"
        "Tap the button below to drop your requirements in our brief, and we'll prepare a roadmap for you.\n\n"
        "_(Type *human* to speak with us, or *menu* to go back)_"
    )
    await whatsapp.send_cta_url_button(
        to_phone_number=phone_number,
        body_text=text,
        button_text="📝 Open Intake Form",
        url=getattr(config, "GENERAL_QUERY_FORM_URL", "https://tally.so/r/0QRgZN")
    )
    crud.set_user_state(phone_number, "STATE_1B")


async def send_state_2_pitch(phone_number: str, product_id: str):
    """State 2: Product-Specific Pitches"""
    if product_id == "prod_scheduler":
        text = (
            "The *Dynamic Scheduler* adapts to your actual life—automatically adjusting your tasks "
            "and energy levels regardless of when you wake up.\n\n"
            "Tap below to fill out the onboarding brief so we can map your custom deployment:\n\n"
            "_(Type *human* to speak with us, or *menu* to go back)_"
        )
        url = getattr(config, "SCHEDULER_FORM_URL", "https://tally.so/r/Y57qNv")
        btn_text = "🗓️ Setup Scheduler"

    elif product_id == "prod_logger":
        text = (
            "Stop scrolling through messy group chats. The *Field Logger* lets your engineers submit photos "
            "and updates, while Gemini AI organizes everything into a clean database in the background.\n\n"
            "Tap below to tell us about your operations and get a quote:\n\n"
            "_(Type *human* to speak with us, or *menu* to go back)_"
        )
        url = getattr(config, "FIELD_LOGGER_FORM_URL", "https://tally.so/r/44lzd5")
        btn_text = "📋 Logger Setup"

    elif product_id == "prod_telephony":
        text = (
            "Never lose a lead to a missed call again. We build automated text-back pipelines, "
            "IVR routing, and smart business phone systems that engage your customers instantly.\n\n"
            "Tap below to blueprint your custom phone setup:\n\n"
            "_(Type *human* to speak with us, or *menu* to go back)_"
        )
        url = getattr(config, "TELEPHONY_FORM_URL", "https://tally.so/r/2EGzLM")
        btn_text = "📞 Telephony Setup"
    else:
        await send_state_0_greeting(phone_number)
        return

    await whatsapp.send_cta_url_button(phone_number, text, btn_text, url)
    crud.set_user_state(phone_number, "STATE_2")


async def trigger_human_takeover(phone_number: str, reason: str = ""):
    """Activates Telegram relay and mutes the bot."""
    crud.update_user_context(phone_number, "is_human_takeover", True)
    
    # Notify User
    text = (
        "Got it. Your request has been flagged and an engineer will review your chat history shortly. "
        "You can drop any specific questions or details here in the meantime!\n\n"
        "_(Note: If you don't receive a response within an hour, please drop your project details "
        "in our brief here: " + getattr(config, "GENERAL_QUERY_FORM_URL", "https://tally.so/r/0QRgZN") + ")_"
    )
    await whatsapp.send_text_message(phone_number, text)
    
    # Notify Admin in Telegram
    alert_msg = f"🚨 *New Human Handoff*\nPhone: `+{phone_number}`\nTrigger: {reason}"
    await whatsapp.send_telegram_alert(alert_msg)


async def trigger_fallback(phone_number: str):
    """Handles unrecognized text inputs."""
    text = (
        "Oh, I didn't quite catch that. 😅 Try using the predefined buttons for the best result.\n\n"
        "If you want to skip the bot and chat with us directly, just type *human*."
    )
    await whatsapp.send_text_message(phone_number, text)


# ==========================================
# MASTER ROUTER (INBOUND WEBHOOK)
# ==========================================

async def process_message(phone_number: str, message: dict):
    """The main entry point for all incoming WhatsApp webhooks."""
    user = crud.get_or_create_user(phone_number)
    state = user.get("state", "NEW")
    context = user.get("context", {})
    
    # 1. Extract message details
    msg_type = message.get("type")
    text_body = ""
    interactive_id = ""

    if msg_type == "text":
        text_body = message["text"]["body"].strip()
        crud.append_chat_history(phone_number, "user", text_body)
    elif msg_type == "interactive":
        interactive_type = message["interactive"]["type"]
        if interactive_type == "button_reply":
            interactive_id = message["interactive"]["button_reply"]["id"]
        elif interactive_type == "list_reply":
            interactive_id = message["interactive"]["list_reply"]["id"]
        crud.append_chat_history(phone_number, "user", f"[Selection: {interactive_id}]")
    else:
        crud.append_chat_history(phone_number, "user", f"[Media Type: {msg_type}]")

    lower_text = text_body.lower()

    # 2. Hard Overrides (Works anytime, anywhere)
    if lower_text in ["human", "support", "agent"]:
        if not context.get("is_human_takeover"):
            await trigger_human_takeover(phone_number, "User typed escape keyword")
        return

    if lower_text in ["menu", "home", "reset", "start"]:
        crud.update_user_context(phone_number, "is_human_takeover", False)
        await send_state_0_greeting(phone_number)
        return

    # 3. Telegram Relay (Bot is muted, forwards to admin)
    if context.get("is_human_takeover"):
        if msg_type == "text":
            await whatsapp.send_telegram_alert(f"💬 Message from `+{phone_number}`:\n\n{text_body}")
        else:
            await whatsapp.send_telegram_alert(f"📎 `+{phone_number}` sent a {msg_type}. Please check WhatsApp.")
        return

    # 4. Interactive Button Routing
    if interactive_id:
        if interactive_id == "btn_products":
            await send_state_1a_products(phone_number)
        elif interactive_id == "btn_custom":
            await send_state_1b_custom(phone_number)
        elif interactive_id == "btn_human":
            await trigger_human_takeover(phone_number, "User clicked Human button")
        elif interactive_id.startswith("prod_"):
            await send_state_2_pitch(phone_number, interactive_id)
        else:
            await send_state_0_greeting(phone_number)
        return

    # 5. New User Initiation
    if state == "NEW":
        await send_state_0_greeting(phone_number)
        return

    # 6. Fallback (If they type random text instead of clicking buttons)
    if msg_type == "text":
        await trigger_fallback(phone_number)