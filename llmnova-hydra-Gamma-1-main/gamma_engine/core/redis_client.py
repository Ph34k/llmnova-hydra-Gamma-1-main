import logging
import os

import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_client = None
REDIS_URL = os.getenv("REDIS_URL")

if REDIS_URL:
    try:
        # The decode_responses=True option ensures that Redis returns strings, not bytes.
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        # Check if the connection is successful
        redis_client.ping()
        logger.info("Successfully connected to Redis.")
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Could not connect to Redis: {e}")
        redis_client = None
else:
    logger.warning("REDIS_URL environment variable not set. Redis client not created.")

def get_redis_client():
    """
    Returns the Redis client instance.
    Returns None if the connection could not be established.
    """
    return redis_client
