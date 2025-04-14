import subprocess
import threading
import sys
import logging
from scheduler import MessageScheduler
from collections import defaultdict
from datetime import datetime

class ProcessManager:
    def __init__(self):
        self.processes = defaultdict(list)
        self.threads = defaultdict(list)
        self.logger = logging.getLogger(__name__)
        
    def start_process(self, schedule_id: str, contact_data: dict) -> None:
        """Start a new process for a contact"""
        process = start_instance(contact_data)
        identifier = f"Schedule {schedule_id} ({contact_data['recipient']})"
        
        self.logger.info(f"Starting message process for {contact_data['recipient']} (ID: {schedule_id})")
        
        # Launch a thread to read the process output
        thread = threading.Thread(target=stream_reader, args=(process, identifier, schedule_id), daemon=True)
        thread.start()
        
        # Store process and thread
        self.processes[schedule_id].append(process)
        self.threads[schedule_id].append(thread)
        
    def cleanup_old_processes(self) -> None:
        """Clean up completed processes"""
        for schedule_id in list(self.processes.keys()):
            # Check each process for this schedule
            for i, process in enumerate(self.processes[schedule_id][:]):
                if process.poll() is not None:  # Process has finished
                    self.logger.debug(f"Cleaning up completed process for schedule {schedule_id}")
                    # Remove the process and its thread
                    self.processes[schedule_id].pop(i)
                    if i < len(self.threads[schedule_id]):
                        self.threads[schedule_id].pop(i)
            
            # Remove empty lists
            if not self.processes[schedule_id]:
                del self.processes[schedule_id]
                del self.threads[schedule_id]

def stream_reader(process, identifier, schedule_id):
    """
    Continuously reads output from the subprocess and prints it with an identifier.
    """
    logger = logging.getLogger(f"process.{schedule_id}")
    
    # Read from stdout and print with an identifier.
    for line in iter(process.stdout.readline, ""):
        if not line:
            break
        print(f"[{identifier}][STDOUT] {line.strip()}")
        logger.info(f"{line.strip()}")
        
        # Check if this is a message sent confirmation
        if "Message sent successfully" in line:
            # Log completion of the task
            now = datetime.now()
            print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] ✓ Message for {identifier} sent successfully")
            print(f"Will run again according to schedule. Check upcoming schedules for details.\n")
    
    # Optionally read from stderr
    for line in iter(process.stderr.readline, ""):
        if not line:
            break
        print(f"[{identifier}][STDERR] {line.strip()}")
        logger.error(f"{line.strip()}")

def start_instance(contact_data):
    """
    Constructs the command to run the api_business_logic script with the contact's data
    and starts the process.
    """
    command = [
        "python",
        "api_business_logic.py",
        "--phone", contact_data['phone'],
        "--recipient", contact_data['recipient']
    ]
    
    try:
        # Start the process with output pipes.
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        return process
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error starting process for {contact_data['recipient']}: {e}")
        print(f"Error starting process for {contact_data['recipient']}: {e}")
        sys.exit(1)

def display_weekday_options():
    """Display weekday options for user selection"""
    print("\nSelect weekdays (multiple choices allowed):")
    print("1) Monday")
    print("2) Tuesday")
    print("3) Wednesday")
    print("4) Thursday")
    print("5) Friday")
    print("6) Saturday")
    print("7) Sunday")
    print("8) All weekdays (Monday to Friday)")
    print("9) Weekends (Saturday and Sunday)")
    print("0) All days")

def get_weekdays_from_user():
    """Get weekday selections from user"""
    weekday_map = {
        '1': ['monday'],
        '2': ['tuesday'],
        '3': ['wednesday'],
        '4': ['thursday'],
        '5': ['friday'],
        '6': ['saturday'],
        '7': ['sunday'],
        '8': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
        '9': ['saturday', 'sunday'],
        '0': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    }
    
    display_weekday_options()
    selected = input("  Enter numbers (space-separated): ").strip().split()
    weekdays = []
    
    for choice in selected:
        if choice in weekday_map:
            weekdays.extend(weekday_map[choice])
    
    return weekdays

def display_upcoming_schedules(scheduler):
    """Display the upcoming schedules in the next 7 days"""
    print("\n===== UPCOMING SCHEDULED MESSAGES =====")
    upcoming = scheduler.get_upcoming_schedules(days=7)
    
    if not upcoming:
        print("No upcoming scheduled messages in the next 7 days.")
        return
    
    # Group by day for easier reading
    for day, schedules in upcoming.items():
        print(f"\n{day.capitalize()}:")
        for schedule in schedules:
            time_str = f"{schedule['hour']:02d}:{schedule['minute']:02d}"
            print(f"  {time_str} - {schedule['recipient']} ({schedule['schedule_id']})")
    
    print("\n=======================================")

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("scheduler.log"),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting message scheduler application")
    
    # Initialize the scheduler and process manager
    scheduler = MessageScheduler()
    process_manager = ProcessManager()
    
    # Check if there are existing schedules
    existing_schedules = scheduler.get_all_schedules()
    if existing_schedules:
        print(f"\nFound {len(existing_schedules)} existing schedule(s):")
        for schedule_id, schedule in existing_schedules.items():
            weekdays_str = ", ".join(day.capitalize() for day in schedule['weekdays'])
            print(f"  {schedule_id}: {schedule['recipient']} - Every {weekdays_str} at {schedule['hour']:02d}:{schedule['minute']:02d}")
        
        use_existing = input("\nUse existing schedules? (y/n): ").lower().strip()
        if use_existing == 'y':
            logger.info("Using existing schedules")
            print("\nUsing existing schedules. Starting the scheduler...")
            
            # Display upcoming schedules
            display_upcoming_schedules(scheduler)
            
            print("Press Ctrl+C to exit and stop all processes.\n")
            run_scheduler(scheduler, process_manager)
            return
    
    # Prompt for the number of contacts
    try:
        num_contacts = int(input("Enter the number of contacts: "))
        logger.info(f"User entered {num_contacts} contacts")
    except ValueError:
        logger.error("Invalid number entered. Exiting.")
        print("Invalid number entered. Exiting.")
        sys.exit(1)
    
    # Collect details for each contact
    for i in range(num_contacts):
        print(f"\nContact {i + 1} details:")
        phone = input("  Phone number: ").strip()
        recipient = input("  Recipient name: ").strip()
        try:
            hour = int(input("  Scheduled Hour (24-hour format): ").strip())
            minute = int(input("  Scheduled Minute: ").strip())
        except ValueError:
            logger.error("Invalid input for hour or minute. Exiting.")
            print("Invalid input for hour or minute. Exiting.")
            sys.exit(1)
            
        # Get weekdays using the new helper function
        print("  Note: Messages will automatically repeat every week on the selected days.")
        weekdays = get_weekdays_from_user()
        
        if not weekdays:
            logger.warning("No valid weekdays selected. Using default (Monday).")
            print("  No valid weekdays selected. Using default (Monday).")
            weekdays = ['monday']
        
        # Add schedule to the scheduler
        schedule_id = f"contact_{i+1}"
        scheduler.add_schedule(
            schedule_id=schedule_id,
            phone=phone,
            recipient=recipient,
            hour=hour,
            minute=minute,
            weekdays=weekdays
        )
        logger.info(f"Added schedule {schedule_id} for {recipient} on {', '.join(weekdays)} at {hour:02d}:{minute:02d}")
        
        # Confirm schedule
        weekdays_str = ", ".join(day.capitalize() for day in weekdays)
        print(f"\n  Schedule created: Every {weekdays_str} at {hour:02d}:{minute:02d}")
    
    print("\nAll schedules have been saved. Starting the scheduler...")
    
    # Display upcoming schedules
    display_upcoming_schedules(scheduler)
    
    print("Press Ctrl+C to exit and stop all processes.\n")
    run_scheduler(scheduler, process_manager)

def run_scheduler(scheduler, process_manager):
    """Run the scheduler continuously"""
    logger = logging.getLogger(__name__)
    
    try:
        # Show upcoming schedules on startup
        upcoming_summary = scheduler.summarize_upcoming_schedules()
        logger.info(f"Scheduler started. Upcoming: {upcoming_summary}")
        
        # Run the scheduler continuously
        for schedule_id, schedule in scheduler.run_continuously():
            # Start new process for this schedule
            process_manager.start_process(schedule_id, schedule)
            
            weekdays_str = ", ".join(day.capitalize() for day in schedule['weekdays'])
            now = datetime.now()
            print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] Executing schedule for {schedule['recipient']}")
            print(f"Repeats every {weekdays_str} at {schedule['hour']:02d}:{schedule['minute']:02d}")
            
            # Display upcoming schedules after each execution
            display_upcoming_schedules(scheduler)
            
            # Clean up any completed processes
            process_manager.cleanup_old_processes()
            
    except KeyboardInterrupt:
        logger.info("Interrupt received, stopping scheduler")
        print("\nInterrupt received, stopping scheduler...")
        print("All schedules have been saved to message_schedules.json")
        sys.exit(0)

if __name__ == "__main__":
    main()
