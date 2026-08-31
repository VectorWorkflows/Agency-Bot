import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Meta / WhatsApp Credentials
    WHATSAPP_TOKEN: str = os.getenv("WHATSAPP_TOKEN", "")
    PHONE_NUMBER_ID: str = os.getenv("PHONE_NUMBER_ID", "")
    VERIFY_TOKEN: str = os.getenv("VERIFY_TOKEN", "vector_agency_webhook_secret_2026")
    META_GRAPH_VERSION: str = "v21.0"
    META_APP_SECRET: str = os.getenv("META_APP_SECRET", "")

    # Database & AI
    MONGO_URI: str = os.getenv("MONGO_URI", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    import os

# Form URLs
GENERAL_QUERY_FORM_URL = os.getenv("GENERAL_QUERY_FORM_URL", "https://tally.so/r/0QRgZN")
SCHEDULER_FORM_URL = os.getenv("SCHEDULER_FORM_URL", "https://tally.so/r/Y57qNv")
FIELD_LOGGER_FORM_URL = os.getenv("FIELD_LOGGER_FORM_URL", "https://tally.so/r/44lzd5")
TELEPHONY_FORM_URL = os.getenv("TELEPHONY_FORM_URL", "https://tally.so/r/2EGzLM")

# Telegram Relay
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_OPS_GROUP_ID = os.getenv("TELEGRAM_OPS_GROUP_ID")

settings = Settings()

# ==========================================
# STRICT INTENT TAXONOMY
# ==========================================
VALID_INTENTS = {
    "SERVICE_PURCHASE",
    "BUSINESS_DIAGNOSIS",
    "PORTFOLIO_EXPLORATION",
    "UNCLEAR"
}

# ==========================================
# STATIC SERVICE CATALOG
# ==========================================
SERVICES = {
    "telegram_scheduler": {
        "name": "Telegram Dynamic Scheduler",
        "description": "Automated calendar management and dynamic scheduling bot built on Telegram.",
        "features": [
            "Real-time slot booking",
            "Calendar synchronization",
            "Automated client reminders"
        ],
        "youtube_url": "https://www.youtube.com/watch?v=example_scheduler",
        "status": "BUILT"
    },
    "whatsapp_automation": {
        "name": "WhatsApp Lead Gen & Workflow Bot",
        "description": "Custom WhatsApp Cloud API integration to capture leads, qualify prospects, and route workflows 24/7.",
        "features": [
            "Interactive buttons and list menus",
            "Automated multi-step qualification",
            "CRM synchronization"
        ],
        "youtube_url": "",
        "status": "BUILT"
    },
    "workflow_automation": {
        "name": "Custom Operations & Fault Tracking",
        "description": "Automated alert and task-routing pipelines connecting internal tools, site monitors, and communication channels.",
        "features": [
            "Website uptime & fault monitoring alerts",
            "Cross-platform data bridging",
            "Custom webhooks and API connectors"
        ],
        "youtube_url": "",
        "status": "BUILT"
    }
}

# ==========================================
# HONEST PORTFOLIO CATALOG
# ==========================================
PROJECTS = {
    "telegram_dynamic_scheduler": {
        "name": "Telegram Dynamic Scheduler",
        "description": "A Telegram-based scheduling and calendar management system.",
        "status": "BUILT",
        "availability": "VERIFICATION_PENDING",
        "youtube_url": "https://youtu.be/naB59uo86v4?si=p0Badn-VD9zPEY_c",
        "notes": "https://app.notion.com/p/Dynamic-Scheduler-Bot-3b9d07dc818580b5ab2dec4c95e80547?v=3a7d07dc818580d78fa6000c60bc6eac&source=copy_link."
    },
    "whatsapp_project_site_tracker": {
        "name": "WhatsApp Project Site Tracker",
        "description": "A demonstration project built for managing project and site information through WhatsApp.",
        "status": "DEMO",
        "availability": "NOT_PUBLIC",
        "youtube_url": "",
        "notes": "This is a demonstration project and does not have a dedicated public WhatsApp phone number."
    }
}

# ==========================================
# AGENCY OPERATIONAL SETTINGS
# ==========================================
REVIEW_SLA = "within 24 business hours"