import logging
from datetime import datetime, timezone
from typing import Any, Dict

from pymongo import ReturnDocument
from pymongo.errors import PyMongoError
from app.database.connection import user_states

logger = logging.getLogger(__name__)

def get_or_create_user(phone_number: str) -> Dict[str, Any]:
    """
    Retrieves the user document or creates a new one with the MVP schema.
    Initial state is strictly set to 'NEW'.
    """
    try:
        now = datetime.now(timezone.utc)
        default_document = {
            "phone_number": phone_number,
            "state": "NEW",
            "context": {
                "detected_intent": None,
                "selected_service": None,
                "selected_project": None,
                "workflow_description": None,
                "human_requested": False,
                "human_request_reason": None
            },
            "chat_history": [],
            "created_at": now,
            "updated_at": now
        }
        
        user = user_states.find_one_and_update(
            {"phone_number": phone_number},
            {"$setOnInsert": default_document},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
        return user
    except PyMongoError as e:
        logger.error(f"Database error in get_or_create_user for {phone_number}: {e}")
        raise

def set_user_state(phone_number: str, new_state: str) -> None:
    """Updates the active application state."""
    try:
        user_states.update_one(
            {"phone_number": phone_number},
            {
                "$set": {
                    "state": new_state,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
    except PyMongoError as e:
        logger.error(f"Database error in set_user_state for {phone_number}: {e}")
        raise

def update_user_context(phone_number: str, key: str, value: Any) -> None:
    """Updates a specific key-value pair within the user's nested context dictionary."""
    try:
        user_states.update_one(
            {"phone_number": phone_number},
            {
                "$set": {
                    f"context.{key}": value,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
    except PyMongoError as e:
        logger.error(f"Database error in update_user_context for {phone_number}: {e}")
        raise

def request_human(phone_number: str, reason: str) -> None:
    """Flags the user context for human handoff and updates the state."""
    try:
        user_states.update_one(
            {"phone_number": phone_number},
            {
                "$set": {
                    "state": "HUMAN_REQUEST",
                    "context.human_requested": True,
                    "context.human_request_reason": reason,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        logger.info(f"HUMAN HANDOFF TRIGGERED for {phone_number}. Reason: {reason}")
    except PyMongoError as e:
        logger.error(f"Database error in request_human for {phone_number}: {e}")
        raise

def append_chat_history(phone_number: str, role: str, content: str) -> None:
    """
    Appends verbatim messages to the chat history array.
    This ensures no user explanation is ever lost or altered.
    """
    try:
        new_message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc)
        }
        
        user_states.update_one(
            {"phone_number": phone_number},
            {
                "$push": {"chat_history": new_message},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            }
        )
    except PyMongoError as e:
        logger.error(f"Database error in append_chat_history for {phone_number}: {e}")
        raise

def reset_to_menu(phone_number: str) -> None:
    """Soft reset: Returns the user to the main menu while preserving their history and context."""
    set_user_state(phone_number, "MAIN_MENU")