 # config.py
from dotenv import load_dotenv
import os
import logging

load_dotenv()  # Loads from .env into environment

TEMPORAL_CLIENT = os.getenv("TEMPORAL_CLIENT")
TEMPORAL_WORKFLOW = os.getenv("TEMPORAL_WORKFLOW")
TEMPORAL_TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE")
START_SIGNAL_FUNCTION = os.getenv("START_SIGNAL_FUNCTION")
POLLING_INTERVAL = os.getenv("POLLING_INTERVAL")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS")
FASTAPI_HOST = os.getenv("FASTAPI_HOST")
FASTAPI_PORT = os.getenv("FASTAPI_PORT")
FASTAPI_RELOAD = os.getenv("FASTAPI_RELOAD")

if POLLING_INTERVAL is None:
    POLLING_INTERVAL=0.5

if TEMPORAL_CLIENT is None:
    raise ValueError("TEMPORAL_CLIENT is not set")
if TEMPORAL_WORKFLOW is None:
    raise ValueError("TEMPORAL_WORKFLOW is not set")
if TEMPORAL_TASK_QUEUE is None:
    raise ValueError("TEMPORAL_TASK_QUEUE is not set")
if START_SIGNAL_FUNCTION is None:
    raise ValueError("START_SIGNAL_FUNCTION is not set")
if ALLOWED_ORIGINS is None:
    raise ValueError("ALLOWED_ORIGINS is not set")


def get_logger(name: str):
    logger = logging.getLogger(name)

    if not logger.handlers:  # Prevent duplicate handlers
        logger.setLevel(logging.DEBUG)

        # File handler only
        file_handler = logging.FileHandler("app.log")
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    return logger
