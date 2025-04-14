# Art_WP_Text_Bot

A simple, reliable application for scheduling automated WhatsApp messages. Supports both a graphical user interface and command-line operation.

## Features

- Schedule WhatsApp messages for specific days of the week and times
- Manage contacts via an intuitive GUI
- Monitor upcoming scheduled messages
- View real-time console output
- Automatic scheduler pausing during contact management
- Auto-restart of the scheduler after contact changes

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/Jasraj-Jassar/Art_WP_Text_Bot.git
   cd Art_WP_Text_Bot
   ```

2. Create and activate a virtual environment:
   ```bash
   # On Linux/Mac
   python -m venv .venv
   source .venv/bin/activate
   
   # On Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install PyQt6 pywhatkit python-dotenv openai
   ```

## Setup

1. Make sure you have WhatsApp Web logged in on your browser
2. If using the OpenAI message generation feature, ensure you have an API key
3. Create a `.env` file in the project root directory with the following content:

   ```
   # OpenAI API Key for message generation
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Default recipient information (can be overridden in the application)
   PHONE_NO=+1234567890  # Include country code with + sign
   RECIPIENT_NAME=RecipientName
   
   # Optional: Customize default scheduling time
   DEFAULT_HOUR=8
   DEFAULT_MINUTE=0
   ```

   Replace the placeholder values with your actual information.

## Usage

### GUI Interface

To run the application with the graphical interface:

```
python gui_manager.py
```

The GUI consists of two main tabs:

1. **Manage Contacts**: Add, edit, and remove contacts, view upcoming scheduled messages, and control the scheduler.
2. **Console Output**: View real-time logs and status updates from the scheduler.

#### Managing Contacts

- **Add Contact**: Enter phone number, recipient name, and schedule timing.
- **Edit Contact**: Modify existing contact information and schedules.
- **Remove Contact**: Delete contacts from the scheduler.

The scheduler automatically pauses when adding, editing, or removing contacts to prevent conflicts, and resumes afterward if it was previously running.

#### Scheduling Options

- Set specific hours and minutes for message delivery
- Select days of the week (with quick selection buttons for weekdays, weekends, or all days)
- View upcoming scheduled messages for the next 24 hours

### Command-Line Interface

To run the application from the command line:

```
python manager.py --run
```

The CLI menu offers the following options:

1. View all contacts
2. Add new contact
3. Edit existing contact
4. Remove contact
5. Start scheduler
0. Exit

Follow the on-screen prompts to manage your messaging schedules.

## Requirements

- Python 3.6+
- PyQt6 (for GUI)
- pywhatkit
- python-dotenv
- openai (for message generation)

## Credits

- [PyWhatKit](https://github.com/Ankit404butfound/PyWhatKit): An awesome library that powers the WhatsApp messaging functionality
- [OpenAI](https://openai.com): For providing easy access to LLMs that helped develop this application
- PyQt6: For the GUI framework
- Python: For the core programming language

## Developed by Jas Jassar

This project was developed by Jas Jassar. Contributions, suggestions, and feedback are welcome.