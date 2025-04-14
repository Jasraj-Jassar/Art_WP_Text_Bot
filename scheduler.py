import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import os
from collections import defaultdict

class MessageScheduler:
    def __init__(self, schedule_file: str = "message_schedules.json"):
        self.schedule_file = schedule_file
        self.logger = logging.getLogger(__name__)
        self.schedules = self._load_schedules()
        self._build_time_index()
        
    def _load_schedules(self) -> Dict:
        """Load schedules from JSON file"""
        if os.path.exists(self.schedule_file):
            try:
                with open(self.schedule_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                self.logger.error("Error decoding schedule file. Starting with empty schedules.")
                return {}
        return {}
        
    def _save_schedules(self) -> None:
        """Save schedules to JSON file"""
        try:
            with open(self.schedule_file, 'w') as f:
                json.dump(self.schedules, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving schedules: {e}")
            
    def _build_time_index(self) -> None:
        """Build an index of schedules by time and weekday for faster lookups"""
        self.time_index = defaultdict(lambda: defaultdict(list))
        for schedule_id, schedule in self.schedules.items():
            for weekday in schedule['weekdays']:
                time_key = (schedule['hour'], schedule['minute'])
                self.time_index[weekday][time_key].append(schedule_id)
                
    def add_schedule(self, 
                    schedule_id: str,
                    phone: str,
                    recipient: str,
                    hour: int,
                    minute: int,
                    weekdays: List[str]) -> None:
        """
        Add a new message schedule.
        
        Args:
            schedule_id (str): Unique identifier for the schedule
            phone (str): Recipient's phone number
            recipient (str): Recipient's name
            hour (int): Hour in 24-hour format
            minute (int): Minute
            weekdays (List[str]): List of weekdays (e.g., ['monday', 'wednesday', 'friday'])
        """
        # Validate weekdays
        valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in weekdays:
            if day.lower() not in valid_days:
                raise ValueError(f"Invalid weekday: {day}")
                
        schedule = {
            'phone': phone,
            'recipient': recipient,
            'hour': hour,
            'minute': minute,
            'weekdays': [day.lower() for day in weekdays]
        }
        
        # Remove old schedule if it exists
        if schedule_id in self.schedules:
            self.remove_schedule(schedule_id)
            
        # Add new schedule
        self.schedules[schedule_id] = schedule
        self._save_schedules()
        
        # Update time index
        for weekday in schedule['weekdays']:
            time_key = (hour, minute)
            self.time_index[weekday][time_key].append(schedule_id)
            
        self.logger.info(f"Added schedule {schedule_id}: {schedule}")
        
    def remove_schedule(self, schedule_id: str) -> None:
        """Remove a schedule"""
        if schedule_id in self.schedules:
            schedule = self.schedules[schedule_id]
            # Remove from time index
            for weekday in schedule['weekdays']:
                time_key = (schedule['hour'], schedule['minute'])
                if schedule_id in self.time_index[weekday][time_key]:
                    self.time_index[weekday][time_key].remove(schedule_id)
                    if not self.time_index[weekday][time_key]:
                        del self.time_index[weekday][time_key]
            
            del self.schedules[schedule_id]
            self._save_schedules()
            self.logger.info(f"Removed schedule {schedule_id}")
            
    def get_schedule(self, schedule_id: str) -> Optional[Dict]:
        """Get schedule information"""
        return self.schedules.get(schedule_id)
        
    def get_all_schedules(self) -> Dict:
        """Get all schedules"""
        return self.schedules
        
    def get_schedules_for_time(self, weekday: str, hour: int, minute: int) -> List[str]:
        """Get all schedule IDs that should run at the given time"""
        return self.time_index[weekday][(hour, minute)]

    def get_upcoming_schedules(self, days: int = 7) -> Dict:
        """
        Get all schedules for the next X days.
        
        Args:
            days (int): Number of days to look ahead
            
        Returns:
            Dict: Dictionary with weekdays as keys and lists of schedules as values
        """
        result = defaultdict(list)
        
        # Get the weekdays for the next X days
        today = datetime.now()
        for i in range(days):
            future_date = today + timedelta(days=i)
            weekday = future_date.strftime('%A').lower()
            
            # Find all schedules for this weekday
            for schedule_id, schedule in self.schedules.items():
                if weekday in schedule['weekdays']:
                    # Check if this schedule would run today but has already passed
                    if i == 0:  # Today
                        current_hour = today.hour
                        current_minute = today.minute
                        schedule_time = (schedule['hour'], schedule['minute'])
                        
                        # Skip if already passed today
                        if schedule_time <= (current_hour, current_minute):
                            continue
                    
                    # Add to results with date information
                    schedule_info = schedule.copy()
                    schedule_info['schedule_id'] = schedule_id
                    schedule_info['date'] = future_date.strftime('%Y-%m-%d')
                    result[weekday].append(schedule_info)
        
        return result
        
    def summarize_upcoming_schedules(self) -> str:
        """
        Get a text summary of upcoming schedules.
        
        Returns:
            str: A summary of upcoming schedules
        """
        upcoming = self.get_upcoming_schedules(days=7)
        if not upcoming:
            return "No upcoming schedules in the next 7 days."
            
        summary_parts = []
        for weekday, schedules in upcoming.items():
            for schedule in schedules:
                summary_parts.append(
                    f"{weekday.capitalize()} {schedule['hour']:02d}:{schedule['minute']:02d} - {schedule['recipient']}"
                )
        
        return "; ".join(summary_parts)
        
    def run_pending(self) -> None:
        """Check and run any pending schedules"""
        current_time = datetime.now()
        current_weekday = current_time.strftime('%A').lower()
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        self.logger.debug(f"Checking schedules at {current_time}")
        
        # Get all schedules that should run now
        schedule_ids = self.get_schedules_for_time(current_weekday, current_hour, current_minute)
        
        for schedule_id in schedule_ids:
            if schedule_id in self.schedules:
                self.logger.info(f"Running schedule {schedule_id} at {current_time}")
                yield schedule_id, self.schedules[schedule_id]
                
    def run_continuously(self, interval: int = 1) -> None:
        """
        Run the scheduler continuously.
        
        Args:
            interval (int): Interval in seconds between checks
        """
        self.logger.info("Starting scheduler...")
        last_minute = -1
        
        while True:
            try:
                current_time = datetime.now()
                current_minute = current_time.minute
                
                # Only check for schedules at the start of each minute
                if current_minute != last_minute:
                    # Log the time check
                    if current_minute % 5 == 0:  # Only log every 5 minutes to avoid excessive logging
                        self.logger.debug(f"Time check: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        
                    # Execute pending schedules
                    for schedule_id, schedule in self.run_pending():
                        yield schedule_id, schedule
                        
                    last_minute = current_minute
                    
                time.sleep(interval)
            except KeyboardInterrupt:
                self.logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in scheduler: {e}")
                time.sleep(interval) 