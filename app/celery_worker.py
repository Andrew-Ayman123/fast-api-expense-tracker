"""Module."""
import logging
import os
import time

from celery import Celery
from dotenv import load_dotenv

load_dotenv()  # Load .env as a fallback

celery = Celery(__name__)
celery.conf.broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
celery.conf.result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

# Configure Celery to store task results
celery.conf.task_track_started = True
celery.conf.result_expires = 3600  # Results stored for 1 hour

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery.task(name="hello")
def say_hello() -> str:
    """Simulate a delayed hello task."""
    logger.info("Starting hello task...")
    time.sleep(5)  # Simulate work with a 5-second delay
    logger.info("Hello from Celery!")
    logger.info("Returning result: ")
    return "Hello task completed successfully!"
