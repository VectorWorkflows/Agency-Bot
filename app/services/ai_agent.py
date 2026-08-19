import json
import logging
from typing import Dict, Any
import google.generativeai as genai
from app.core.config import settings, VALID_INTENTS

logger = logging.getLogger(__name__)

# Configure the Gemini SDK
genai.configure(api_key=settings.GEMINI_API_KEY)

# Strict classification prompt ensuring the model never hallucinates or acts as a router
CLASSIFIER_SYSTEM_INSTRUCTION = """
You are an intent classification engine for Vector Workflows, an AI and automation agency.
Your sole job is to analyze the user's message and classify their intent into exactly one of these predefined categories:

1. SERVICE_PURCHASE: The user knows what they want, is asking about a specific service, or wants something similar to a known solution.
2. BUSINESS_DIAGNOSIS: The user has a problem, is explaining a manual process, wants an automation audit, or doesn't know what service they need.
3. PORTFOLIO_EXPLORATION: The user wants to see what the agency has built, view past projects, or check demos/walkthroughs.
4. UNCLEAR: The message is ambiguous, off-topic, or cannot be confidently mapped to the above categories.

Rules:
- You must output valid JSON only.
- Follow this exact schema:
{
  "intent": "SERVICE_PURCHASE" | "BUSINESS_DIAGNOSIS" | "PORTFOLIO_EXPLORATION" | "UNCLEAR",
  "confidence": 0.0 to 1.0
}
- Never invent services, projects, prices, or URLs.
- If unsure, always return "UNCLEAR".
"""

try:
    classifier_model = genai.GenerativeModel(
        model_name="gemini-3.6-flash",
        system_instruction=CLASSIFIER_SYSTEM_INSTRUCTION,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.0
        }
    )
except Exception as e:
    logger.error(f"Failed to initialize Gemini classifier model: {e}")
    classifier_model = None


async def classify_intent(user_message: str) -> Dict[str, Any]:
    """
    Sends the user message to Gemini under strict JSON constraints
    and validates the resulting schema and confidence threshold.
    """
    default_result = {"intent": "UNCLEAR", "confidence": 0.0}

    if not classifier_model:
        return default_result

    try:
        response = classifier_model.generate_content(f"User message: \"{user_message}\"")
        raw_text = response.text.strip()
        
        parsed_data = json.loads(raw_text)
        intent = parsed_data.get("intent")
        confidence = parsed_data.get("confidence", 0.0)

        # Validate against allowed taxonomy and type bounds
        if intent not in VALID_INTENTS:
            logger.warning(f"Model returned invalid intent: {intent}. Defaulting to UNCLEAR.")
            return default_result

        if not isinstance(confidence, (int, float)) or confidence < 0.70:
            logger.info(f"Classification confidence too low ({confidence}) or invalid. Routing to UNCLEAR.")
            return {"intent": "UNCLEAR", "confidence": float(confidence)}

        return {"intent": intent, "confidence": float(confidence)}

    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON from Gemini classifier output: {response.text}")
        return default_result
    except Exception as e:
        logger.error(f"Error during intent classification: {e}")
        return default_result