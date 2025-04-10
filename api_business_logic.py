import argparse
import logging
from config import load_api_key, load_phone_no, load_recipient_name
from message_generator import fetch_good_morning_text
from send_text import send_whatsapp_message

def main():
    # Parse command-line arguments for scheduling and contact data
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
    parser.add_argument(
        "--phone", type=str,
        help="Recipient phone number. Overrides the environment variable PHONE_NO if provided."
    )
    parser.add_argument(
        "--recipient", type=str,
        help="Recipient name. Overrides the environment variable RECIPIENT_NAME if provided."
    )
    args = parser.parse_args()

    # Load sensitive data from environment if not provided via command line.
    api_key = load_api_key()
    phone_no = args.phone if args.phone else load_phone_no()
    recipient_name = args.recipient if args.recipient else load_recipient_name()

    # Fetch and send the message
    message = fetch_good_morning_text(api_key, recipient_name)
    if message:
        logging.info(f"Generated message: {message}")
        send_whatsapp_message(phone_no, message, args.hour, args.minute)
    else:
        logging.error("Failed to generate a message. Exiting.")

if __name__ == "__main__":
    main()
