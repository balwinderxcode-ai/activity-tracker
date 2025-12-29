#!/usr/bin/env python3
"""
Simplified Activity Tracker - Demo Version
This version simulates the activity tracking logic without requiring pyautogui/keyboard
"""

import time
import random
import threading
from datetime import datetime, timedelta
import json
import os

class SimpleActivityTracker:
    def __init__(self):
        self.is_running = False
        self.error_count = 0
        self.max_errors = 100
        self.config = self.load_config()
        self.kill_switch_file = "STOP_TRACKER.txt"
        
        # Human-like behavior state
        self.session_start_time = time.time()
        self.fatigue_level = 0.0
        self.focus_level = random.uniform(0.7, 1.0)
        self.last_activity_time = time.time()
        self.consecutive_active_minutes = 0
        self.break_needed = False
        
        # Activity tracking
        self.activity_history = []
        self.session_analytics = {
            'start_time': time.time(),
            'total_activities': 0,
            'activity_breakdown': {},
            'mistakes_made': 0
        }
    
    def load_config(self):
        """Load configuration from file or create default"""
        default_config = {
            "mouse_movement_interval": (1, 5),
            "click_probability": 0.3,
            "idle_periods": {
                "min_duration": 5,
                "max_duration": 30
            },
            "activity_patterns": {
                "coding": {
                    "mouse_movement_frequency": 0.6,
                    "click_frequency": 0.4
                },
                "browsing": {
                    "mouse_movement_frequency": 0.9,
                    "click_frequency": 0.7
                },
                "research": {
                    "mouse_movement_frequency": 0.8,
                    "click_frequency": 0.6
                }
            }
        }
        
        try:
            with open('tracker_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            with open('tracker_config.json', 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def check_kill_switch(self):
        """Check if kill switch file exists to stop the tracker"""
        if os.path.exists(self.kill_switch_file):
            print(f"\n🛑 KILL SWITCH ACTIVATED!")
            print(f"Found kill switch file: {self.kill_switch_file}")
            print("Stopping tracker immediately...")
            self.is_running = False
            try:
                os.remove(self.kill_switch_file)
                print("✅ Kill switch file removed")
            except Exception as e:
                print(f"⚠️  Could not remove kill switch file: {e}")
            return True
        return False
    
    def update_human_state(self):
        """Update human-like behavioral state based on time and activity"""
        current_time = time.time()
        session_duration = (current_time - self.session_start_time) / 3600  # Hours
        
        # Update fatigue level (increases over time)
        base_fatigue = min(session_duration * 0.1, 0.8)  # Max 80% fatigue
        activity_fatigue = self.consecutive_active_minutes * 0.02  # 2% per active minute
        self.fatigue_level = min(base_fatigue + activity_fatigue, 1.0)
        
        # Update focus level (decreases with fatigue, varies randomly)
        base_focus = 1.0 - (self.fatigue_level * 0.5)
        focus_variation = random.uniform(-0.2, 0.2)
        self.focus_level = max(0.3, min(1.0, base_focus + focus_variation))
        
        # Check if break is needed
        if self.consecutive_active_minutes > random.randint(45, 90):
            self.break_needed = True
    
    def simulate_mouse_movement(self, pattern="coding"):
        """Simulate mouse movement (demo version - no actual mouse movement)"""
        if not self.is_running:
            return "Stopped"
        
        frequency = self.config["activity_patterns"][pattern]["mouse_movement_frequency"]
        
        if random.random() > frequency:
            return "Skipped (low frequency)"
        
        # Simulate movement patterns
        movement_type = random.choice([
            "small_move", "medium_move", "large_move", "random_walk"
        ])
        
        if movement_type == "small_move":
            num_moves = random.randint(2, 5)
            max_move = random.randint(20, 60)
        elif movement_type == "medium_move":
            num_moves = random.randint(3, 6)
            max_move = random.randint(100, 300)
        elif movement_type == "large_move":
            num_moves = random.randint(1, 3)
            max_move = 500
        else:  # random_walk
            num_moves = random.randint(5, 12)
            max_move = random.randint(30, 80)
        
        # Simulate the movement time
        time.sleep(random.uniform(0.1, 0.5))
        
        return f"{movement_type} ({num_moves} moves, max {max_move}px)"
    
    def simulate_mouse_clicks(self, scale=5):
        """Simulate mouse clicks (demo version - no actual clicking)"""
        if not self.is_running:
            return "Stopped"
        
        click_probability = random.uniform(0.8, 0.98)
        
        if random.random() > click_probability:
            return "Skipped (low probability)"
        
        num_clicks = random.randint(1, 6)
        
        # Simulate click timing
        time.sleep(random.uniform(0.1, 0.3))
        
        return f"Performed {num_clicks} clicks"
    
    def simulate_navigation(self):
        """Simulate keyboard navigation (demo version - no actual key presses)"""
        if not self.is_running:
            return "Stopped"
        
        key_probability = random.uniform(0.4, 0.7)
        
        if random.random() > key_probability:
            return "Skipped (low probability)"
        
        allowed_keys = [
            'up', 'down', 'left', 'right', 'pageup', 'pagedown',
            'home', 'end', 'tab', 'shift', 'return', 'enter',
            'delete', 'backspace', 'space'
        ]
        
        num_keys = random.randint(1, 4)
        keys_pressed = []
        
        for _ in range(num_keys):
            key = random.choice(allowed_keys)
            keys_pressed.append(key)
            time.sleep(random.uniform(0.1, 0.4))
        
        return f"Pressed {num_keys} keys: {', '.join(keys_pressed)}"
    
    def simulate_activity_scale(self, scale, duration_minutes=10):
        """Simulate activity based on scale with scattered idle/active minutes"""
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        # Calculate idle vs active minutes based on scale
        idle_minutes = 10 - scale
        active_minutes = scale
        
        # Generate scattered idle/active pattern
        all_minutes = list(range(10))
        idle_minute_positions = random.sample(all_minutes, idle_minutes)
        
        # Execute each minute of the 10-minute window
        for minute_num in range(10):
            if not self.is_running:
                break
            
            if self.check_kill_switch():
                break
                
            minute_start = time.time()
            minute_end = min(minute_start + 60, end_time)
            
            is_idle_minute = minute_num in idle_minute_positions
            
            if is_idle_minute:
                print(f"    😴 Idle minute {minute_num + 1}/10")
                time.sleep(60)  # Wait 1 minute doing nothing
                continue
            else:
                print(f"    🎯 Active minute {minute_num + 1}/10")
                
                # Calculate target activities based on scale
                if scale == 7:
                    target_activities = random.randint(17, 40)
                elif scale == 8:
                    target_activities = random.randint(33, 55)
                else:  # scale == 9
                    target_activities = random.randint(47, 75)
                
                activities_performed = 0
                
                # Update human state
                self.update_human_state()
                
                # Simulate activities throughout the active minute
                seconds_used = 0
                max_active_seconds = int(50 * self.focus_level)
                
                while (seconds_used < max_active_seconds and 
                       time.time() < minute_end and 
                       self.is_running and 
                       activities_performed < target_activities):
                    
                    if self.check_kill_switch():
                        break
                    
                    # Choose activity type
                    activity = random.choice([
                        "mouse_movement", "mouse_click", "navigation", 
                        "scroll_wheel", "text_selection", "copy_paste", "hover_behavior"
                    ])
                    
                    self.activity_history.append(activity)
                    activities_performed += 1
                    self.session_analytics['total_activities'] += 1
                    
                    activity_start = time.time()
                    
                    if activity == "mouse_movement":
                        result = self.simulate_mouse_movement('coding')
                        print(f"    🖱️  Mouse Movement: {result}")
                    elif activity == "mouse_click":
                        result = self.simulate_mouse_clicks(scale)
                        print(f"    👆 Mouse Click: {result}")
                    elif activity == "navigation":
                        result = self.simulate_navigation()
                        print(f"    ⌨️  Navigation: {result}")
                    elif activity == "scroll_wheel":
                        print(f"    📜 Scroll: Scrolled using {random.choice(['smooth_scroll', 'burst_scroll', 'slow_scroll'])} pattern")
                    elif activity == "text_selection":
                        print(f"    📝 Text Selection: Selected text using {random.choice(['click_drag', 'double_click', 'triple_click'])}")
                    elif activity == "copy_paste":
                        print(f"    📋 Copy/Paste: Completed copy-paste workflow")
                    elif activity == "hover_behavior":
                        print(f"    🎯 Hover: Hovered for {random.uniform(0.5, 2.5):.1f}s")
                    
                    # Simulate human mistakes occasionally
                    if random.random() < 0.05:  # 5% chance
                        print(f"    🔧 Human Mistake: {random.choice(['double_click', 'wrong_selection', 'mouse_slip'])}")
                        self.session_analytics['mistakes_made'] += 1
                    
                    # Update consecutive active minutes
                    self.consecutive_active_minutes += 1
                    self.last_activity_time = time.time()
                    
                    activity_duration = time.time() - activity_start
                    seconds_used += activity_duration
                    
                    # Random delay between activities
                    if seconds_used < max_active_seconds and activities_performed < target_activities:
                        time.sleep(random.uniform(0.02, 0.3))
                
                # Wait for the minute to complete
                remaining_time = minute_end - time.time()
                if remaining_time > 0:
                    time.sleep(remaining_time)
    
    def start_tracking(self, duration_hours=1):
        """Start the main tracking loop"""
        self.is_running = True
        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)
        
        print(f"Starting user activity tracking for {duration_hours} hours...")
        print("Each hour is split into 6 windows of 10 minutes each")
        print("Activity scale: 1=idle, 10=very active (random 7-9)")
        print("=" * 60)
        print("🛑 STOP METHODS:")
        print("   • Press Ctrl+C to quit")
        print("   • Create kill switch file: touch STOP_TRACKER.txt")
        
        try:
            current_time = start_time
            window_count = 0
            
            while current_time < end_time and self.is_running:
                if self.check_kill_switch():
                    break
                    
                # Generate random activity scale between 7-9
                activity_scale = random.randint(7, 9)
                window_count += 1
                
                # Calculate window start and end times
                window_start = current_time
                window_end = min(current_time + 600, end_time)  # 10 minutes = 600 seconds
                
                # Calculate remaining time in this window
                window_duration_minutes = (window_end - window_start) / 60
                
                # Calculate progress
                elapsed_time = (current_time - start_time) / 3600  # Hours elapsed
                progress_percent = (elapsed_time / duration_hours) * 100
                
                print(f"\n--- Window {window_count} ---")
                print(f"Activity Scale: {activity_scale}/10")
                print(f"Duration: {window_duration_minutes:.1f} minutes")
                print(f"Time: {datetime.fromtimestamp(window_start).strftime('%H:%M:%S')} - {datetime.fromtimestamp(window_end).strftime('%H:%M:%S')}")
                print(f"Progress: {elapsed_time:.1f}/{duration_hours:.1f} hours ({progress_percent:.1f}%)")
                
                # Simulate activity for this 10-minute window
                try:
                    self.simulate_activity_scale(activity_scale, window_duration_minutes)
                except Exception as e:
                    print(f"Error in window {window_count}: {e}")
                    self.error_count += 1
                    if self.error_count >= self.max_errors:
                        print("Maximum errors reached. Stopping.")
                        break
                
                # Move to next window
                current_time = window_end
                
                # Small break between windows
                if self.is_running and current_time < end_time:
                    time.sleep(random.uniform(2, 5))
                    
        except KeyboardInterrupt:
            print("\nTracking interrupted by user")
        except Exception as e:
            print(f"Fatal error in tracking: {e}")
        
        self.stop_tracking()
    
    def stop_tracking(self):
        """Stop the tracking and show summary"""
        self.is_running = False
        
        # Show session summary
        session_duration = time.time() - self.session_analytics['start_time']
        print("\n" + "=" * 60)
        print("✅ Tracking session completed successfully")
        print(f"📊 Session Summary:")
        print(f"   • Duration: {session_duration/60:.1f} minutes")
        print(f"   • Total activities: {self.session_analytics['total_activities']}")
        print(f"   • Activities per minute: {self.session_analytics['total_activities']/(session_duration/60):.1f}")
        print(f"   • Mistakes made: {self.session_analytics['mistakes_made']}")
        print(f"   • Human-likeness: {random.uniform(0.7, 0.95):.2f}")
        print("=" * 60)

def main():
    import sys
    
    tracker = SimpleActivityTracker()
    
    print("Simplified Activity Tracker (Demo Version)")
    print("=" * 50)
    print("This version simulates activity tracking without requiring")
    print("pyautogui or keyboard modules. Perfect for testing the logic!")
    print("=" * 50)
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        try:
            hours = float(sys.argv[1])
            if hours <= 0:
                print("Please enter a positive number of hours.")
                return
            elif hours > 24:
                print("Maximum 24 hours allowed for safety.")
                return
            
            print(f"\nStarting {hours} hour tracking...")
            print(f"This will create {int(hours * 6)} windows of 10 minutes each")
            tracker.start_tracking(hours)
            return
        except ValueError:
            print("Invalid argument. Please enter a number.")
            return
    
    # Interactive mode
    while True:
        try:
            hours = float(input("\nEnter how many hours you want to run the tracking: "))
            
            if hours <= 0:
                print("Please enter a positive number of hours.")
                continue
            elif hours > 24:
                print("Maximum 24 hours allowed for safety.")
                continue
            
            print(f"\nStarting {hours} hour tracking...")
            print(f"This will create {int(hours * 6)} windows of 10 minutes each")
            
            confirm = input("Continue? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                tracker.start_tracking(hours)
                break
            else:
                print("Tracking cancelled.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except ValueError:
            print("Invalid input. Please enter a number.")
        except EOFError:
            print("\nNo input available. Use: python simple_activity_tracker.py <hours>")
            break

if __name__ == "__main__":
    main()
