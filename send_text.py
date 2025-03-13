import os
import sys
import json
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv
import openai
import pywhatkit
import random

# -------------------------------
# Logging configuration
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("morning_message.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Load environment variables once
load_dotenv()

# -------------------------------
# Load sensitive data from .env
# -------------------------------
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

# -------------------------------
# Last Prompt Storage Functions
# -------------------------------
def load_last_prompts(file_path="three_last_used.json"):
    """
    Load the list of the last three generated messages (raw GPT output without prefix) from a JSON file.
    Returns an empty list if the file doesn't exist or on error.
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except json.JSONDecodeError:
            logging.warning("JSON decode error in three_last_used.json. Starting with an empty list.")
    return []

def update_last_prompts(new_message, file_path="three_last_used.json"):
    """
    Update the JSON file with the new generated raw message (without greeting prefix).
    Only the last three messages are kept.
    """
    prompts = load_last_prompts(file_path)
    if len(prompts) >= 3:
        prompts = prompts[-2:]
    prompts.append(new_message)
    with open(file_path, "w") as f:
        json.dump(prompts, f)

# -------------------------------
# Fetch Good Morning Message
# -------------------------------
def fetch_good_morning_text(api_key, recipient_name):
    """
    Fetch a unique, non-cliché good morning message using the OpenAI API.
    
    The prompt instructs the model to:
      - Generate a one-sentence message that is natural, original, and subtly flirty.
      - Avoid clichéd phrases and any invitation to meet up.
      - Consider previously generated messages (without the greeting prefix) so as to produce something new.
    
    Note: The greeting "Доброго ранку {recipient_name}," is now added permanently after generation.
    
    Args:
        api_key (str): The OpenAI API key.
        recipient_name (str): The name of the message recipient.
    
    Returns:
        str: The complete good morning message with the permanent greeting prefixed,
             or None if an error occurs.
    """
    openai.api_key = api_key
    today_date = datetime.now().strftime("%Y-%m-%d")
    themes = ["serendipity", "adventure", "quote", "joy", "calm", "hope", "coffee", "Work"]
    theme_word = random.choice(themes)
    
    # Load last three generated messages if they exist.
    last_messages = load_last_prompts()
    
    prompt_system = (
        "You are an assistant that generates original, natural, and non-inviting good morning messages."
    )
    prompt_user = (
        "Dont say good morning, just start with the line"
        #f"Today is {today_date}. Generate a single one-sentence English good morning message that is genuine and original, subtly incorporating the theme {theme_word}. "
        "The message should be in English, no more than one line, and avoid overused phrases, clichés, or simping language. "
    )
    
    if last_messages:
        prompt_user += f"Please create a new message that is completely different from these focus on generating something new and way different please. Previously generated messages: {last_messages}.  "
    
    prompt_user += "Add a simple smile emoji at the end."
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Replace with your desired model (e.g., "gpt-3.5-turbo")
            messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": prompt_user}
            ]
        )
        # Retrieve the raw message from GPT (without the greeting prefix)
        raw_message = response.choices[0].message.content.strip()
        logging.info("Successfully fetched the morning text.")
        
        # Permanently add the greeting to the message for sending
        final_message = f"Доброго ранку {recipient_name}, {raw_message}"
        
        # Update the stored prompts with the raw message only.
        update_last_prompts(raw_message)
        
        return final_message
    except Exception as e:
        logging.error(f"Error fetching good morning text: {e}")
        return None

# -------------------------------
# Send WhatsApp Message
# -------------------------------
def send_whatsapp_message(phone_number, message, hour=8, minute=0):
    """
    Schedule sending a WhatsApp message using pywhatkit.
    
    Args:
        phone_number (str): The recipient's phone number.
        message (str): The message to be sent.
        hour (int): Hour (24-hour format) when the message should be sent.
        minute (int): Minute when the message should be sent.
    """
    try:
        logging.info(f"Scheduling message to {phone_number} at {hour}:{minute:02d}.")
        pywhatkit.sendwhatmsg(phone_number, message, hour, minute)
        logging.info("Message scheduled successfully.")
    except Exception as e:
        logging.error(f"Error scheduling WhatsApp message: {e}")

# -------------------------------
# Main entry point
# -------------------------------
def main():
    # Load sensitive data from environment
    api_key = load_api_key()
    phone_no = load_phone_no()
    recipient_name = load_recipient_name()
    
    # Parse command-line arguments for scheduling time
    parser = argparse.ArgumentParser(
        description="Fetch and send a unique good morning message via WhatsApp."
    )
    parser.add_argument(
        "--hour", type=int, default=8,
        help="Hour (24-hour format) to send the message (default: 8)"
    )
    parser.add_argument(
        "--minute", type=int, default=0, 
        help="Minute to send the message (default: 0)"
    )
    args = parser.parse_args()

    # Fetch and send the message
    message = fetch_good_morning_text(api_key, recipient_name)
    if message:
        logging.info(f"Generated message: {message}")
        send_whatsapp_message(phone_no, message, args.hour, args.minute)
    else:
        logging.error("Failed to generate a message. Exiting.")

if __name__ == "__main__":
    main()
