import subprocess
import threading
import sys

def stream_reader(process, identifier):
    """
    Continuously reads output from the subprocess and prints it with an identifier.
    """
    # Read from stdout and print with an identifier.
    for line in iter(process.stdout.readline, ""):
        if not line:
            break
        print(f"[{identifier}][STDOUT] {line.strip()}")
    
    # Optionally read from stderr
    for line in iter(process.stderr.readline, ""):
        if not line:
            break
        print(f"[{identifier}][STDERR] {line.strip()}")

def start_instance(contact_data):
    """
    Constructs the command to run the api_business_logic script with the contact's data
    and starts the process.
    """
    command = [
        "python",
        "api_business_logic.py",  # Now the file is in the same directory.
        "--phone", contact_data['phone'],
        "--recipient", contact_data['recipient'],
        "--hour", str(contact_data['hour']),
        "--minute", str(contact_data['minute'])
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
        print(f"Error starting process for {contact_data['recipient']}: {e}")
        sys.exit(1)

def main():
    # Prompt for the number of contacts.
    try:
        num_contacts = int(input("Enter the number of contacts: "))
    except ValueError:
        print("Invalid number entered. Exiting.")
        sys.exit(1)
    
    contact_configs = []
    # Collect details for each contact.
    for i in range(num_contacts):
        print(f"\nContact {i + 1} details:")
        phone = input("  Phone number: ").strip()
        recipient = input("  Recipient name: ").strip()
        try:
            hour = int(input("  Scheduled Hour (24-hour format): ").strip())
            minute = int(input("  Scheduled Minute: ").strip())
        except ValueError:
            print("Invalid input for hour or minute. Exiting.")
            sys.exit(1)
            
        contact_configs.append({
            'phone': phone,
            'recipient': recipient,
            'hour': hour,
            'minute': minute
        })

    processes = []
    threads = []
    
    # For each contact, launch an instance of the messaging process and capture its output.
    for idx, config in enumerate(contact_configs):
        process = start_instance(config)
        processes.append(process)
        identifier = f"Contact {idx + 1} ({config['recipient']})"
        
        # Launch a thread to read the process output.
        thread = threading.Thread(target=stream_reader, args=(process, identifier), daemon=True)
        thread.start()
        threads.append(thread)

    print("\nAll messaging processes launched. Outputs will appear as they are generated.")
    print("Press Ctrl+C to exit and terminate all processes.\n")
    
    # Keep the script running until all processes finish or the user interrupts.
    try:
        for proc in processes:
            proc.wait()
    except KeyboardInterrupt:
        print("\nInterrupt received, terminating all messaging processes...")
        for proc in processes:
            proc.terminate()
            proc.wait()
        print("All processes terminated. Exiting.")

if __name__ == "__main__":
    main()
