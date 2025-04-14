#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging
import subprocess
import threading
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QDialog, QLineEdit, QTimeEdit, QCheckBox, QTabWidget, QTextEdit,
    QGroupBox, QFormLayout, QSpinBox, QComboBox
)
from PyQt6.QtCore import Qt, QTime, QTimer, pyqtSignal

# Import the message scheduler from manager.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from manager import MessageScheduler

# Constants
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
LOG_LEVELS = {
    "INFO": "blue",
    "SUCCESS": "green",
    "WARNING": "orange",
    "ERROR": "red",
    "DEBUG": "gray"
}

class ConsoleOutput(QTextEdit):
    """Widget to display console-like output."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("font-family: monospace; background-color: #f0f0f0;")
        
    def append_log(self, message, level="INFO"):
        """Append a log message with timestamp and level-based coloring."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = LOG_LEVELS.get(level, "black")
        formatted_msg = f'<span style="color:gray;">[{timestamp}]</span> <span style="color:{color};"><b>[{level}]</b></span> {message}'
        self.append(formatted_msg)
        # Auto-scroll to bottom
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

class ProcessWorker(threading.Thread):
    """Thread for running external processes."""
    
    def __init__(self, command, signals, contact_id=None, contact_data=None):
        super().__init__()
        self.command = command
        self.process = None
        self.signals = signals
        self.contact_id = contact_id
        self.contact_data = contact_data
        self.running = True
        self.daemon = True  # Thread will exit when main program exits
        
    def run(self):
        """Run the process and capture output."""
        try:
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            # Process output line by line
            for line in iter(self.process.stdout.readline, ''):
                if not self.running:
                    break
                # Remove trailing newline
                line = line.rstrip()
                if line:
                    self.signals["output"].emit(line.strip(), "INFO")
            
            # Process has completed
            if self.process.poll() is not None:
                exit_code = self.process.returncode
                if exit_code == 0:
                    self.signals["output"].emit(f"Process completed successfully", "SUCCESS")
                else:
                    self.signals["output"].emit(f"Process exited with code {exit_code}", "ERROR")
                
        except Exception as e:
            self.signals["output"].emit(f"Error running process: {str(e)}", "ERROR")
        finally:
            self.signals["finished"].emit()
            
    def stop(self):
        """Stop the running process."""
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                # Give it a moment to terminate
                time.sleep(0.5)
                # If still running, force kill
                if self.process.poll() is None:
                    self.process.kill()
            except Exception as e:
                print(f"Error stopping process: {e}")
                
class ContactDialog(QDialog):
    """Dialog for adding or editing a contact."""
    
    def __init__(self, schedule=None, parent=None):
        super().__init__(parent)
        self.schedule = schedule
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components."""
        is_edit = self.schedule is not None
        self.setWindowTitle(f"{'Edit' if is_edit else 'Add'} Contact")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Form layout for inputs
        form_layout = QFormLayout()
        
        # Phone number input
        self.phone_input = QLineEdit()
        if is_edit:
            self.phone_input.setText(self.schedule.get('phone', ''))
        form_layout.addRow("Phone Number:", self.phone_input)
        
        # Recipient name input
        self.recipient_input = QLineEdit()
        if is_edit:
            self.recipient_input.setText(self.schedule.get('recipient', ''))
        form_layout.addRow("Recipient Name:", self.recipient_input)
        
        # Time scheduling
        time_layout = QHBoxLayout()
        
        # Hour input
        self.hour_input = QSpinBox()
        self.hour_input.setRange(0, 23)
        if is_edit:
            self.hour_input.setValue(int(self.schedule.get('hour', 9)))
        else:
            self.hour_input.setValue(9)  # Default to 9 AM
        
        # Minute input
        self.minute_input = QSpinBox()
        self.minute_input.setRange(0, 59)
        self.minute_input.setSingleStep(5)
        if is_edit:
            self.minute_input.setValue(int(self.schedule.get('minute', 0)))
        
        time_layout.addWidget(QLabel("Hour:"))
        time_layout.addWidget(self.hour_input)
        time_layout.addWidget(QLabel("Minute:"))
        time_layout.addWidget(self.minute_input)
        form_layout.addRow("Scheduled Time:", time_layout)
        
        # Weekday selection
        weekday_group = QGroupBox("Scheduled Days")
        weekday_layout = QVBoxLayout()
        
        # Weekday checkboxes
        self.weekday_checkboxes = []
        for day in WEEKDAYS:
            checkbox = QCheckBox(day)
            if is_edit and 'weekdays' in self.schedule:
                checkbox.setChecked(day.lower() in self.schedule['weekdays'])
            self.weekday_checkboxes.append(checkbox)
            weekday_layout.addWidget(checkbox)
            
        # Quick selection buttons
        quick_select_layout = QHBoxLayout()
        
        weekdays_btn = QPushButton("Weekdays")
        weekdays_btn.clicked.connect(self.select_weekdays)
        quick_select_layout.addWidget(weekdays_btn)
        
        weekend_btn = QPushButton("Weekend")
        weekend_btn.clicked.connect(self.select_weekend)
        quick_select_layout.addWidget(weekend_btn)
        
        all_days_btn = QPushButton("All Days")
        all_days_btn.clicked.connect(self.select_all_days)
        quick_select_layout.addWidget(all_days_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_selection)
        quick_select_layout.addWidget(clear_btn)
        
        weekday_layout.addLayout(quick_select_layout)
        weekday_group.setLayout(weekday_layout)
        
        # Add everything to the main layout
        layout.addLayout(form_layout)
        layout.addWidget(weekday_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def select_weekdays(self):
        """Select weekdays (Monday-Friday)."""
        for i, checkbox in enumerate(self.weekday_checkboxes):
            checkbox.setChecked(i < 5)  # Monday-Friday are indexes 0-4
            
    def select_weekend(self):
        """Select weekend days (Saturday-Sunday)."""
        for i, checkbox in enumerate(self.weekday_checkboxes):
            checkbox.setChecked(i >= 5)  # Saturday-Sunday are indexes 5-6
            
    def select_all_days(self):
        """Select all days."""
        for checkbox in self.weekday_checkboxes:
            checkbox.setChecked(True)
            
    def clear_selection(self):
        """Clear all day selections."""
        for checkbox in self.weekday_checkboxes:
            checkbox.setChecked(False)
            
    def get_values(self):
        """Get the values from the form."""
        # Get selected weekdays
        weekdays = []
        for i, checkbox in enumerate(self.weekday_checkboxes):
            if checkbox.isChecked():
                weekdays.append(WEEKDAYS[i].lower())
                
        return {
            'phone': self.phone_input.text(),
            'recipient': self.recipient_input.text(),
            'hour': self.hour_input.value(),
            'minute': self.minute_input.value(),
            'weekdays': weekdays
        }

class SchedulerGUI(QMainWindow):
    """Main GUI window for managing message schedules."""
    
    # Define signals for process communication
    output_signal = pyqtSignal(str, str)
    process_finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Initialize the scheduler
        self.scheduler = MessageScheduler()
        
        # Initialize process worker
        self.process_worker = None
        
        # Set up signals
        self.output_signal.connect(self.update_console)
        self.process_finished.connect(self.on_process_finished)
        
        # Set up the UI
        self.init_ui()
        
        # Load existing schedules
        self.load_schedules()
        
        # Set up timer for updating upcoming schedules
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_upcoming_schedules)
        self.update_timer.start(60000)  # Update every minute
        self.update_upcoming_schedules()  # Initial update
        
    def init_ui(self):
        """Initialize the UI components."""
        self.setWindowTitle("Message Scheduler")
        self.setMinimumSize(700, 500)
        
        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tabs
        tabs = QTabWidget()
        
        # Manage tab
        manage_tab = QWidget()
        manage_layout = QVBoxLayout(manage_tab)
        
        # Contacts list
        contacts_group = QGroupBox("Contacts")
        contacts_layout = QVBoxLayout()
        
        self.contact_list = QListWidget()
        contacts_layout.addWidget(self.contact_list)
        
        # Contact buttons
        contact_buttons = QHBoxLayout()
        
        add_btn = QPushButton("Add Contact")
        add_btn.clicked.connect(self.add_contact)
        contact_buttons.addWidget(add_btn)
        
        edit_btn = QPushButton("Edit Contact")
        edit_btn.clicked.connect(self.edit_contact)
        contact_buttons.addWidget(edit_btn)
        
        remove_btn = QPushButton("Remove Contact")
        remove_btn.clicked.connect(self.remove_contact)
        contact_buttons.addWidget(remove_btn)
        
        contacts_layout.addLayout(contact_buttons)
        contacts_group.setLayout(contacts_layout)
        manage_layout.addWidget(contacts_group)
        
        # Upcoming schedules
        upcoming_group = QGroupBox("Upcoming Schedules")
        upcoming_layout = QVBoxLayout()
        
        self.upcoming_text = QTextEdit()
        self.upcoming_text.setReadOnly(True)
        upcoming_layout.addWidget(self.upcoming_text)
        
        upcoming_group.setLayout(upcoming_layout)
        manage_layout.addWidget(upcoming_group)
        
        # Scheduler control
        control_layout = QHBoxLayout()
        
        self.run_btn = QPushButton("Start Scheduler")
        self.run_btn.clicked.connect(self.run_scheduler)
        control_layout.addWidget(self.run_btn)
        
        self.stop_btn = QPushButton("Stop Scheduler")
        self.stop_btn.clicked.connect(self.stop_scheduler)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        manage_layout.addLayout(control_layout)
        
        # Console tab
        console_tab = QWidget()
        console_layout = QVBoxLayout(console_tab)
        
        self.console = ConsoleOutput()
        console_layout.addWidget(self.console)
        
        # Add tabs
        tabs.addTab(manage_tab, "Manage Contacts")
        tabs.addTab(console_tab, "Console Output")
        
        main_layout.addWidget(tabs)
        
        # Add console message about startup
        self.console.append_log("Message Scheduler GUI started", "INFO")
        self.console.append_log("Use the 'Manage Contacts' tab to set up schedules", "INFO")
        self.console.append_log("Use 'Start Scheduler' to begin sending messages", "INFO")
        
    def load_schedules(self):
        """Load existing schedules into the contact list."""
        self.contact_list.clear()
        
        schedules = self.scheduler.get_all_schedules()
        if not schedules:
            self.console.append_log("No schedules found", "INFO")
            return
            
        for schedule_id, schedule in schedules.items():
            item = QListWidgetItem()
            weekdays_str = ", ".join(day.capitalize() for day in schedule.get('weekdays', []))
            item.setText(f"{schedule['recipient']} - {int(schedule['hour']):02d}:{int(schedule['minute']):02d} - {weekdays_str}")
            item.setData(Qt.ItemDataRole.UserRole, schedule_id)
            self.contact_list.addItem(item)
            
        self.console.append_log(f"Loaded {len(schedules)} contact(s)", "INFO")
        
    def update_upcoming_schedules(self):
        """Update the upcoming schedules display."""
        schedules = self.scheduler.get_all_schedules()
        if not schedules:
            self.upcoming_text.setPlainText("No scheduled messages.")
            return
            
        # Get next 24 hours of schedules
        now = datetime.now()
        end_time = now + timedelta(days=1)
        
        # Collect upcoming schedules
        upcoming = []
        for schedule_id, schedule in schedules.items():
            next_run = self._calculate_next_run_time(schedule)
            if next_run and next_run <= end_time:
                upcoming.append((next_run, schedule_id, schedule))
                
        # Sort by next run time
        upcoming.sort(key=lambda x: x[0])
        
        # Format for display
        text = []
        for next_run, schedule_id, schedule in upcoming:
            time_str = next_run.strftime("%a %I:%M %p")
            text.append(f"• {time_str} - {schedule['recipient']}")
            
        if not text:
            text = ["No messages scheduled in the next 24 hours."]
            
        self.upcoming_text.setPlainText("\n".join(text))
        
    def _calculate_next_run_time(self, schedule):
        """Calculate the next time a schedule will run."""
        # Get current time
        now = datetime.now()
        
        # Get weekdays from schedule
        weekdays = schedule.get('weekdays', [])
        if not weekdays:
            return None
        
        # Get time from schedule
        hour = int(schedule.get('hour', 0))
        minute = int(schedule.get('minute', 0))
        
        # Map weekday names to numbers (0=Monday, 6=Sunday)
        weekday_map = {day.lower(): i for i, day in enumerate(WEEKDAYS)}
        weekday_nums = [weekday_map[day] for day in weekdays if day in weekday_map]
        if not weekday_nums:
            return None
        
        # Calculate the next occurrence
        # Start with today
        current_weekday = now.weekday()  # 0=Monday, 6=Sunday
        
        # Check if we can run later today
        if current_weekday in weekday_nums:
            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target_time > now:
                return target_time
            
        # Find the next weekday that matches
        for days_ahead in range(1, 8):  # Look ahead up to a week
            next_day = (current_weekday + days_ahead) % 7
            if next_day in weekday_nums:
                # Calculate the date
                target_date = now + timedelta(days=days_ahead)
                return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
        return None
        
    def ensure_scheduler_stopped(self):
        """Make sure the scheduler is stopped before making changes."""
        if hasattr(self, 'process') and self.process is not None and self.process.poll() is None:
            self.console.append_log("Stopping scheduler to make changes...", "WARNING")
            try:
                self.process.terminate()
                # Give a moment for the process to terminate
                for _ in range(10):  # Wait up to 1 second
                    if self.process.poll() is not None:
                        break
                    time.sleep(0.1)
                    
                # If still running, force kill
                if self.process.poll() is None:
                    self.process.kill()
                    
                self.process = None
                self.run_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
            except Exception as e:
                self.console.append_log(f"Error stopping scheduler: {str(e)}", "ERROR")
                
            self.console.append_log("Scheduler stopped. Making changes...", "SUCCESS")
            return True
        return False
        
    def add_contact(self):
        """Add a new contact."""
        # Stop the scheduler if it's running
        was_running = self.ensure_scheduler_stopped()
        
        dialog = ContactDialog(parent=self)
        if dialog.exec():
            values = dialog.get_values()
            
            # Generate schedule ID
            existing_ids = list(self.scheduler.get_all_schedules().keys())
            if existing_ids:
                # Find the highest contact_X number
                contact_nums = [int(id.split('_')[1]) for id in existing_ids if id.startswith('contact_')]
                next_id = max(contact_nums) + 1 if contact_nums else 1
            else:
                next_id = 1
                
            schedule_id = f"contact_{next_id}"
            
            # Add to scheduler
            self.scheduler.add_schedule(
                schedule_id=schedule_id,
                phone=values['phone'],
                recipient=values['recipient'],
                hour=values['hour'],
                minute=values['minute'],
                weekdays=values['weekdays']
            )
            
            self.console.append_log(f"Added contact: {values['recipient']}", "SUCCESS")
            self.load_schedules()
            self.update_upcoming_schedules()
            
            # Switch back to the manage tab
            self.centralWidget().findChild(QTabWidget).setCurrentIndex(0)
            
            # Restart scheduler if it was running
            if was_running:
                self.console.append_log("Restarting scheduler...", "INFO")
                self.run_scheduler()
            
    def edit_contact(self):
        """Edit selected contact."""
        # Stop the scheduler if it's running
        was_running = self.ensure_scheduler_stopped()
        
        selected_items = self.contact_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a contact to edit.")
            return
            
        item = selected_items[0]
        schedule_id = item.data(Qt.ItemDataRole.UserRole)
        schedule = self.scheduler.get_schedule(schedule_id)
        
        if not schedule:
            QMessageBox.warning(self, "Warning", "Could not find the selected contact.")
            return
            
        dialog = ContactDialog(schedule, parent=self)
        if dialog.exec():
            values = dialog.get_values()
            
            # Update the schedule
            self.scheduler.add_schedule(
                schedule_id=schedule_id,
                phone=values['phone'],
                recipient=values['recipient'],
                hour=values['hour'],
                minute=values['minute'],
                weekdays=values['weekdays']
            )
            
            self.console.append_log(f"Updated contact: {values['recipient']}", "SUCCESS")
            self.load_schedules()
            self.update_upcoming_schedules()
            
            # Switch back to the manage tab
            self.centralWidget().findChild(QTabWidget).setCurrentIndex(0)
            
            # Restart scheduler if it was running
            if was_running:
                self.console.append_log("Restarting scheduler...", "INFO")
                self.run_scheduler()
            
    def remove_contact(self):
        """Remove the selected contact."""
        # Stop the scheduler if it's running
        was_running = self.ensure_scheduler_stopped()
        
        selected_items = self.contact_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a contact to remove.")
            return
            
        item = selected_items[0]
        schedule_id = item.data(Qt.ItemDataRole.UserRole)
        schedule = self.scheduler.get_schedule(schedule_id)
        
        if not schedule:
            QMessageBox.warning(self, "Warning", "Could not find the selected contact.")
            return
            
        confirm = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove {schedule['recipient']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.scheduler.remove_schedule(schedule_id)
            self.console.append_log(f"Removed contact: {schedule['recipient']}", "WARNING")
            self.load_schedules()
            self.update_upcoming_schedules()
            
            # Switch back to the manage tab
            self.centralWidget().findChild(QTabWidget).setCurrentIndex(0)
            
            # Restart scheduler if it was running
            if was_running:
                self.console.append_log("Restarting scheduler...", "INFO")
                self.run_scheduler()
            
    def run_scheduler(self):
        """Run the scheduler process."""
        if self.process_worker and self.process_worker.is_alive():
            self.console.append_log("Scheduler is already running", "WARNING")
            return
            
        # Create and start the process worker
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manager.py")
        
        # The standard "--run" argument shows the menu
        command = [sys.executable, script_path, "--run"]
        
        # Create a subprocess that we can communicate with
        try:
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Start a thread to handle process output
            def read_output():
                for line in iter(self.process.stdout.readline, ''):
                    line = line.rstrip()
                    if line:
                        self.output_signal.emit(line.strip(), "INFO")
                self.process_finished.emit()
            
            threading.Thread(target=read_output, daemon=True).start()
            
            # Wait a moment for the menu to appear, then send "5" to start the scheduler
            time.sleep(0.5)
            self.process.stdin.write("5\n")
            self.process.stdin.flush()
            
            self.run_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            
            # Switch to console tab to show output
            self.centralWidget().findChild(QTabWidget).setCurrentIndex(1)
            self.console.append_log("Started scheduler process", "SUCCESS")
            
        except Exception as e:
            self.console.append_log(f"Error starting scheduler: {str(e)}", "ERROR")
        
    def stop_scheduler(self):
        """Stop the scheduler process."""
        if not hasattr(self, 'process') or self.process is None:
            self.console.append_log("No scheduler process is running", "WARNING")
            return
            
        self.console.append_log("Stopping scheduler...", "WARNING")
        try:
            # Send Ctrl+C signal to terminate the process
            self.process.terminate()
            # Give it a moment to terminate
            time.sleep(0.5)
            # If still running, force kill
            if self.process.poll() is None:
                self.process.kill()
        except Exception as e:
            self.console.append_log(f"Error stopping process: {str(e)}", "ERROR")
            
        self.process = None
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
    def update_console(self, message, level="INFO"):
        """Update the console with a new message."""
        self.console.append_log(message, level)
        
    def on_process_finished(self):
        """Handle process completion."""
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.console.append_log("Scheduler process has stopped", "INFO")
        
    def closeEvent(self, event):
        """Handle window close event."""
        if hasattr(self, 'process') and self.process is not None and self.process.poll() is None:
            confirm = QMessageBox.question(
                self,
                "Confirm Exit",
                "The scheduler is still running. Do you want to stop it and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if confirm == QMessageBox.StandardButton.Yes:
                self.process.terminate()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create and run the app
    app = QApplication(sys.argv)
    gui = SchedulerGUI()
    gui.show()
    sys.exit(app.exec())
