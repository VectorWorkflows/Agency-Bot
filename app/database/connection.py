import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    # Initialize PyMongo client with a 5-second timeout for fail-fast behavior
    client: MongoClient = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    
    # Ping to verify the connection is active
    client.admin.command("ping")
    logger.info("Successfully connected to MongoDB Atlas.")
except ConnectionFailure as e:
    logger.critical(f"Failed to connect to MongoDB: {e}")
    raise

# Define Database and Collection
db = client["vector_agency_db"]
user_states = db["user_states"]