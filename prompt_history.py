import os
import json
import logging

def load_last_prompts(file_path="three_last_used.json"):
    """
    Load the last three raw generated messages from a JSON file.
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
    Update the JSON file with the new raw message.
    Keep only the last three messages.
    """
    prompts = load_last_prompts(file_path)
    if len(prompts) >= 3:
        prompts = prompts[-2:]
    prompts.append(new_message)
    with open(file_path, "w") as f:
        json.dump(prompts, f)
