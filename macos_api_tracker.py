#!/usr/bin/env python3
"""
macOS API Activity Tracker
Uses macOS APIs (Quartz/CoreGraphics) for real mouse and keyboard control
Mirrors windows_api_tracker.py functionality
"""

import time
import random
import threading
from datetime import datetime, timedelta
import json
import os
import sys

# macOS-specific imports
try:
    import Quartz
    from Quartz import CGEvent, CGKeyCode
    import AppKit
    HAS_QUARTZ = True
except ImportError:
    HAS_QUARTZ = False
    print("⚠️ Quartz not available, falling back to pyautogui")

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False

# Mouse button constants
MOUSEEVENTF_LEFTDOWN = 0x0001
MOUSEEVENTF_LEFTUP = 0x0002
MOUSEEVENTF_RIGHTDOWN = 0x0004
MOUSEEVENTF_RIGHTUP = 0x0008
MOUSEEVENTF_MIDDLEDOWN = 0x0010
MOUSEEVENTF_MIDDLEUP = 0x0020
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_WHEEL = 0x0800

# Virtual key codes for macOS
VK_LEFT = 0x7B
VK_RIGHT = 0x7C
VK_UP = 0x7E
VK_DOWN = 0x7D
VK_HOME = 0x7F
VK_END = 0x7B  # Different mapping
VK_PRIOR = 0x7B
VK_NEXT = 0x7C
VK_TAB = 0x30
VK_RETURN = 0x24
VK_BACK = 0x33
VK_DELETE = 0x75
VK_SPACE = 0x31
VK_SHIFT = 0x38
VK_CONTROL = 0x3B
VK_ESCAPE = 0x35

class MacOSAPITracker:
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
        
        # Get screen dimensions using Quartz
        if HAS_QUARTZ:
            self.screen_width = int(Quartz.CGDisplayPixelsWide(Quartz.CGMainDisplayID()))
            self.screen_height = int(Quartz.CGDisplayPixelsHigh(Quartz.CGMainDisplayID()))
        elif HAS_PYAUTOGUI:
            self.screen_width, self.screen_height = pyautogui.size()
        else:
            self.screen_width = 1920
            self.screen_height = 1080
            print("⚠️ Could not detect screen size, using default 1920x1080")
        
        print(f"📺 Screen detected: {self.screen_width}x{self.screen_height}")
        
        if HAS_QUARTZ:
            print("✅ Quartz/CoreGraphics API control enabled")
        elif HAS_PYAUTOGUI:
            print("✅ pyautogui fallback enabled")
        
        print("⚠️  WARNING: This will actually move your mouse and click!")
        print("⚠️  Make sure no important work is open!")
        print("💡 Tip: Create a 'STOP_TRACKER.txt' file to stop immediately")
    
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
        """Get safe zone coordinates for macOS screen"""
        margin = 100  # Safe margin from edges
        
        safe_x_min = margin
        safe_x_max = self.screen_width - margin
        safe_y_min = margin + 50  # Extra margin from top (menu bar)
        safe_y_max = self.screen_height - margin - 50  # Extra margin from bottom (dock)
        
        return safe_x_min, safe_x_max, safe_y_min, safe_y_max
    
    def move_mouse_to(self, x, y):
        """Move mouse to absolute position using Quartz/CoreGraphics"""
        try:
            if HAS_QUARTZ:
                # Use Quartz for direct CGEvent
                move = Quartz.CGEventCreateMouseEvent(
                    None,
                    Quartz.kCGEventMouseMoved,
                    (x, y),
                    Quartz.kCGMouseButtonLeft
                )
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, move)
            elif HAS_PYAUTOGUI:
                pyautogui.moveTo(x, y)
            return True
        except Exception as e:
            print(f"Error moving mouse: {e}")
            return False
    
    def move_mouse_relative(self, dx, dy):
        """Move mouse relatively"""
        try:
            if HAS_QUARTZ:
                move = Quartz.CGEventCreateMouseEvent(
                    None,
                    Quartz.kCGEventMouseMoved,
                    (dx, dy),
                    Quartz.kCGMouseButtonLeft
                )
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, move)
            elif HAS_PYAUTOGUI:
                pyautogui.move(dx, dy)
            return True
        except Exception as e:
            print(f"Error moving mouse: {e}")
            return False
    
    def click_mouse(self, button='left'):
        """Click mouse button using Quartz/CoreGraphics"""
        try:
            # Get current mouse position
            if HAS_QUARTZ:
                event = Quartz.CGEventCreate(None)
                pos = Quartz.CGEventGetLocation(event)
                x, y = pos.x, pos.y
            elif HAS_PYAUTOGUI:
                x, y = pyautogui.position()
            
            if button == 'left':
                if HAS_QUARTZ:
                    down = Quartz.CGEventCreateMouseEvent(
                        None, Quartz.kCGEventLeftMouseDown, (x, y), Quartz.kCGMouseButtonLeft
                    )
                    up = Quartz.CGEventCreateMouseEvent(
                        None, Quartz.kCGEventLeftMouseUp, (x, y), Quartz.kCGMouseButtonLeft
                    )
                    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
                    time.sleep(random.uniform(0.01, 0.05))
                    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
                elif HAS_PYAUTOGUI:
                    pyautogui.click()
            elif button == 'right':
                if HAS_QUARTZ:
                    down = Quartz.CGEventCreateMouseEvent(
                        None, Quartz.kCGEventRightMouseDown, (x, y), Quartz.kCGMouseButtonRight
                    )
                    up = Quartz.CGEventCreateMouseEvent(
                        None, Quartz.kCGEventRightMouseUp, (x, y), Quartz.kCGMouseButtonRight
                    )
                    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
                    time.sleep(random.uniform(0.01, 0.05))
                    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
                elif HAS_PYAUTOGUI:
                    pyautogui.rightClick()
            return True
        except Exception as e:
            print(f"Error clicking mouse: {e}")
            return False
    
    def double_click_mouse(self):
        """Double click using Quartz/CoreGraphics"""
        try:
            if HAS_QUARTZ:
                event = Quartz.CGEventCreate(None)
                pos = Quartz.CGEventGetLocation(event)
                x, y = pos.x, pos.y
                
                # First click
                down1 = Quartz.CGEventCreateMouseEvent(
                    None, Quartz.kCGEventLeftMouseDown, (x, y), Quartz.kCGMouseButtonLeft
                )
                up1 = Quartz.CGEventCreateMouseEvent(
                    None, Quartz.kCGEventLeftMouseUp, (x, y), Quartz.kCGMouseButtonLeft
                )
                Quartz.CGEventSetIntegerValueField(down1, Quartz.kCGMouseEventClickState, 2)
                Quartz.CGEventSetIntegerValueField(up1, Quartz.kCGMouseEventClickState, 2)
                
                # Second click
                down2 = Quartz.CGEventCreateMouseEvent(
                    None, Quartz.kCGEventLeftMouseDown, (x, y), Quartz.kCGMouseButtonLeft
                )
                up2 = Quartz.CGEventCreateMouseEvent(
                    None, Quartz.kCGEventLeftMouseUp, (x, y), Quartz.kCGMouseButtonLeft
                )
                Quartz.CGEventSetIntegerValueField(down2, Quartz.kCGMouseEventClickState, 2)
                Quartz.CGEventSetIntegerValueField(up2, Quartz.kCGMouseEventClickState, 2)
                
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, down1)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, up1)
                time.sleep(0.05)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, down2)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, up2)
            elif HAS_PYAUTOGUI:
                pyautogui.doubleClick()
            return True
        except Exception as e:
            print(f"Error double clicking: {e}")
            return False
    
    def scroll_wheel(self, direction='down', clicks=1):
        """Scroll wheel using Quartz/CoreGraphics"""
        try:
            if HAS_QUARTZ:
                scroll_amount = -clicks if direction == 'down' else clicks
                event = Quartz.CGEventCreateScrollWheelEvent(
                    None, Quartz.kCGScrollEventUnitPixel, 1, scroll_amount
                )
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
            elif HAS_PYAUTOGUI:
                pyautogui.scroll(-clicks if direction == 'down' else clicks)
            return True
        except Exception as e:
            print(f"Error scrolling: {e}")
            return False
    
    def press_key(self, key_code, modifiers=None):
        """Press key using Quartz/CoreGraphics"""
        try:
            if HAS_KEYBOARD:
                if modifiers:
                    keyboard.send(key_code, modifiers=modifiers)
                else:
                    keyboard.send(key_code)
            elif HAS_QUARTZ:
                key_down = Quartz.CGEventCreateKeyboardEvent(None, key_code, True)
                key_up = Quartz.CGEventCreateKeyboardEvent(None, key_code, False)
                
                if modifiers:
                    if 'shift' in modifiers:
                        Quartz.CGEventSetFlags(key_down, Quartz.kCGEventFlagMaskShift)
                        Quartz.CGEventSetFlags(key_up, Quartz.kCGEventFlagMaskShift)
                
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_down)
                time.sleep(random.uniform(0.01, 0.05))
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_up)
            elif HAS_PYAUTOGUI:
                pyautogui.press(key_code)
            return True
        except Exception as e:
            print(f"Error pressing key: {e}")
            return False
    
    def type_text(self, text):
        """Type text using keyboard module"""
        try:
            if HAS_KEYBOARD:
                keyboard.write(text, delay=random.uniform(0.05, 0.15))
            elif HAS_PYAUTOGUI:
                pyautogui.write(text, interval=random.uniform(0.05, 0.15))
            return True
        except Exception as e:
            print(f"Error typing text: {e}")
            return False
    
    def get_random_position_in_safe_zone(self):
        """Get random position within safe zone"""
        safe_x_min, safe_x_max, safe_y_min, safe_y_max = self.get_safe_zone()
        
        x = random.randint(int(safe_x_min), int(safe_x_max))
        y = random.randint(int(safe_y_min), int(safe_y_max))
        
        return x, y
    
    def get_smooth_mouse_path(self, start_x, start_y, end_x, end_y, steps=None):
        """Generate smooth mouse path with human-like variation"""
        if steps is None:
            distance = ((end_x - start_x)**2 + (end_y - start_y)**2) ** 0.5
            steps = max(3, int(distance / 50))  # One step per 50 pixels
        
        path = []
        for i in range(steps):
            t = i / (steps - 1) if steps > 1 else 0
            
            # Add some easing
            t = t * t * (3 - 2 * t)  # Smoothstep
            
            # Linear interpolation with slight randomness
            x = start_x + (end_x - start_x) * t + random.uniform(-2, 2)
            y = start_y + (end_y - start_y) * t + random.uniform(-2, 2)
            
            path.append((int(x), int(y)))
        
        return path
    
    def move_mouse_human_like(self, end_x, end_y):
        """Move mouse in human-like manner with smooth path"""
        try:
            # Get current position
            if HAS_QUARTZ:
                event = Quartz.CGEventCreate(None)
                start_pos = Quartz.CGEventGetLocation(event)
                start_x, start_y = start_pos.x, start_pos.y
            elif HAS_PYAUTOGUI:
                start_x, start_y = pyautogui.position()
            
            # Generate smooth path
            path = self.get_smooth_mouse_path(start_x, start_y, end_x, end_y)
            
            # Move along path with varying speeds
            for x, y in path:
                self.move_mouse_to(x, y)
                # Vary the delay for human-like movement
                delay = random.uniform(0.01, 0.03)
                time.sleep(delay)
            
            return True
        except Exception as e:
            print(f"Error in human-like move: {e}")
            return False
    
    def simulate_idle(self, duration_minutes=None):
        """Simulate idle period"""
        if duration_minutes is None:
            idle_config = self.config.get('idle_periods', {})
            duration_minutes = random.randint(
                idle_config.get('min_duration', 5),
                idle_config.get('max_duration', 30)
            )
        
        print(f"💤 Simulating idle for {duration_minutes} minutes...")
        
        # Convert to seconds for the loop
        duration_seconds = duration_minutes * 60
        check_interval = 5  # Check every 5 seconds for kill switch
        
        for _ in range(int(duration_seconds / check_interval)):
            if self.check_kill_switch():
                return
            
            # Occasionally check other things during idle
            if random.random() < 0.1:
                self.update_human_state()
            
            time.sleep(check_interval)
        
        print("✅ Idle period complete")
    
    def simulate_activity(self, activity_type='general', duration_minutes=5):
        """Simulate realistic activity with human-like behavior"""
        print(f"🎯 Simulating {activity_type} activity for {duration_minutes} minutes...")
        
        end_time = time.time() + (duration_minutes * 60)
        activity_count = 0
        
        while time.time() < end_time and self.is_running:
            if self.check_kill_switch():
                break
            
            # Update human state
            self.update_human_state()
            
            # Check if break is needed
            if self.break_needed:
                print("😴 Taking a break...")
                self.simulate_idle(random.randint(2, 5))
                self.break_needed = False
                self.consecutive_active_minutes = 0
                continue
            
            # Get activity pattern from config
            patterns = self.config.get('activity_patterns', {})
            pattern = patterns.get(activity_type, {})
            
            # Random interval between actions
            interval_config = self.config.get('mouse_movement_interval', (1, 5))
            next_action_delay = random.uniform(interval_config[0], interval_config[1])
            
            # Reduce delay based on focus level
            next_action_delay *= (2 - self.focus_level)
            
            # Decide what action to take
            action_roll = random.random()
            
            if action_roll < pattern.get('mouse_movement_frequency', 0.6):
                # Move mouse to random position
                target_x, target_y = self.get_random_position_in_safe_zone()
                self.move_mouse_human_like(target_x, target_y)
                activity_count += 1
                self.consecutive_active_minutes += 1
                
                # Occasionally click
                if random.random() < pattern.get('click_frequency', 0.3):
                    # Random click type
                    click_roll = random.random()
                    if click_roll < 0.7:
                        self.click_mouse('left')
                    elif click_roll < 0.9:
                        self.click_mouse('right')
                    else:
                        self.double_click_mouse()
                    activity_count += 1
                    
                    # Occasionally scroll after click
                    if random.random() < 0.3:
                        direction = 'up' if random.random() > 0.5 else 'down'
                        self.scroll_wheel(direction, random.randint(1, 3))
                
                self.session_analytics['total_activities'] += 1
                
            elif action_roll < pattern.get('mouse_movement_frequency', 0.6) + 0.2:
                # Scroll wheel
                direction = 'up' if random.random() > 0.5 else 'down'
                self.scroll_wheel(direction, random.randint(1, 5))
                activity_count += 1
                self.session_analytics['total_activities'] += 1
                
            else:
                # Small pause, micro-movement
                time.sleep(random.uniform(0.5, 2))
            
            # Record activity
            self.activity_history.append({
                'timestamp': datetime.now().isoformat(),
                'type': activity_type,
                'fatigue': self.fatigue_level,
                'focus': self.focus_level
            })
            
            # Wait before next action
            time.sleep(next_action_delay)
        
        print(f"✅ Activity session complete. Performed {activity_count} actions.")
    
    def get_session_summary(self):
        """Get summary of current session"""
        duration = (time.time() - self.session_start_time) / 60  # minutes
        
        summary = {
            'duration_minutes': duration,
            'total_activities': self.session_analytics['total_activities'],
            'final_fatigue_level': self.fatigue_level,
            'final_focus_level': self.focus_level,
            'activity_history_count': len(self.activity_history)
        }
        
        return summary
    
    def run(self, activity_type='coding', duration_minutes=10):
        """Main run method"""
        print(f"\n🚀 Starting Activity Tracker")
        print(f"📋 Activity type: {activity_type}")
        print(f"⏱️  Duration: {duration_minutes} minutes")
        print(f"🛑 To stop: create 'STOP_TRACKER.txt' file")
        print("-" * 40)
        
        self.is_running = True
        self.session_start_time = time.time()
        
        try:
            self.simulate_activity(activity_type, duration_minutes)
        except KeyboardInterrupt:
            print("\n⚠️ Interrupted by user")
        finally:
            self.is_running = False
            
            # Print session summary
            summary = self.get_session_summary()
            print("\n📊 Session Summary:")
            print(f"   Duration: {summary['duration_minutes']:.1f} minutes")
            print(f"   Total activities: {summary['total_activities']}")
            print(f"   Final fatigue: {summary['final_fatigue_level']:.2f}")
            print(f"   Final focus: {summary['final_focus_level']:.2f}")
            print("\n✅ Tracker stopped")


def main():
    """Main entry point"""
    tracker = MacOSAPITracker()
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='macOS Activity Tracker')
    parser.add_argument('-a', '--activity', default='coding', 
                        choices=['coding', 'browsing', 'research'],
                        help='Activity type to simulate')
    parser.add_argument('-d', '--duration', type=int, default=10,
                        help='Duration in minutes')
    
    args = parser.parse_args()
    
    tracker.run(args.activity, args.duration)


if __name__ == '__main__':
    main()
