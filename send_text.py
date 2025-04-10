import logging
import pywhatkit

def send_whatsapp_message(phone_number, message, hour=8, minute=0):
    """
    Schedule sending a WhatsApp message using pywhatkit.
    
    Args:
        phone_number (str): The recipient's phone number.
        message (str): The message to be sent.
        hour (int): Hour (24-hour format) for sending.
        minute (int): Minute for sending.
    """
    try:
        logging.info(f"Scheduling message to {phone_number} at {hour}:{minute:02d}.")
        pywhatkit.sendwhatmsg(phone_number, message, hour, minute)
        logging.info("Message scheduled successfully.")
    except Exception as e:
        logging.error(f"Error scheduling WhatsApp message: {e}")
