import logging
import pywhatkit

def send_whatsapp_message(phone_number: str, message: str) -> None:
    """
    Send a WhatsApp message using pywhatkit.
    
    Args:
        phone_number (str): The recipient's phone number.
        message (str): The message to be sent.
    """
    try:
        logging.info(f"Sending message to {phone_number}")
        pywhatkit.sendwhatmsg_instantly(phone_number, message)
        logging.info("Message sent successfully.")
    except Exception as e:
        logging.error(f"Error sending WhatsApp message: {e}")
