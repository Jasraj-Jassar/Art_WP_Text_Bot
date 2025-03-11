# Art_WP_Text_Bot 

## Overview
This Python script generates a unique, natural, and subtle good morning message using the OpenAI API, and schedules it to be sent via WhatsApp using pywhatkit. It is designed with robust error handling and logging to ensure reliability and maintainability.

## Features
- **Unique Message Generation:** Uses OpenAI's GPT model to create original good morning messages.
- **WhatsApp Scheduling:** Automatically schedules messages to be sent via WhatsApp.
- **Secure Configuration:** Sensitive data is managed through an external `.env` file.
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

4. **Create a `.env` File:**
   In the root directory of the project, create a file named `.env` with the following content. You can use the commands below to quickly create it:

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
Run the script via the command line. You can optionally specify the time to send the message using command-line arguments. For example:
```bash
python send_text.py --hour 8 --minute 0
```
If no scheduling time is provided, the default is set to 8:00 AM (MST).

## Logging
The script logs important events and errors to both:
- **Console Output:** For real-time monitoring.
- **Log File:** `morning_message.log` in the project directory for persistent record keeping.

## Notes
- Ensure your OpenAI API key has access to the required model.
- WhatsApp Web must be active and logged in for pywhatkit to send messages successfully.

## Developed by Jas Jassar
This project was developed by Jas Jassar. Contributions, suggestions, and feedback are welcome.
