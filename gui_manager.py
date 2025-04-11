import sys
import subprocess
import threading
import time
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                            QTextEdit, QScrollArea, QFrame, QDialog, 
                            QLineEdit, QSpinBox, QMessageBox, QFormLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QFontDatabase

class ProcessSignals(QObject):
    """Defines the signals available for communicating with the GUI thread."""
    output = pyqtSignal(str, str)  # (contact_id, output_text)
    finished = pyqtSignal(str)     # contact_id

class ProcessWorker(threading.Thread):
    """Worker thread to handle a subprocess and emit its output."""
    def __init__(self, contact_id, command, signals):
        super().__init__()
        self.contact_id = contact_id
        self.command = command
        self.signals = signals
        self.process = None
        self.daemon = True
        self.stop_event = threading.Event()
        
    def run(self):
        try:
            # Start the process
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read stdout
            for line in iter(self.process.stdout.readline, ''):
                if self.stop_event.is_set():
                    break
                if line:
                    self.signals.output.emit(self.contact_id, f"[STDOUT] {line.strip()}")
            
            # Read stderr
            for line in iter(self.process.stderr.readline, ''):
                if self.stop_event.is_set():
                    break
                if line:
                    self.signals.output.emit(self.contact_id, f"[STDERR] {line.strip()}")
            
            # Process completed
            return_code = self.process.wait()
            if return_code:
                self.signals.output.emit(
                    self.contact_id, 
                    f"Process exited with return code {return_code}"
                )
            
        except Exception as e:
            self.signals.output.emit(self.contact_id, f"Error: {str(e)}")
        finally:
            self.signals.finished.emit(self.contact_id)
    
    def stop(self):
        """Stop the process."""
        self.stop_event.set()
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()

class ContactCard(QFrame):
    """Widget representing a contact card in the GUI."""
    def __init__(self, contact_id, contact_data, parent=None):
        super().__init__(parent)
        self.contact_id = contact_id
        self.contact_data = contact_data
        self.process_worker = None
        self.process_signals = ProcessSignals()
        self.is_running = False
        
        # Connect signals
        self.process_signals.output.connect(self.update_output)
        self.process_signals.finished.connect(self.process_finished)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components of the card."""
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            ContactCard {
                background-color: #ffffff;
                border-radius: 16px;
                border: none;
            }
            QLabel#nameLabel {
                font-weight: 600;
                font-size: 18px;
                color: #1a1a2e;
            }
            QLabel#detailLabel {
                color: #4a4a6a;
                font-size: 13px;
            }
            QLabel#statusRunning {
                color: #10b981;
                font-weight: 500;
            }
            QLabel#statusIdle {
                color: #6b7280;
                font-weight: 500;
            }
            QTextEdit {
                background-color: #f8fafc;
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 13px;
                color: #334155;
            }
            QPushButton {
                background-color: #f1f5f9;
                color: #334155;
                border: none;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
            QPushButton:pressed {
                background-color: #cbd5e1;
            }
            QPushButton:disabled {
                background-color: #e2e8f0;
                color: #94a3b8;
            }
            QPushButton#primaryButton {
                background-color: #3b82f6;
                color: white;
            }
            QPushButton#primaryButton:hover {
                background-color: #2563eb;
            }
            QPushButton#primaryButton:pressed {
                background-color: #1d4ed8;
            }
            QPushButton#dangerButton {
                background-color: #ef4444;
                color: white;
            }
            QPushButton#dangerButton:hover {
                background-color: #dc2626;
            }
            QPushButton#dangerButton:pressed {
                background-color: #b91c1c;
            }
        """)
        
        # Add drop shadow effect
        self.setGraphicsEffect(None)  # Clear any existing effect
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)
        
        # Header with contact name
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        self.name_label = QLabel(self.contact_data['recipient'])
        self.name_label.setObjectName("nameLabel")
        header_layout.addWidget(self.name_label)
        
        self.status_label = QLabel("Idle")
        self.status_label.setObjectName("statusIdle")
        header_layout.addWidget(self.status_label)
        
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        # Contact details
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(4)
        
        phone_label = QLabel(f"📱 {self.contact_data['phone']}")
        phone_label.setObjectName("detailLabel")
        details_layout.addWidget(phone_label)
        
        time_label = QLabel(f"🕒 Scheduled at {self.contact_data['hour']:02d}:{self.contact_data['minute']:02d}")
        time_label.setObjectName("detailLabel")
        details_layout.addWidget(time_label)
        
        main_layout.addWidget(details_widget)
        
        # Output text area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(150)
        self.output_text.setPlaceholderText("Process output will appear here...")
        main_layout.addWidget(self.output_text)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("primaryButton")
        self.start_button.clicked.connect(self.start_process)
        buttons_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("dangerButton")
        self.stop_button.clicked.connect(self.stop_process)
        self.stop_button.setEnabled(False)
        buttons_layout.addWidget(self.stop_button)
        
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_card)
        buttons_layout.addWidget(self.edit_button)
        
        main_layout.addLayout(buttons_layout)
        
    def start_process(self):
        """Start the process for this contact."""
        if self.process_worker and self.process_worker.is_alive():
            return
            
        # Clear previous output
        self.output_text.clear()
        
        # Create and start the process worker
        command = [
            "python",
            "api_business_logic.py",
            "--phone", self.contact_data['phone'],
            "--recipient", self.contact_data['recipient'],
            "--hour", str(self.contact_data['hour']),
            "--minute", str(self.contact_data['minute'])
        ]
        
        self.process_worker = ProcessWorker(self.contact_id, command, self.process_signals)
        self.process_worker.start()
        
        # Update UI
        self.is_running = True
        self.status_label.setText("Running")
        self.status_label.setObjectName("statusRunning")
        self.status_label.setStyleSheet("")  # Force style refresh
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.output_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] Starting process for {self.contact_data['recipient']}...")
        
    def stop_process(self):
        """Stop the process for this contact."""
        if self.process_worker and self.process_worker.is_alive():
            self.output_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] Stopping process...")
            self.process_worker.stop()
            
    def process_finished(self, contact_id):
        """Handle process completion."""
        if contact_id == self.contact_id:
            self.is_running = False
            self.status_label.setText("Idle")
            self.status_label.setObjectName("statusIdle")
            self.status_label.setStyleSheet("")  # Force style refresh
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.output_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] Process finished")
            
    def update_output(self, contact_id, text):
        """Update the output text area with new output."""
        if contact_id == self.contact_id:
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # Format the output with colors based on the type
            if "[STDERR]" in text:
                self.output_text.append(f"<span style='color:#ef4444;'>[{timestamp}] {text}</span>")
            else:
                self.output_text.append(f"<span style='color:#334155;'>[{timestamp}] {text}</span>")
                
            # Auto-scroll to bottom
            scrollbar = self.output_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
    def edit_card(self):
        """Open dialog to edit this card's details."""
        dialog = EditContactDialog(self.contact_data, self.parent())
        if dialog.exec():
            new_data = dialog.get_values()
            self.contact_data = new_data
            self.name_label.setText(self.contact_data['recipient'])
            
            # Update the details display
            layout = self.layout()
            details_widget = layout.itemAt(1).widget()
            details_layout = details_widget.layout()
            
            # Update phone and time labels
            details_layout.itemAt(0).widget().setText(f"📱 {self.contact_data['phone']}")
            details_layout.itemAt(1).widget().setText(
                f"🕒 Scheduled at {self.contact_data['hour']:02d}:{self.contact_data['minute']:02d}")
            
            self.output_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] Contact details updated")

class EditContactDialog(QDialog):
    """Dialog for editing or adding a contact."""
    def __init__(self, contact_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Contact")
        self.setMinimumWidth(400)
        
        if contact_data is None:
            contact_data = {
                'phone': '',
                'recipient': '',
                'hour': 12,
                'minute': 0
            }
        
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 16px;
            }
            QLabel {
                color: #1a1a2e;
                font-size: 14px;
                font-weight: 500;
            }
            QLineEdit, QSpinBox {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                color: #334155;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 1px solid #3b82f6;
            }
            QPushButton {
                background-color: #f1f5f9;
                color: #334155;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
            QPushButton:pressed {
                background-color: #cbd5e1;
            }
            QPushButton#primaryButton {
                background-color: #3b82f6;
                color: white;
            }
            QPushButton#primaryButton:hover {
                background-color: #2563eb;
            }
            QPushButton#primaryButton:pressed {
                background-color: #1d4ed8;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(16)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Phone field
        self.phone_edit = QLineEdit(contact_data['phone'])
        self.phone_edit.setPlaceholderText("Enter phone number")
        form_layout.addRow("Phone Number", self.phone_edit)
        
        # Recipient field
        self.recipient_edit = QLineEdit(contact_data['recipient'])
        self.recipient_edit.setPlaceholderText("Enter recipient name")
        form_layout.addRow("Recipient Name", self.recipient_edit)
        
        # Hour field
        self.hour_edit = QSpinBox()
        self.hour_edit.setRange(0, 23)
        self.hour_edit.setValue(contact_data['hour'])
        form_layout.addRow("Hour (24h)", self.hour_edit)
        
        # Minute field
        self.minute_edit = QSpinBox()
        self.minute_edit.setRange(0, 59)
        self.minute_edit.setValue(contact_data['minute'])
        form_layout.addRow("Minute", self.minute_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        save_button = QPushButton("Save")
        save_button.setObjectName("primaryButton")
        save_button.clicked.connect(self.accept)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)
        
    def get_values(self):
        """Return the values entered in the dialog."""
        return {
            'phone': self.phone_edit.text(),
            'recipient': self.recipient_edit.text(),
            'hour': self.hour_edit.value(),
            'minute': self.minute_edit.value()
        }

class AddContactsDialog(QDialog):
    """Dialog for adding multiple contacts at once."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Contacts")
        self.setMinimumWidth(500)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 16px;
            }
            QLabel {
                color: #1a1a2e;
                font-size: 14px;
                font-weight: 500;
            }
            QLineEdit, QSpinBox {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                color: #334155;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 1px solid #3b82f6;
            }
            QPushButton {
                background-color: #f1f5f9;
                color: #334155;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
            QPushButton:pressed {
                background-color: #cbd5e1;
            }
            QPushButton#primaryButton {
                background-color: #3b82f6;
                color: white;
            }
            QPushButton#primaryButton:hover {
                background-color: #2563eb;
            }
            QPushButton#primaryButton:pressed {
                background-color: #1d4ed8;
            }
            QFrame {
                background-color: #f8fafc;
                border-radius: 12px;
                padding: 4px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Add Multiple Contacts")
        title_label.setStyleSheet("font-size: 18px; font-weight: 600; margin-bottom: 12px;")
        layout.addWidget(title_label)
        
        # Number of contacts
        num_layout = QHBoxLayout()
        num_layout.setSpacing(12)
        num_layout.addWidget(QLabel("Number of contacts:"))
        self.num_contacts_spin = QSpinBox()
        self.num_contacts_spin.setRange(1, 100)
        self.num_contacts_spin.setValue(1)
        self.num_contacts_spin.valueChanged.connect(self.update_contact_forms)
        num_layout.addWidget(self.num_contacts_spin)
        num_layout.addStretch()
        layout.addLayout(num_layout)
        
        # Scroll area for contact forms
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(16)
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        add_button = QPushButton("Add Contacts")
        add_button.setObjectName("primaryButton")
        add_button.clicked.connect(self.accept)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)
        
        # Initialize with one contact form
        self.contact_forms = []
        self.update_contact_forms(1)
        
    def update_contact_forms(self, num_contacts):
        """Update the number of contact forms displayed."""
        # Clear existing forms
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.contact_forms = []
        
        # Add new forms
        for i in range(num_contacts):
            group_box = QFrame()
            group_box.setFrameShape(QFrame.Shape.StyledPanel)
            group_box.setFrameShadow(QFrame.Shadow.Raised)
            
            form_layout = QFormLayout(group_box)
            form_layout.setContentsMargins(16, 16, 16, 16)
            form_layout.setSpacing(12)
            form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
            form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
            
            # Add a label for the contact number
            contact_label = QLabel(f"Contact {i+1}")
            contact_label.setStyleSheet("font-weight: 600; font-size: 16px; color: #1a1a2e;")
            form_layout.addRow(contact_label)
            
            # Phone field
            phone_edit = QLineEdit()
            phone_edit.setPlaceholderText("Enter phone number")
            form_layout.addRow("Phone Number", phone_edit)
            
            # Recipient field
            recipient_edit = QLineEdit()
            recipient_edit.setPlaceholderText("Enter recipient name")
            form_layout.addRow("Recipient Name", recipient_edit)
            
            # Hour field
            hour_edit = QSpinBox()
            hour_edit.setRange(0, 23)
            hour_edit.setValue(12)
            form_layout.addRow("Hour (24h)", hour_edit)
            
            # Minute field
            minute_edit = QSpinBox()
            minute_edit.setRange(0, 59)
            minute_edit.setValue(0)
            form_layout.addRow("Minute", minute_edit)
            
            self.scroll_layout.addWidget(group_box)
            
            # Store the form fields
            self.contact_forms.append({
                'phone': phone_edit,
                'recipient': recipient_edit,
                'hour': hour_edit,
                'minute': minute_edit
            })
        
        # Add a spacer at the end
        self.scroll_layout.addStretch()
        
    def get_values(self):
        """Return the values entered in all contact forms."""
        contacts = []
        for form in self.contact_forms:
            contacts.append({
                'phone': form['phone'].text(),
                'recipient': form['recipient'].text(),
                'hour': form['hour'].value(),
                'minute': form['minute'].value()
            })
        return contacts

class MessagingGUI(QMainWindow):
    """Main application window."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Messaging Manager")
        self.resize(1200, 800)
        self.contacts = {}  # Dictionary to store contact cards
        
        # Set application style
        self.setup_fonts()
        self.setup_ui()
        self.check_required_scripts()
        
    def setup_fonts(self):
        """Set up custom fonts for the application."""
        # Set the application font
        app_font = QFont("Segoe UI", 10)
        QApplication.setFont(app_font)
        
    def setup_ui(self):
        """Set up the main UI components."""
        # Set window style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8fafc;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QWidget#centralWidget {
                background-color: #f8fafc;
            }
            QLabel#headerLabel {
                font-size: 24px;
                font-weight: 600;
                color: #1a1a2e;
            }
            QPushButton {
                background-color: #f1f5f9;
                color: #334155;
                border: none;
                padding: 12px 20px;
                border-radius: 10px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
            QPushButton:pressed {
                background-color: #cbd5e1;
            }
            QPushButton#primaryButton {
                background-color: #3b82f6;
                color: white;
            }
            QPushButton#primaryButton:hover {
                background-color: #2563eb;
            }
            QPushButton#primaryButton:pressed {
                background-color: #1d4ed8;
            }
            QPushButton#dangerButton {
                background-color: #ef4444;
                color: white;
            }
            QPushButton#dangerButton:hover {
                background-color: #dc2626;
            }
            QPushButton#dangerButton:pressed {
                background-color: #b91c1c;
            }
        """)
        
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)
        
        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Messaging Dashboard")
        header_label.setObjectName("headerLabel")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        # Top controls
        top_controls = QHBoxLayout()
        top_controls.setSpacing(12)
        
        self.start_all_button = QPushButton("Start All")
        self.start_all_button.setObjectName("primaryButton")
        self.start_all_button.setMinimumWidth(120)
        self.start_all_button.clicked.connect(self.start_all_processes)
        top_controls.addWidget(self.start_all_button)
        
        self.stop_all_button = QPushButton("Stop All")
        self.stop_all_button.setObjectName("dangerButton")
        self.stop_all_button.setMinimumWidth(120)
        self.stop_all_button.clicked.connect(self.stop_all_processes)
        top_controls.addWidget(self.stop_all_button)
        
        top_controls.addStretch()
        
        self.add_contact_button = QPushButton("Add Contact")
        self.add_contact_button.setMinimumWidth(120)
        self.add_contact_button.clicked.connect(self.add_single_contact)
        top_controls.addWidget(self.add_contact_button)
        
        self.add_multiple_button = QPushButton("Add Multiple")
        self.add_multiple_button.setMinimumWidth(120)
        self.add_multiple_button.clicked.connect(self.add_multiple_contacts)
        top_controls.addWidget(self.add_multiple_button)
        
        main_layout.addLayout(top_controls)
        
        # Contacts grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: transparent;")
        
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(24)
        
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)
        
        # Empty state message
        self.empty_label = QLabel("No contacts added yet. Click 'Add Contact' to get started.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #64748b; font-size: 16px; margin: 48px 0;")
        self.grid_layout.addWidget(self.empty_label, 0, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        
    def check_required_scripts(self):
        """Check if required scripts exist."""
        if not os.path.exists("api_business_logic.py"):
            QMessageBox.warning(
                self, 
                "Warning", 
                "api_business_logic.py not found in the current directory. "
                "This application requires api_business_logic.py to function properly."
            )
            
    def add_contact_card(self, contact_id, contact_data):
        """Add a new contact card to the grid."""
        # Remove empty state message if this is the first contact
        if len(self.contacts) == 0:
            item = self.grid_layout.itemAtPosition(0, 0)
            if item and item.widget() == self.empty_label:
                self.grid_layout.removeWidget(self.empty_label)
                self.empty_label.hide()
        
        # Create the card
        card = ContactCard(contact_id, contact_data, self)
        self.contacts[contact_id] = card
        
        # Add to grid layout
        row, col = divmod(len(self.contacts) - 1, 2)
        self.grid_layout.addWidget(card, row, col)
        
    def add_single_contact(self):
        """Open dialog to add a new contact."""
        dialog = EditContactDialog(parent=self)
        if dialog.exec():
            contact_data = dialog.get_values()
            # Generate a unique ID
            contact_id = str(len(self.contacts) + 1)
            self.add_contact_card(contact_id, contact_data)
            
    def add_multiple_contacts(self):
        """Open dialog to add multiple contacts at once."""
        dialog = AddContactsDialog(parent=self)
        if dialog.exec():
            contacts_data = dialog.get_values()
            for contact_data in contacts_data:
                contact_id = str(len(self.contacts) + 1)
                self.add_contact_card(contact_id, contact_data)
            
    def start_all_processes(self):
        """Start all contact processes."""
        for contact_id, card in self.contacts.items():
            card.start_process()
            
    def stop_all_processes(self):
        """Stop all running processes."""
        for contact_id, card in self.contacts.items():
            card.stop_process()
            
    def closeEvent(self, event):
        """Handle window close event."""
        # Stop all processes before closing
        self.stop_all_processes()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MessagingGUI()
    window.show()
    sys.exit(app.exec())
