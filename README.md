# Art_WP_Text_Bot

## Overview
This Python script generates a unique, natural, and subtle good morning message using the OpenAI API and schedules it to be sent via WhatsApp using pywhatkit. It is designed with robust error handling and logging to ensure reliability and maintainability. In addition to loading sensitive data from an environment file, you can now also pass the recipient phone number and name as command-line arguments.

## Features
- **Unique Message Generation:** Uses OpenAI's 4o mini GPT model to create original good morning messages.
- **WhatsApp Scheduling:** Automatically schedules messages to be sent via WhatsApp.
- **Flexible Configuration:** Sensitive data can be managed via an external `.env` file or overridden directly by command-line arguments.
- **Robust Logging:** Logs events and errors to both the console and a log file.

## Requirements
- Python 3.8 or higher
- Python packages:
  - [openai](https://pypi.org/project/openai/)
  - [pywhatkit](https://pypi.org/project/pywhatkit/)
  - [python-dotenv](https://pypi.org/project/python-dotenv/)

## Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Jasraj-Jassar/Art_WP_Text_Bot
   cd Art_WP_Text_Bot
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install openai pywhatkit python-dotenv
   ```

4. **Create a `.env` File (Optional):**
   If you prefer to use an environment file for the default configuration, create a file named `.env` in the project root with the following content:

   **On Linux/Mac:**
   ```bash
   cat <<EOT >> .env
   OPENAI_API_KEY=your_openai_api_key_here
   PHONE_NO=your_recipient_phone_number
   RECIPIENT_NAME=RecipientName
   EOT
   ```

   **On Windows (PowerShell):**
   ```powershell
   echo OPENAI_API_KEY=your_openai_api_key_here > .env
   echo PHONE_NO=your_recipient_phone_number >> .env
   echo RECIPIENT_NAME=RecipientName >> .env
   ```

## Usage
Run the script via the command line. You can optionally specify the scheduling time, recipient phone number, and recipient name using command-line arguments. For example:
```bash
python main.py --hour 8 --minute 0 --phone "+1234567890" --recipient "Alice"
```
- **--hour & --minute:** Set the time (24-hour format) to send the message (default is 8:00 AM).
- **--phone & --recipient:** Override the default phone number and recipient name that would otherwise be loaded from the `.env` file.

If no command-line values are provided for phone and recipient, the script will use the values specified in the `.env` file.

## Logging
The script logs important events and errors to:
- **Console Output:** For real-time monitoring.
- **Log File:** `morning_message.log` in the project directory, for persistent logging.

## Notes
- Ensure your OpenAI API key has the appropriate access rights for the desired model.
- WhatsApp Web must be active and logged in for pywhatkit to send messages successfully.

## Developed by Jas Jassar
This project was developed by Jas Jassar. Contributions, suggestions, and feedback are welcome.