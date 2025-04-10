import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configure logging (both file and console)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("morning_message.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def load_api_key():
    """
    Load the OpenAI API key from the environment.
    Exits if not found.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logging.error("API_KEY not found in environment. Please set your OPENAI_API_KEY in the .env file.")
        sys.exit(1)
    return api_key

def load_phone_no():
    """
    Load the recipient's phone number from the environment.
    Exits if not found.
    """
    phone_no = os.getenv("PHONE_NO")
    if not phone_no:
        logging.error("Phone number not found in environment. Please set PHONE_NO in the .env file.")
        sys.exit(1)
    return phone_no

def load_recipient_name():
    """
    Load the recipient's name from the environment.
    Exits if not found.
    """
    recipient_name = os.getenv("RECIPIENT_NAME")
    if not recipient_name:
        logging.error("Recipient name not found in environment. Please set RECIPIENT_NAME in the .env file.")
        sys.exit(1)
    return recipient_name
