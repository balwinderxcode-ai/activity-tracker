#!/usr/bin/env python3
"""
Visible Activity Tracker
Makes very obvious mouse movements and activities so you can see it working
"""

import time
import random
import threading
from datetime import datetime, timedelta
import json
import os
import sys
import ctypes
from ctypes import wintypes

# Windows API constants
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_ABSOLUTE = 0x8000

# Virtual key codes
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_HOME = 0x24
VK_END = 0x23
VK_PRIOR = 0x21  # Page Up
VK_NEXT = 0x22   # Page Down
VK_TAB = 0x09
VK_RETURN = 0x0D
VK_BACK = 0x08
VK_DELETE = 0x2E
VK_SPACE = 0x20
VK_SHIFT = 0x10
VK_CONTROL = 0x11

class VisibleTracker:
    def __init__(self):
        self.is_running = False
        self.error_count = 0
        self.max_errors = 100
        self.kill_switch_file = "STOP_TRACKER.txt"
        
        # Activity tracking
        self.session_analytics = {
            'start_time': time.time(),
            'total_activities': 0,
            'mistakes_made': 0
        }
        
        # Get screen dimensions
        self.screen_width = ctypes.windll.user32.GetSystemMetrics(0)
        self.screen_height = ctypes.windll.user32.GetSystemMetrics(1)
        print(f"📺 Screen detected: {self.screen_width}x{self.screen_height}")
        
        # Load Windows API functions
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        
        print("✅ VISIBLE Activity Tracker enabled")
        print("🎯 This will make VERY OBVIOUS movements and activities!")
        print("⚠️  WARNING: This will actually move your mouse and click!")
        print("⚠️  Make sure no important work is open!")
    
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
    
    def move_mouse_to(self, x, y):
        """Move mouse to absolute position using Windows API"""
        try:
            # Convert to absolute coordinates (0-65535 range)
            abs_x = int(x * 65535 / self.screen_width)
            abs_y = int(y * 65535 / self.screen_height)
            
            # Move mouse
            self.user32.mouse_event(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, abs_x, abs_y, 0, 0)
            return True
        except Exception as e:
            print(f"Error moving mouse: {e}")
            return False
    
    def click_mouse(self, button='left'):
        """Click mouse button using Windows API"""
        try:
            if button == 'left':
                # Left mouse down
                self.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(random.uniform(0.01, 0.05))
                # Left mouse up
                self.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            elif button == 'right':
                # Right mouse down
                self.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                time.sleep(random.uniform(0.01, 0.05))
                # Right mouse up
                self.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            return True
        except Exception as e:
            print(f"Error clicking mouse: {e}")
            return False
    
    def double_click_mouse(self):
        """Double click using Windows API"""
        try:
            # First click
            self.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(random.uniform(0.01, 0.05))
            self.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            
            # Small delay
            time.sleep(random.uniform(0.05, 0.15))
            
            # Second click
            self.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(random.uniform(0.01, 0.05))
            self.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            return True
        except Exception as e:
            print(f"Error double clicking: {e}")
            return False
    
    def scroll_wheel(self, direction, amount=3):
        """Scroll mouse wheel using Windows API"""
        try:
            wheel_delta = direction * amount * 120  # 120 is the standard wheel delta
            self.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, wheel_delta, 0)
            return True
        except Exception as e:
            print(f"Error scrolling: {e}")
            return False
    
    def press_key(self, vk_code):
        """Press a key using Windows API"""
        try:
            # Key down
            self.user32.keybd_event(vk_code, 0, 0, 0)
            time.sleep(random.uniform(0.01, 0.05))
            # Key up
            self.user32.keybd_event(vk_code, 0, 2, 0)  # 2 = KEYEVENTF_KEYUP
            return True
        except Exception as e:
            print(f"Error pressing key: {e}")
            return False
    
    def big_mouse_movement(self):
        """Make a very obvious mouse movement across the screen"""
        if not self.is_running:
            return "Stopped"
        
        print("    🖱️  BIG Mouse Movement: Moving across screen...")
        
        # Get safe zone (avoid edges)
        margin = 100
        safe_x_min = margin
        safe_x_max = self.screen_width - margin
        safe_y_min = margin + 50
        safe_y_max = self.screen_height - margin - 50
        
        # Start from one corner
        start_x = random.choice([safe_x_min, safe_x_max])
        start_y = random.choice([safe_y_min, safe_y_max])
        
        # End at opposite corner
        end_x = safe_x_max if start_x == safe_x_min else safe_x_min
        end_y = safe_y_max if start_y == safe_y_min else safe_y_min
        
        # Move to start position
        self.move_mouse_to(start_x, start_y)
        time.sleep(0.5)
        
        # Move to end position with visible steps
        steps = 20
        for i in range(steps):
            if not self.is_running:
                break
            progress = i / steps
            x = int(start_x + (end_x - start_x) * progress)
            y = int(start_y + (end_y - start_y) * progress)
            self.move_mouse_to(x, y)
            time.sleep(0.1)  # Slow enough to see
        
        time.sleep(0.5)
        return f"Big movement from ({start_x},{start_y}) to ({end_x},{end_y})"
    
    def obvious_clicks(self):
        """Make very obvious mouse clicks"""
        if not self.is_running:
            return "Stopped"
        
        print("    👆 OBVIOUS Clicks: Clicking around screen...")
        
        # Get safe zone
        margin = 100
        safe_x_min = margin
        safe_x_max = self.screen_width - margin
        safe_y_min = margin + 50
        safe_y_max = self.screen_height - margin - 50
        
        num_clicks = random.randint(3, 8)
        
        for i in range(num_clicks):
            if not self.is_running:
                break
            
            # Move to random position
            x = random.randint(safe_x_min, safe_x_max)
            y = random.randint(safe_y_min, safe_y_max)
            
            print(f"    👆 Click {i+1}/{num_clicks} at ({x},{y})")
            self.move_mouse_to(x, y)
            time.sleep(0.3)
            
            # Click
            self.click_mouse('left')
            time.sleep(0.2)
            
            # Sometimes double click
            if random.random() < 0.3:
                print(f"    👆 Double click at ({x},{y})")
                self.double_click_mouse()
                time.sleep(0.2)
        
        return f"Performed {num_clicks} obvious clicks"
    
    def obvious_scrolling(self):
        """Make very obvious scrolling"""
        if not self.is_running:
            return "Stopped"
        
        print("    📜 OBVIOUS Scrolling: Scrolling up and down...")
        
        # Move to center of screen
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        self.move_mouse_to(center_x, center_y)
        time.sleep(0.5)
        
        # Scroll up and down multiple times
        scroll_amount = random.randint(5, 15)
        for i in range(scroll_amount):
            if not self.is_running:
                break
            
            direction = 1 if i % 2 == 0 else -1
            print(f"    📜 Scroll {i+1}/{scroll_amount} {'up' if direction > 0 else 'down'}")
            self.scroll_wheel(direction, random.randint(3, 8))
            time.sleep(0.3)
        
        return f"Scrolled {scroll_amount} times"
    
    def obvious_keyboard(self):
        """Make very obvious keyboard activity"""
        if not self.is_running:
            return "Stopped"
        
        print("    ⌨️  OBVIOUS Keyboard: Pressing keys...")
        
        # Key mapping
        key_map = {
            'up': VK_UP,
            'down': VK_DOWN,
            'left': VK_LEFT,
            'right': VK_RIGHT,
            'pageup': VK_PRIOR,
            'pagedown': VK_NEXT,
            'home': VK_HOME,
            'end': VK_END,
            'tab': VK_TAB,
            'return': VK_RETURN,
            'delete': VK_DELETE,
            'backspace': VK_BACK,
            'space': VK_SPACE
        }
        
        num_keys = random.randint(5, 15)
        keys_pressed = []
        
        for i in range(num_keys):
            if not self.is_running:
                break
            
            key_name = random.choice(list(key_map.keys()))
            vk_code = key_map[key_name]
            keys_pressed.append(key_name)
            
            print(f"    ⌨️  Key {i+1}/{num_keys}: {key_name}")
            self.press_key(vk_code)
            time.sleep(0.2)
        
        return f"Pressed {num_keys} keys: {', '.join(keys_pressed)}"
    
    def start_tracking(self, duration_minutes=5):
        """Start the visible tracking"""
        self.is_running = True
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        print(f"🎯 Starting VISIBLE Activity Tracker for {duration_minutes} minutes...")
        print("🎯 This will make VERY OBVIOUS movements and activities!")
        print("=" * 60)
        print("🛑 STOP METHODS:")
        print("   • Press Ctrl+C to quit")
        print("   • Create kill switch file: touch STOP_TRACKER.txt")
        
        try:
            current_time = start_time
            activity_count = 0
            
            while current_time < end_time and self.is_running:
                if self.check_kill_switch():
                    break
                
                activity_count += 1
                elapsed_minutes = (current_time - start_time) / 60
                remaining_minutes = (end_time - current_time) / 60
                
                print(f"\n--- Activity {activity_count} ---")
                print(f"Time: {elapsed_minutes:.1f} minutes elapsed, {remaining_minutes:.1f} minutes remaining")
                
                # Choose activity type
                activity_type = random.choice([
                    "big_mouse_movement",
                    "obvious_clicks", 
                    "obvious_scrolling",
                    "obvious_keyboard"
                ])
                
                if activity_type == "big_mouse_movement":
                    result = self.big_mouse_movement()
                    print(f"    ✅ {result}")
                elif activity_type == "obvious_clicks":
                    result = self.obvious_clicks()
                    print(f"    ✅ {result}")
                elif activity_type == "obvious_scrolling":
                    result = self.obvious_scrolling()
                    print(f"    ✅ {result}")
                elif activity_type == "obvious_keyboard":
                    result = self.obvious_keyboard()
                    print(f"    ✅ {result}")
                
                self.session_analytics['total_activities'] += 1
                
                # Wait between activities
                wait_time = random.uniform(2, 8)
                print(f"    ⏱️  Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                
                current_time = time.time()
                    
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
        print("✅ VISIBLE Activity Tracker completed successfully")
        print(f"📊 Session Summary:")
        print(f"   • Duration: {session_duration/60:.1f} minutes")
        print(f"   • Total activities: {self.session_analytics['total_activities']}")
        print(f"   • Activities per minute: {self.session_analytics['total_activities']/(session_duration/60):.1f}")
        print("=" * 60)

def main():
    import sys
    
    tracker = VisibleTracker()
    
    print("VISIBLE Activity Tracker")
    print("=" * 50)
    print("🎯 Makes VERY OBVIOUS movements and activities!")
    print("⚠️  WARNING: This will actually move your mouse and click!")
    print("⚠️  Make sure no important work is open!")
    print("=" * 50)
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        try:
            minutes = float(sys.argv[1])
            if minutes <= 0:
                print("Please enter a positive number of minutes.")
                return
            elif minutes > 60:
                print("Maximum 60 minutes allowed for safety.")
                return
            
            print(f"\nStarting {minutes} minute tracking...")
            tracker.start_tracking(minutes)
            return
        except ValueError:
            print("Invalid argument. Please enter a number.")
            return
    
    # Interactive mode
    while True:
        try:
            minutes = float(input("\nEnter how many minutes you want to run the tracking: "))
            
            if minutes <= 0:
                print("Please enter a positive number of minutes.")
                continue
            elif minutes > 60:
                print("Maximum 60 minutes allowed for safety.")
                continue
            
            print(f"\nStarting {minutes} minute tracking...")
            
            confirm = input("Continue? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                tracker.start_tracking(minutes)
                break
            else:
                print("Tracking cancelled.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except ValueError:
            print("Invalid input. Please enter a number.")
        except EOFError:
            print("\nNo input available. Use: python visible_tracker.py <minutes>")
            break

if __name__ == "__main__":
    main()
