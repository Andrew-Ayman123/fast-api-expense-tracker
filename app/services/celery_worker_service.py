"""Module."""
import time

from celery import Celery

from app.dependencies import get_env_settings
from app.utils.logger_util import get_logger

celery = Celery(__name__)
celery.conf.broker_url = get_env_settings().celery_broker_url
celery.conf.result_backend = get_env_settings().celery_result_backend

# Configure Celery to store task results
celery.conf.task_track_started = True
celery.conf.result_expires = 3600  # Results stored for 1 hour


@celery.task(name="hello")
def say_hello() -> str:
    """Simulate a delayed hello task."""
    get_logger().info("Starting hello task...")
    time.sleep(5)  # Simulate work with a 5-second delay
    get_logger().info("Hello from Celery!")
    get_logger().info("Returning result: ")
    return "Hello task completed successfully!"
