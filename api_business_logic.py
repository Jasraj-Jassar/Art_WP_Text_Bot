import argparse
import logging
from config import load_api_key, load_phone_no, load_recipient_name
from message_generator import fetch_good_morning_text
from send_text import send_whatsapp_message

def send_scheduled_message(phone: str, recipient: str) -> None:
    """
    Send a scheduled message using the provided contact information.
    
    Args:
        phone (str): Recipient's phone number
        recipient (str): Recipient's name
    """
    api_key = load_api_key()
    message = fetch_good_morning_text(api_key, recipient)
    if message:
        logging.info(f"Generated message: {message}")
        send_whatsapp_message(phone, message)
    else:
        logging.error("Failed to generate a message.")

def main():
    # Parse command-line arguments for contact data
    parser = argparse.ArgumentParser(
        description="Fetch and send a unique good morning message via WhatsApp."
    )
    parser.add_argument(
        "--phone", type=str,
        help="Recipient phone number. Overrides the environment variable PHONE_NO if provided."
    )
    parser.add_argument(
        "--recipient", type=str,
        help="Recipient name. Overrides the environment variable RECIPIENT_NAME if provided."
    )
    args = parser.parse_args()

    # Load sensitive data from environment if not provided via command line
    phone_no = args.phone if args.phone else load_phone_no()
    recipient_name = args.recipient if args.recipient else load_recipient_name()

    # Send the message
    send_scheduled_message(phone_no, recipient_name)

if __name__ == "__main__":
    main()
