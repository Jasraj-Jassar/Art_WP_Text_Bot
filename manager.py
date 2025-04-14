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

def display_schedule_menu():
    """Display schedule management menu"""
    print("\n===== SCHEDULE MANAGEMENT =====")
    print("1) View all contacts")
    print("2) Add new contact")
    print("3) Edit existing contact")
    print("4) Remove contact")
    print("5) Start scheduler")
    print("0) Exit")
    print("=============================")
    return input("Enter your choice: ").strip()

def display_all_contacts(scheduler):
    """Display all contacts in the schedule"""
    schedules = scheduler.get_all_schedules()
    if not schedules:
        print("\nNo contacts scheduled.")
        return
    
    print("\n===== SCHEDULED CONTACTS =====")
    for i, (schedule_id, schedule) in enumerate(schedules.items(), 1):
        weekdays_str = ", ".join(day.capitalize() for day in schedule['weekdays'])
        print(f"{i}) {schedule_id}: {schedule['recipient']} - {schedule['phone']}")
        print(f"   Schedule: Every {weekdays_str} at {schedule['hour']:02d}:{schedule['minute']:02d}")
    print("=============================")

def add_new_contact(scheduler):
    """Add a new contact to the schedule"""
    print("\n----- Add New Contact -----")
    
    # Get next available ID
    existing_ids = list(scheduler.get_all_schedules().keys())
    if existing_ids:
        # Find the highest contact_X number
        contact_nums = [int(id.split('_')[1]) for id in existing_ids if id.startswith('contact_')]
        next_id = max(contact_nums) + 1 if contact_nums else 1
    else:
        next_id = 1
    
    schedule_id = f"contact_{next_id}"
    
    # Get contact information
    phone = input("Phone number: ").strip()
    recipient = input("Recipient name: ").strip()
    
    try:
        hour = int(input("Scheduled Hour (24-hour format): ").strip())
        minute = int(input("Scheduled Minute: ").strip())
        
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            print("Invalid time. Hour must be 0-23, minute must be 0-59.")
            return
    except ValueError:
        print("Invalid input for hour or minute.")
        return
    
    # Get weekdays
    print("Note: Messages will automatically repeat every week on the selected days.")
    weekdays = get_weekdays_from_user()
    
    if not weekdays:
        print("No valid weekdays selected. Using default (Monday).")
        weekdays = ['monday']
    
    # Add schedule
    scheduler.add_schedule(
        schedule_id=schedule_id,
        phone=phone,
        recipient=recipient,
        hour=hour,
        minute=minute,
        weekdays=weekdays
    )
    
    weekdays_str = ", ".join(day.capitalize() for day in weekdays)
    print(f"\nContact added: {recipient}")
    print(f"Schedule: Every {weekdays_str} at {hour:02d}:{minute:02d}")

def edit_contact(scheduler):
    """Edit an existing contact in the schedule"""
    display_all_contacts(scheduler)
    schedules = scheduler.get_all_schedules()
    
    if not schedules:
        return
    
    # Create a mapping of displayed numbers to schedule IDs
    id_map = {i: schedule_id for i, schedule_id in enumerate(schedules.keys(), 1)}
    
    try:
        choice = int(input("\nEnter the number of the contact to edit (0 to cancel): "))
        if choice == 0:
            return
        
        if choice not in id_map:
            print("Invalid choice.")
            return
        
        schedule_id = id_map[choice]
        schedule = scheduler.get_schedule(schedule_id)
        
        print(f"\nEditing contact: {schedule['recipient']}")
        print("Leave fields blank to keep existing values.\n")
        
        # Phone
        new_phone = input(f"Phone number [{schedule['phone']}]: ").strip()
        if not new_phone:
            new_phone = schedule['phone']
        
        # Recipient
        new_recipient = input(f"Recipient name [{schedule['recipient']}]: ").strip()
        if not new_recipient:
            new_recipient = schedule['recipient']
        
        # Hour
        new_hour = input(f"Hour (24-hour format) [{schedule['hour']}]: ").strip()
        if new_hour:
            try:
                new_hour = int(new_hour)
                if new_hour < 0 or new_hour > 23:
                    print("Invalid hour. Using previous value.")
                    new_hour = schedule['hour']
            except ValueError:
                print("Invalid input. Using previous value.")
                new_hour = schedule['hour']
        else:
            new_hour = schedule['hour']
        
        # Minute
        new_minute = input(f"Minute [{schedule['minute']}]: ").strip()
        if new_minute:
            try:
                new_minute = int(new_minute)
                if new_minute < 0 or new_minute > 59:
                    print("Invalid minute. Using previous value.")
                    new_minute = schedule['minute']
            except ValueError:
                print("Invalid input. Using previous value.")
                new_minute = schedule['minute']
        else:
            new_minute = schedule['minute']
        
        # Weekdays
        print(f"Current weekdays: {', '.join(day.capitalize() for day in schedule['weekdays'])}")
        change_weekdays = input("Change weekdays? (y/n): ").lower().strip() == 'y'
        
        if change_weekdays:
            new_weekdays = get_weekdays_from_user()
            if not new_weekdays:
                print("No valid weekdays selected. Using previous values.")
                new_weekdays = schedule['weekdays']
        else:
            new_weekdays = schedule['weekdays']
        
        # Update schedule
        scheduler.add_schedule(
            schedule_id=schedule_id,
            phone=new_phone,
            recipient=new_recipient,
            hour=new_hour,
            minute=new_minute,
            weekdays=new_weekdays
        )
        
        weekdays_str = ", ".join(day.capitalize() for day in new_weekdays)
        print(f"\nContact updated: {new_recipient}")
        print(f"Schedule: Every {weekdays_str} at {new_hour:02d}:{new_minute:02d}")
        
    except ValueError:
        print("Invalid input.")

def remove_contact(scheduler):
    """Remove a contact from the schedule"""
    display_all_contacts(scheduler)
    schedules = scheduler.get_all_schedules()
    
    if not schedules:
        return
    
    # Create a mapping of displayed numbers to schedule IDs
    id_map = {i: schedule_id for i, schedule_id in enumerate(schedules.keys(), 1)}
    
    try:
        choice = int(input("\nEnter the number of the contact to remove (0 to cancel): "))
        if choice == 0:
            return
        
        if choice not in id_map:
            print("Invalid choice.")
            return
        
        schedule_id = id_map[choice]
        schedule = scheduler.get_schedule(schedule_id)
        
        confirm = input(f"Are you sure you want to remove {schedule['recipient']}? (y/n): ").lower().strip() == 'y'
        if confirm:
            scheduler.remove_schedule(schedule_id)
            print(f"\nContact {schedule['recipient']} removed successfully.")
        else:
            print("Operation cancelled.")
        
    except ValueError:
        print("Invalid input.")

def manage_schedules(scheduler, process_manager):
    """Main schedule management function"""
    while True:
        choice = display_schedule_menu()
        
        if choice == '1':
            display_all_contacts(scheduler)
        elif choice == '2':
            add_new_contact(scheduler)
        elif choice == '3':
            edit_contact(scheduler)
        elif choice == '4':
            remove_contact(scheduler)
        elif choice == '5':
            # Start the scheduler
            print("\nStarting scheduler...")
            display_upcoming_schedules(scheduler)
            print("Press Ctrl+C to exit and stop all processes.\n")
            run_scheduler(scheduler, process_manager)
            return
        elif choice == '0':
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")

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
    
    # Always go to schedule management instead of the old workflow
    manage_schedules(scheduler, process_manager)

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
