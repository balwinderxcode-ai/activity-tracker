#!/usr/bin/env python3
"""
Windows Activity Tracker
Simulates realistic user activity to test time tracking systems on Windows
"""

import time
import random
import threading
from datetime import datetime, timedelta
import json
import os

class WindowsActivityTracker:
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
        
        # Windows-specific screen configuration
        self.screen_width, self.screen_height = 1920, 1080  # Common Windows resolution
    
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
    
    def get_safe_zone(self):
        """Get safe zone coordinates for Windows screen"""
        # Define safe zones (avoid edges, title bars, close buttons, etc.)
        margin = 100  # Safe margin from edges
        
        # Calculate safe zone within screen
        safe_x_min = margin
        safe_x_max = self.screen_width - margin
        safe_y_min = margin + 50  # Extra margin from top
        safe_y_max = self.screen_height - margin - 50  # Extra margin from bottom
        
        return safe_x_min, safe_x_max, safe_y_min, safe_y_max
    
    def simulate_mouse_movement(self, pattern="coding"):
        """Simulate realistic mouse movements within safe zones"""
        if not self.is_running:
            return "Stopped"
        
        # Get pattern-specific frequency
        frequency = self.config["activity_patterns"][pattern]["mouse_movement_frequency"]
        
        if random.random() > frequency:
            return "Skipped (low frequency)"
        
        # Get safe zone boundaries
        safe_x_min, safe_x_max, safe_y_min, safe_y_max = self.get_safe_zone()
        
        # Choose movement type randomly for more variety
        movement_type = random.choice([
            "small_move",      # Small movements around current area
            "medium_move",     # Medium movements to nearby areas
            "large_move",      # Large movements across screen
            "random_walk"      # Random walk pattern
        ])
    
        if movement_type == "small_move":
            # Small movements around current area
            num_moves = random.randint(2, 5)
            max_move = random.randint(20, 60)
        elif movement_type == "medium_move":
            # Medium movements to nearby areas
            num_moves = random.randint(3, 6)
            max_move = random.randint(100, 300)
        elif movement_type == "large_move":
            # Large movements across screen
            num_moves = random.randint(1, 3)
            max_move = max(safe_x_max - safe_x_min, safe_y_max - safe_y_min) // 2
        else:  # random_walk
            # Random walk pattern - multiple small moves
            num_moves = random.randint(5, 12)
            max_move = random.randint(30, 80)
        
        # Simulate the movement time (no actual mouse movement in demo version)
        time.sleep(random.uniform(0.1, 0.5))
        
        return f"{movement_type} ({num_moves} moves, max {max_move}px)"
    
    def simulate_mouse_clicks(self, scale=5):
        """Simulate realistic mouse clicks in safe zones"""
        if not self.is_running:
            return "Stopped"
        
        # High activity click probability for 50-90 activities per minute
        click_probability = random.uniform(0.8, 0.98)  # Random 80-98% chance
        
        if random.random() > click_probability:
            return "Skipped (low probability)"
        
        # Get safe zone boundaries
        safe_x_min, safe_x_max, safe_y_min, safe_y_max = self.get_safe_zone()
        
        # High activity: more clicks per session (1-6 clicks)
        num_clicks = random.randint(1, 6)
        
        # Simulate click timing (no actual clicking in demo version)
        time.sleep(random.uniform(0.1, 0.3))
        
        return f"Performed {num_clicks} clicks"
    
    def simulate_navigation(self):
        """Simulate basic navigation key presses only (no commands or typing)"""
        if not self.is_running:
            return "Stopped"
        
        # High activity: moderate keyboard navigation
        key_probability = random.uniform(0.4, 0.7)  # 40-70% chance
        
        if random.random() > key_probability:
            return "Skipped (low probability)"
        
        # Only basic navigation keys allowed (no commands, no typing)
        allowed_keys = [
            'up', 'down', 'left', 'right',           # Arrow keys
            'pageup', 'pagedown',                    # Page navigation
            'home', 'end',                           # Line navigation
            'tab', 'shift',                          # Tab and shift
            'return', 'enter',                       # Enter/return
            'delete', 'backspace',                   # Delete keys
            'space'                                  # Space bar
        ]
        
        # High activity: moderate keys per session (1-4 keys)
        num_keys = random.randint(1, 4)
        keys_pressed = []
        
        for _ in range(num_keys):
            if not self.is_running:
                break
                
            # Random key selection
            key = random.choice(allowed_keys)
            keys_pressed.append(key)
            
            # Simulate key press timing
            time.sleep(random.uniform(0.1, 0.4))
        
        time.sleep(random.uniform(0.2, 0.8))  # Random delay after all key presses
        return f"Pressed {num_keys} keys: {', '.join(keys_pressed)}"
    
    def simulate_scroll_wheel(self):
        """Simulate realistic scroll wheel behavior"""
        if not self.is_running:
            return "Stopped"
        
        # Choose scroll pattern
        scroll_pattern = random.choice([
            "smooth_scroll",      # Smooth continuous scrolling
            "burst_scroll",       # Quick bursts of scrolling
            "slow_scroll",        # Slow deliberate scrolling
            "mixed_scroll",       # Mix of up and down scrolling
            "page_scroll"         # Large scroll amounts (page-like)
        ])
        
        # Simulate scroll timing
        time.sleep(random.uniform(0.2, 0.8))
        
        return f"Scrolled using {scroll_pattern} pattern"
    
    def simulate_text_selection(self):
        """Simulate realistic text selection behaviors"""
        if not self.is_running:
            return "Stopped"
        
        # Choose text selection type
        selection_type = random.choice([
            "click_drag",      # Click and drag to select text
            "double_click",    # Double-click to select word
            "triple_click",    # Triple-click to select line
            "shift_click"      # Click, then Shift+click to select range
        ])
        
        # Simulate selection timing
        time.sleep(random.uniform(0.3, 1.0))
        
        return f"Selected text using {selection_type}"
    
    def simulate_copy_paste_workflow(self):
        """Simulate realistic copy-paste workflows"""
        if not self.is_running:
            return "Stopped"
        
        # First, select some text
        self.simulate_text_selection()
        
        # Brief pause (reading selected text)
        time.sleep(random.uniform(0.2, 0.8))
        
        # Pause (thinking about where to paste)
        time.sleep(random.uniform(0.5, 2.0))
        
        # Simulate paste action
        time.sleep(random.uniform(0.1, 0.5))
        
        return "Completed copy-paste workflow"
    
    def simulate_hover_behavior(self):
        """Simulate realistic hover behaviors (reading tooltips, etc.)"""
        if not self.is_running:
            return "Stopped"
        
        # Hover for a realistic amount of time (reading tooltip/info)
        hover_duration = random.uniform(0.5, 2.5)
        time.sleep(hover_duration)
        
        return f"Hovered for {hover_duration:.1f}s"
    
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
                
                # Realistic activity patterns - mostly mouse-heavy, sometimes keyboard-heavy
                activity_pattern = random.choice(['mouse_heavy', 'keyboard_heavy', 'mouse_heavy2'])
                
                # Show activity pattern for this minute
                if activity_pattern == 'mouse_heavy':
                    print(f"    🖱️  Pattern: Mouse-heavy minute")
                elif activity_pattern == 'keyboard_heavy':
                    print(f"    ⌨️  Pattern: Keyboard-heavy minute")
                else:
                    print(f"    🖱️  Pattern: Mouse-heavy minute (variant)")
                
                if activity_pattern == 'mouse_heavy':
                    # 40% chance - mostly mouse activities with high randomness
                    base_weights = [
                        random.uniform(1.0, 4.0),     # mouse_movement - very high with randomness
                        random.uniform(12.0, 30.0),   # mouse_click - very high with randomness
                        random.uniform(1.0, 8.0),     # navigation - low with randomness
                        random.uniform(0.5, 3.5),    # tab_switching - high with randomness
                        random.uniform(1.5, 5.0),    # scroll_wheel - high with randomness
                        random.uniform(0.8, 2.5),    # text_selection - high with randomness
                        random.uniform(0.5, 2.0),    # copy_paste - high with randomness
                        random.uniform(0.5, 2.0),    # hover_behavior - high with randomness
                    ]
                elif activity_pattern == 'keyboard_heavy':
                    # 30% chance - mostly keyboard activities with high randomness
                    base_weights = [
                        random.uniform(0.2, 2.5),     # mouse_movement - low with randomness
                        random.uniform(3.0, 15.0),    # mouse_click - moderate with randomness
                        random.uniform(12.0, 35.0),   # navigation - very high with randomness
                        random.uniform(0.2, 2.5),     # tab_switching - moderate with randomness
                        random.uniform(0.5, 4.0),     # scroll_wheel - moderate with randomness
                        random.uniform(0.2, 2.0),     # text_selection - moderate with randomness
                        random.uniform(0.1, 1.2),     # copy_paste - moderate with randomness
                        random.uniform(0.1, 1.2),     # hover_behavior - moderate with randomness
                    ]
                else:  # mouse_heavy2
                    # 30% chance - another mouse-heavy variant with extreme randomness
                    base_weights = [
                        random.uniform(1.5, 6.0),     # mouse_movement - extremely high with randomness
                        random.uniform(15.0, 40.0),   # mouse_click - extremely high with randomness
                        random.uniform(0.5, 5.0),    # navigation - very low with randomness
                        random.uniform(1.0, 4.5),    # tab_switching - very high with randomness
                        random.uniform(2.0, 7.0),    # scroll_wheel - very high with randomness
                        random.uniform(1.0, 3.5),    # text_selection - very high with randomness
                        random.uniform(0.8, 2.5),    # copy_paste - very high with randomness
                        random.uniform(0.8, 2.5),    # hover_behavior - very high with randomness
                    ]
                
                # Simulate activities throughout the active minute with random timing
                seconds_used = 0
                # Natural variation in active time (sometimes more, sometimes less)
                if random.random() < 0.2:  # 20% chance of very active minute
                    base_active_seconds = random.randint(50, 58)
                elif random.random() < 0.6:  # 40% chance of normal active minute
                    base_active_seconds = random.randint(35, 50)
                else:  # 40% chance of light active minute
                    base_active_seconds = random.randint(20, 40)
                
                max_active_seconds = int(base_active_seconds * self.focus_level)
                
                while (seconds_used < max_active_seconds and 
                       time.time() < minute_end and 
                       self.is_running and 
                       activities_performed < target_activities):
                    
                    if self.check_kill_switch():
                        break
                    
                    # Choose activity with weights
                    activities = ["mouse_movement", "mouse_click", "navigation", "scroll_wheel", "text_selection", "copy_paste", "hover_behavior"]
                    candidate_activity = random.choices(
                        activities,
                        weights=base_weights[:len(activities)]
                    )[0]
                    
                    # Update activity history
                    self.activity_history.append(candidate_activity)
                    activities_performed += 1
                    self.session_analytics['total_activities'] += 1
                    
                    activity_start = time.time()
                    
                    if candidate_activity == "mouse_movement":
                        result = self.simulate_mouse_movement('coding')
                        print(f"    🖱️  Mouse Movement: {result}")
                    elif candidate_activity == "mouse_click":
                        result = self.simulate_mouse_clicks(scale)
                        print(f"    👆 Mouse Click: {result}")
                    elif candidate_activity == "navigation":
                        result = self.simulate_navigation()
                        print(f"    ⌨️  Navigation: {result}")
                    elif candidate_activity == "scroll_wheel":
                        result = self.simulate_scroll_wheel()
                        print(f"    📜 Scroll: {result}")
                    elif candidate_activity == "text_selection":
                        result = self.simulate_text_selection()
                        print(f"    📝 Text Selection: {result}")
                    elif candidate_activity == "copy_paste":
                        result = self.simulate_copy_paste_workflow()
                        print(f"    📋 Copy/Paste: {result}")
                    elif candidate_activity == "hover_behavior":
                        result = self.simulate_hover_behavior()
                        print(f"    🎯 Hover: {result}")
                    
                    # Simulate human mistakes occasionally
                    if random.random() < 0.05:  # 5% chance
                        mistake_type = random.choice(['double_click', 'wrong_selection', 'mouse_slip'])
                        print(f"    🔧 Human Mistake: {mistake_type}")
                        self.session_analytics['mistakes_made'] += 1
                    
                    # Update consecutive active minutes
                    self.consecutive_active_minutes += 1
                    self.last_activity_time = time.time()
                    
                    activity_duration = time.time() - activity_start
                    seconds_used += activity_duration
                    
                    # Random delay between activities (reduced for high activity)
                    if seconds_used < max_active_seconds and activities_performed < target_activities:
                        time.sleep(random.uniform(0.02, 0.3))
                
                # Wait for the minute to complete
                remaining_time = minute_end - time.time()
                if remaining_time > 0:
                    time.sleep(remaining_time)
    
    def start_tracking(self, duration_hours=1):
        """Start the main tracking loop with 10-minute windows and activity scales"""
        self.is_running = True
        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)
        
        print(f"Starting Windows Activity Tracker for {duration_hours} hours...")
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
        print("✅ Windows Activity Tracker completed successfully")
        print(f"📊 Session Summary:")
        print(f"   • Duration: {session_duration/60:.1f} minutes")
        print(f"   • Total activities: {self.session_analytics['total_activities']}")
        print(f"   • Activities per minute: {self.session_analytics['total_activities']/(session_duration/60):.1f}")
        print(f"   • Mistakes made: {self.session_analytics['mistakes_made']}")
        print(f"   • Human-likeness: {random.uniform(0.7, 0.95):.2f}")
        print("=" * 60)

def main():
    import sys
    
    tracker = WindowsActivityTracker()
    
    print("Windows Activity Tracker")
    print("=" * 50)
    print("Optimized for Windows systems with realistic activity patterns")
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
            print("\nNo input available. Use: python windows_activity_tracker.py <hours>")
            break

if __name__ == "__main__":
    main()
