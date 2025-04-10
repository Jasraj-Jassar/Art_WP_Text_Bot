import random
import logging
from datetime import datetime
import openai
from prompt_history import load_last_prompts, update_last_prompts

def fetch_good_morning_text(api_key, recipient_name):
    """
    Fetch a unique, non-cliché good morning message using the OpenAI API.
    Incorporates past messages to create a new and original text.
    
    Args:
        api_key (str): The OpenAI API key.
        recipient_name (str): The name of the recipient.
    
    Returns:
        str: The complete morning message with a greeting prefix, or None on error.
    """
    openai.api_key = api_key
    today_date = datetime.now().strftime("%Y-%m-%d")
    themes = ["serendipity", "adventure", "quote", "joy", "calm", "hope", "coffee", "work"]
    theme_word = random.choice(themes)
    
    # Load the last three generated messages if they exist.
    last_messages = load_last_prompts()
    
    prompt_system = "You are an genuine human that wishes his friend good morning messages."
    prompt_user = (
        "For example, Good morning! Hope your day starts off great. "
        "Morning! Wishing you a smooth and productive day. "
        "Hope you slept well. Let’s crush this day. "
        "Don't say good morning, just start with the line. "
        "For example, you can say, 'I hope your day goes well.' "
        "Generate a single one-sentence message in English, no more than one line, "
        "avoiding overused phrases, clichés, or language. "
    )
    
    if last_messages:
        prompt_user += f"Please create a new message that is completely different from these. Previously generated messages: {last_messages}.  "
    
    prompt_user += "Add a simple smile emoji at the end."
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Replace with your desired model
            messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": prompt_user}
            ]
        )
        raw_message = response.choices[0].message.content.strip()
        logging.info("Successfully fetched the morning text.")
        
        # Add the permanent greeting
        final_message = f"Доброго ранку {recipient_name}, {raw_message}"
        update_last_prompts(raw_message)
        return final_message
    except Exception as e:
        logging.error(f"Error fetching good morning text: {e}")
        return None
