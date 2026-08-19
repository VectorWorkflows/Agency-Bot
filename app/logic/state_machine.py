import logging
from app.core.config import SERVICES, PROJECTS, REVIEW_SLA
from app.database import crud
from app.services import whatsapp, ai_agent

logger = logging.getLogger(__name__)

# ==========================================
# JOURNEY HANDLERS
# ==========================================

async def send_main_menu(phone_number: str):
    """Sends the 4-option customer-facing main menu using a WhatsApp List Message."""
    sections = [{
        "title": "How can we help?",
        "rows": [
            {"id": "menu_service", "title": "Have a service in mind", "description": "Explore specific automation solutions"},
            {"id": "menu_diagnosis", "title": "Figure out what I need", "description": "Describe workflow for consultation"},
            {"id": "menu_portfolio", "title": "Show what you've built", "description": "View our live projects & demos"},
            {"id": "menu_human", "title": "Speak with someone", "description": "Connect with our team directly"}
        ]
    }]
    await whatsapp.send_list_message(
        phone_number,
        "Welcome to *Vector Workflows*! \n\nWhat can we help you with today?",
        "Select an option",
        sections,
        "Main Menu"
    )
    crud.set_user_state(phone_number, "MAIN_MENU")


async def handle_service_purchase(phone_number: str, selected_service_id: str = None):
    """Journey 1: SERVICE_PURCHASE"""
    if not selected_service_id:
        rows = []
        for svc_key, svc_data in SERVICES.items():
            # WhatsApp List Row Titles are limited to 24 characters
            title = svc_data["name"][:24] 
            rows.append({"id": f"svc_{svc_key}", "title": title})
        
        sections = [{"title": "Available Services", "rows": rows}]
        await whatsapp.send_list_message(
            phone_number,
            "Which service are you interested in?",
            "View Services",
            sections
        )
        crud.set_user_state(phone_number, "SERVICE_PURCHASE")
        return

    # Show specific service details
    svc_key = selected_service_id.replace("svc_", "")
    service = SERVICES.get(svc_key)
    
    if service:
        text = f"*{service['name']}*\n\n{service['description']}\n\n*Key Features:*\n"
        for f in service['features']:
            text += f"• {f}\n"
        if service['youtube_url']:
            text += f"\n*Watch Walkthrough:*\n{service['youtube_url']}\n"
            
        text += "\n_(Type *menu* to return or *human* to speak with our team)_"
        await whatsapp.send_text_message(phone_number, text)
    else:
        await whatsapp.send_text_message(phone_number, "Service not found. Please type *menu* to return.")


async def handle_business_diagnosis_start(phone_number: str):
    """Journey 2: BUSINESS_DIAGNOSIS (Prompt)"""
    text = (
        "We'd be happy to take a look.\n\n"
        "Tell us how you currently handle the process from start to finish. Explain it however is easiest for you.\n\n"
        "You can include the people involved, tools you use, repetitive work, handoffs, delays, or anything that feels unnecessarily time-consuming.\n\n"
        "We'll review it and look for practical opportunities to save time and resources."
    )
    await whatsapp.send_text_message(phone_number, text)
    crud.set_user_state(phone_number, "BUSINESS_DIAGNOSIS")


async def handle_workflow_submission(phone_number: str, text_body: str):
    """Journey 2: BUSINESS_DIAGNOSIS (Submission Received)"""
    # 1. Save verbatim text to MongoDB Context
    crud.update_user_context(phone_number, "workflow_description", text_body)
    crud.set_user_state(phone_number, "WORKFLOW_RECEIVED")
    
    # 2. Acknowledge Receipt
    text = (
        "Thanks for taking the time to explain that. We've received your workflow and our team will review it to identify practical opportunities for automation and improvement.\n\n"
        f"We'll get back to you {REVIEW_SLA}."
    )
    await whatsapp.send_text_message(phone_number, text)
    logger.info(f"NEW WORKFLOW SUBMITTED for human review by {phone_number}.")


async def handle_portfolio_exploration(phone_number: str, selected_project_id: str = None):
    """Journey 3: PORTFOLIO_EXPLORATION"""
    if not selected_project_id:
        rows = []
        for proj_key, proj_data in PROJECTS.items():
            title = proj_data["name"][:24]
            rows.append({"id": f"proj_{proj_key}", "title": title})
            
        sections = [{"title": "Our Work", "rows": rows}]
        await whatsapp.send_list_message(
            phone_number,
            "Here's some of the work we've been building. Which one would you like to explore?",
            "View Projects",
            sections
        )
        crud.set_user_state(phone_number, "PORTFOLIO_EXPLORATION")
        return

    # Show honest project details
    proj_key = selected_project_id.replace("proj_", "")
    project = PROJECTS.get(proj_key)
    
    if project:
        text = f"*{project['name']}*\n\n{project['description']}\n\n*Status:* {project['status']}\n"
        if project.get('notes'):
            text += f"\n_{project['notes']}_\n"
        if project.get('youtube_url'):
            text += f"\n*Resources:*\n{project['youtube_url']}\n"
            
        text += "\n_(Type *menu* to go back)_"
        await whatsapp.send_text_message(phone_number, text)
    else:
        await whatsapp.send_text_message(phone_number, "Project not found. Please type *menu* to return.")


async def handle_human_request(phone_number: str, reason: str):
    """Universal Fallback: HUMAN_REQUEST"""
    crud.request_human(phone_number, reason)
    text = (
        "I've notified our team to step in! A human will take over this chat shortly.\n\n"
        "_(If you want to cancel and return to the automated assistant, just type *menu*)_"
    )
    await whatsapp.send_text_message(phone_number, text)


# ==========================================
# MASTER ROUTER
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
        crud.append_chat_history(phone_number, "user", f"[Interactive Selection: {interactive_id}]")
    else:
        crud.append_chat_history(phone_number, "user", f"[Unsupported Media Type: {msg_type}]")
        return

    # 2. Global Escape Hatches (Deterministically bypasses AI)
    lower_text = text_body.lower()
    if lower_text in ["menu", "reset", "exit", "restart", "home", "start"]:
        crud.reset_to_menu(phone_number)
        await send_main_menu(phone_number)
        return
        
    if lower_text in ["human", "support", "help", "agent", "operator"]:
        await handle_human_request(phone_number, "User typed escape keyword")
        return

    # Ignore automated processing if paused for human review
    if context.get("human_requested") and state == "HUMAN_REQUEST":
        logger.info(f"Chat with {phone_number} is paused for human review. Ignoring bot router.")
        return

    # 3. Handle Interactive Clicks (Zero AI Required - Fast Path)
    if interactive_id:
        if interactive_id == "menu_service":
            await handle_service_purchase(phone_number)
        elif interactive_id == "menu_diagnosis":
            await handle_business_diagnosis_start(phone_number)
        elif interactive_id == "menu_portfolio":
            await handle_portfolio_exploration(phone_number)
        elif interactive_id == "menu_human":
            await handle_human_request(phone_number, "User selected human from main menu")
        elif interactive_id.startswith("svc_"):
            await handle_service_purchase(phone_number, interactive_id)
        elif interactive_id.startswith("proj_"):
            await handle_portfolio_exploration(phone_number, interactive_id)
        else:
            await send_main_menu(phone_number)
        return

    # 4. State-Based Text Routing (Zero AI Required)
    if state == "NEW":
        await send_main_menu(phone_number)
        return

    elif state == "BUSINESS_DIAGNOSIS" and msg_type == "text":
        # Any text sent in this state is treated as their open-ended workflow submission
        await handle_workflow_submission(phone_number, text_body)
        return
        
    elif state == "WORKFLOW_RECEIVED":
        await whatsapp.send_text_message(phone_number, f"We've received your workflow and will review it {REVIEW_SLA}. Type *menu* to return to the main menu.")
        return

    # 5. NLP Intent Classification (Only used when free-text cannot be deterministically routed)
    if msg_type == "text":
        ai_result = await ai_agent.classify_intent(text_body)
        intent = ai_result.get("intent", "UNCLEAR")
        
        logger.info(f"Classified intent for {phone_number}: {intent} (Confidence: {ai_result.get('confidence')})")
        crud.update_user_context(phone_number, "detected_intent", intent)

        if intent == "SERVICE_PURCHASE":
            await handle_service_purchase(phone_number)
        elif intent == "BUSINESS_DIAGNOSIS":
            await handle_business_diagnosis_start(phone_number)
        elif intent == "PORTFOLIO_EXPLORATION":
            await handle_portfolio_exploration(phone_number)
        else:
            # Safe Fallback to UNCLEAR / HUMAN_REQUEST
            await handle_human_request(phone_number, f"Unclear intent from natural language message: {text_body}")