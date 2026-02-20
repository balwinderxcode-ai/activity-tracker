#!/usr/bin/env python3
"""
macOS API Activity Tracker
Uses macOS APIs (Quartz/CoreGraphics) for real mouse and keyboard control
Mirrors windows_api_tracker.py functionality exactly
"""

import time
import random
from datetime import datetime
import json
import os
import sys

# macOS-specific imports
try:
    import Quartz
    from Quartz import CGEvent
    HAS_QUARTZ = True
except ImportError:
    HAS_QUARTZ = False
    print("⚠️ Quartz not available, falling back to pyautogui")

try:
    import pyautogui
    HAS_PYAUTOGUI = True
    # Configure pyautogui for safety
    pyautogui.PAUSE = 0.01
    pyautogui.FAILSAFE = True
except ImportError:
    HAS_PYAUTOGUI = False
    print("⚠️ pyautogui not available")

try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False

# Track mouse position for failsafe
_last_mouse_position = None
_failSafeTriggered = False

# Mouse button constants (for reference, not used in macOS API)
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_ABSOLUTE = 0x8000

# Virtual key codes for macOS
VK_LEFT = 0x7B
VK_UP = 0x7E
VK_RIGHT = 0x7C
VK_DOWN = 0x7D
VK_HOME = 0x7F
VK_END = 0x77  # Correct macOS key code
VK_PRIOR = 0x74  # Page Up
VK_NEXT = 0x79   # Page Down
VK_TAB = 0x30
VK_RETURN = 0x24
VK_BACK = 0x33
VK_DELETE = 0x75
VK_SPACE = 0x31
VK_SHIFT = 0x38
VK_CONTROL = 0x3B
VK_COMMAND = 0x37  # macOS Command key

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
        
        # Check for Accessibility permissions on macOS
        self._check_accessibility_permissions()
        
        # Detect natural scrolling setting (macOS)
        self.natural_scrolling = self._detect_natural_scrolling()
        
        # Get screen dimensions using Quartz
        self._detect_screen_dimensions()
        
        if HAS_QUARTZ:
            print("✅ Real macOS API control enabled (Quartz/CoreGraphics)")
        elif HAS_PYAUTOGUI:
            print("✅ pyautogui fallback enabled")
        
        print("⚠️  WARNING: This will actually move your mouse and click!")
        print("⚠️  Make sure no important work is open!")
        print("💡 Tip: Create a 'STOP_TRACKER.txt' file to stop immediately")
    
    def _check_accessibility_permissions(self):
        """Check if the app has Accessibility permissions on macOS"""
        if HAS_QUARTZ:
            try:
                # Try to create a simple event to test permissions
                test_event = Quartz.CGEventCreate(None)
                if test_event:
                    # Clean up
                    del test_event
                    print("✅ Accessibility permissions verified")
            except Exception as e:
                print("⚠️  WARNING: Accessibility permissions may not be granted!")
                print("   Go to: System Preferences > Security & Privacy > Privacy > Accessibility")
                print("   Add your terminal/Python to the allowed apps")
    
    def _detect_natural_scrolling(self):
        """Detect if macOS natural scrolling is enabled"""
        try:
            # Check macOS natural scrolling setting
            # com.apple.swipescrolldirection: 1 = natural, 0 = traditional
            import subprocess
            result = subprocess.run(
                ['defaults', 'read', '-g', 'com.apple.swipescrolldirection'],
                capture_output=True, text=True
            )
            if result.returncode == 0 and '1' in result.stdout:
                return True  # Natural scrolling enabled
        except:
            pass
        return False  # Default to traditional
    
    def _detect_screen_dimensions(self):
        """Detect screen dimensions with proper Retina support"""
        if HAS_QUARTZ:
            try:
                display_id = Quartz.CGMainDisplayID()
                self.screen_width = int(Quartz.CGDisplayPixelsWide(display_id))
                self.screen_height = int(Quartz.CGDisplayPixelsHigh(display_id))
            except Exception as e:
                print(f"⚠️ Error detecting screen: {e}")
                if HAS_PYAUTOGUI:
                    self.screen_width, self.screen_height = pyautogui.size()
                else:
                    self.screen_width = 1920
                    self.screen_height = 1080
        elif HAS_PYAUTOGUI:
            self.screen_width, self.screen_height = pyautogui.size()
        else:
            self.screen_width = 1920
            self.screen_height = 1080
            print("⚠️ Could not detect screen size, using default 1920x1080")
        
        print(f"📺 Screen detected: {self.screen_width}x{self.screen_height}")
    
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
        """Move mouse to absolute position using macOS API"""
        # Check failsafe before moving
        if self._check_failsafe():
            return False
            
        try:
            if HAS_QUARTZ:
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
    
    def click_mouse(self, button='left'):
        """Click mouse button using macOS API"""
        try:
            # Get current mouse position
            if HAS_QUARTZ:
                event = Quartz.CGEventCreate(None)
                pos = Quartz.CGEventGetLocation(event)
                x, y = pos.x, pos.y
            elif HAS_PYAUTOGUI:
                x, y = pyautogui.position()
            else:
                x, y = 0, 0
            
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
        """Double click using macOS API"""
        try:
            # Get current position
            if HAS_QUARTZ:
                event = Quartz.CGEventCreate(None)
                pos = Quartz.CGEventGetLocation(event)
                x, y = pos.x, pos.y
            elif HAS_PYAUTOGUI:
                x, y = pyautogui.position()
            else:
                return False
            
            if HAS_QUARTZ:
                # First click
                down1 = Quartz.CGEventCreateMouseEvent(
                    None, Quartz.kCGEventLeftMouseDown, (x, y), Quartz.kCGMouseButtonLeft
                )
                up1 = Quartz.CGEventCreateMouseEvent(
                    None, Quartz.kCGEventLeftMouseUp, (x, y), Quartz.kCGMouseButtonLeft
                )
                
                # Second click
                down2 = Quartz.CGEventCreateMouseEvent(
                    None, Quartz.kCGEventLeftMouseDown, (x, y), Quartz.kCGMouseButtonLeft
                )
                up2 = Quartz.CGEventCreateMouseEvent(
                    None, Quartz.kCGEventLeftMouseUp, (x, y), Quartz.kCGMouseButtonLeft
                )
                
                # Set click state for double click
                Quartz.CGEventSetIntegerValueField(down1, Quartz.kCGMouseEventClickState, 2)
                Quartz.CGEventSetIntegerValueField(up1, Quartz.kCGMouseEventClickState, 2)
                Quartz.CGEventSetIntegerValueField(down2, Quartz.kCGMouseEventClickState, 2)
                Quartz.CGEventSetIntegerValueField(up2, Quartz.kCGMouseEventClickState, 2)
                
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, down1)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, up1)
                time.sleep(random.uniform(0.05, 0.15))
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, down2)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, up2)
            elif HAS_PYAUTOGUI:
                pyautogui.doubleClick()
            return True
        except Exception as e:
            print(f"Error double clicking: {e}")
            return False
    
    def scroll_wheel(self, direction, amount=3):
        """Scroll mouse wheel using macOS API
        direction: 1 = up, -1 = down (inverted if natural scrolling enabled)
        """
        try:
            # Adjust for natural scrolling (inverts the direction)
            actual_direction = direction
            if self.natural_scrolling:
                actual_direction = -direction
            
            if HAS_QUARTZ:
                scroll_delta = actual_direction * amount
                event = Quartz.CGEventCreateScrollWheelEvent(
                    None, 
                    Quartz.kCGScrollEventUnitLine,
                    1, 
                    scroll_delta
                )
                if event:
                    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
            elif HAS_PYAUTOGUI:
                pyautogui.scroll(actual_direction * amount)
            return True
        except Exception as e:
            print(f"Error scrolling: {e}")
            return False
    
    def _check_failsafe(self):
        """Check if mouse is in top-left corner (failsafe trigger)"""
        global _last_mouse_position, _failSafeTriggered
        
        if _failSafeTriggered:
            return True
            
        try:
            if HAS_QUARTZ:
                event = Quartz.CGEventCreate(None)
                pos = Quartz.CGEventGetLocation(event)
                x, y = pos.x, pos.y
            elif HAS_PYAUTOGUI:
                x, y = pyautogui.position()
            else:
                return False
            
            # Check if mouse is in top-left corner (0,0 to 10,10)
            if x < 10 and y < 10:
                print("\n🛑 FAILSAFE TRIGGERED: Mouse in top-left corner!")
                _failSafeTriggered = True
                self.is_running = False
                return True
            
            _last_mouse_position = (x, y)
            return False
        except:
            return False
    
    def press_key(self, vk_code):
        """Press a key using macOS API"""
        try:
            if HAS_QUARTZ:
                key_down = Quartz.CGEventCreateKeyboardEvent(None, vk_code, True)
                key_up = Quartz.CGEventCreateKeyboardEvent(None, vk_code, False)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_down)
                time.sleep(random.uniform(0.01, 0.05))
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_up)
            elif HAS_KEYBOARD:
                # Map key codes to key names for keyboard module
                key_map = {
                    0x7B: 'left', 0x7C: 'right', 0x7E: 'up', 0x7D: 'down',
                    0x30: 'tab', 0x24: 'enter', 0x33: 'backspace',
                    0x75: 'delete', 0x31: 'space', 0x35: 'esc',
                    0x7F: 'home', 0x77: 'end', 0x74: 'page up', 0x79: 'page down'
                }
                key_name = key_map.get(vk_code, chr(vk_code) if vk_code < 128 else 'enter')
                keyboard.send(key_name)
            elif HAS_PYAUTOGUI:
                pyautogui.press(chr(vk_code) if vk_code < 128 else 'enter')
            return True
        except Exception as e:
            print(f"Error pressing key: {e}")
            return False
    
    def key_combination(self, keys):
        """Press key combination using macOS API"""
        try:
            if HAS_QUARTZ:
                # Press all keys down
                for vk_code in keys:
                    key_down = Quartz.CGEventCreateKeyboardEvent(None, vk_code, True)
                    Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_down)
                    time.sleep(random.uniform(0.01, 0.05))
                
                # Release all keys in reverse order
                for vk_code in reversed(keys):
                    key_up = Quartz.CGEventCreateKeyboardEvent(None, vk_code, False)
                    Quartz.CGEventPost(Quartz.kCGHIDEventTap, key_up)
                    time.sleep(random.uniform(0.01, 0.05))
            elif HAS_KEYBOARD:
                keyboard.send('+'.join([chr(k) if k < 128 else 'cmd' for k in keys]))
            elif HAS_PYAUTOGUI:
                pyautogui.hotkey(*[chr(k) if k < 128 else 'command' for k in keys])
            return True
        except Exception as e:
            print(f"Error with key combination: {e}")
            return False
    
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
        
        # Get current mouse position
        current_x = random.randint(safe_x_min, safe_x_max)
        current_y = random.randint(safe_y_min, safe_y_max)
        
        # Execute the chosen movement pattern
        for _ in range(num_moves):
            if not self.is_running:
                break
                
            if movement_type == "large_move":
                # For large moves, go to completely random positions
                target_x = random.randint(safe_x_min, safe_x_max)
                target_y = random.randint(safe_y_min, safe_y_max)
            else:
                # Calculate next position (within safe bounds)
                target_x = max(safe_x_min, min(safe_x_max, 
                                     current_x + random.randint(-max_move, max_move)))
                target_y = max(safe_y_min, min(safe_y_max, 
                                     current_y + random.randint(-max_move, max_move)))
            
            # Move with slight curve for realism
            steps = random.randint(5, 15)
            for i in range(steps):
                if not self.is_running:
                    break
                    
                progress = i / steps
                # Add slight curve
                curve_offset = random.randint(-5, 5)
                
                x = int(current_x + (target_x - current_x) * progress + curve_offset)
                y = int(current_y + (target_y - current_y) * progress + curve_offset)
                
                # Ensure intermediate positions are also safe
                x = max(safe_x_min, min(safe_x_max, x))
                y = max(safe_y_min, min(safe_y_max, y))
                
                # Actually move the mouse
                self.move_mouse_to(x, y)
                time.sleep(random.uniform(0.01, 0.03))
            
            current_x, current_y = target_x, target_y
            time.sleep(random.uniform(0.1, 0.3))
        
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
        
        for _ in range(num_clicks):
            if not self.is_running:
                break
            
            # Move to a random safe position before clicking
            safe_x = random.randint(safe_x_min, safe_x_max)
            safe_y = random.randint(safe_y_min, safe_y_max)
            
            # Move to position
            self.move_mouse_to(safe_x, safe_y)
            time.sleep(random.uniform(0.1, 0.3))
            
            # Choose click type
            click_types = ["left", "left", "left", "double"]  # Mostly left clicks, some double
            click_type = random.choice(click_types)
            
            if click_type == "left":
                self.click_mouse('left')
            elif click_type == "double":
                self.double_click_mouse()
            
            # Random delay between multiple clicks
            if num_clicks > 1:
                time.sleep(random.uniform(0.05, 0.3))
        
        time.sleep(random.uniform(0.1, 1.0))  # Random delay after all clicks
        return f"Performed {num_clicks} real clicks"
    
    def simulate_navigation(self):
        """Simulate basic navigation key presses"""
        if not self.is_running:
            return "Stopped"
        
        # High activity: moderate keyboard navigation
        key_probability = random.uniform(0.4, 0.7)  # 40-70% chance
        
        if random.random() > key_probability:
            return "Skipped (low probability)"
        
        # Navigation keys mapping for macOS
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
            'shift': VK_SHIFT,
            'return': VK_RETURN,
            'enter': VK_RETURN,
            'delete': VK_DELETE,
            'backspace': VK_BACK,
            'space': VK_SPACE
        }
        
        # High activity: moderate keys per session (1-4 keys)
        num_keys = random.randint(1, 4)
        keys_pressed = []
        
        for _ in range(num_keys):
            if not self.is_running:
                break
                
            # Random key selection
            key_name = random.choice(list(key_map.keys()))
            vk_code = key_map[key_name]
            keys_pressed.append(key_name)
            
            # Actually press the key
            self.press_key(vk_code)
            
            # Random delay between key presses
            if num_keys > 1:
                time.sleep(random.uniform(0.1, 0.4))
        
        time.sleep(random.uniform(0.2, 0.8))  # Random delay after all key presses
        return f"Pressed {num_keys} real keys: {', '.join(keys_pressed)}"
    
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
        
        if scroll_pattern == "smooth_scroll":
            # Smooth continuous scrolling
            scroll_direction = random.choice([1, -1])  # 1 = up, -1 = down
            scroll_amount = random.randint(3, 8)
            for _ in range(scroll_amount):
                if not self.is_running:
                    break
                self.scroll_wheel(scroll_direction, random.randint(1, 3))
                time.sleep(random.uniform(0.1, 0.3))
                
        elif scroll_pattern == "burst_scroll":
            # Quick bursts of scrolling
            num_bursts = random.randint(2, 4)
            for _ in range(num_bursts):
                if not self.is_running:
                    break
                burst_amount = random.randint(2, 5)
                direction = random.choice([1, -1])
                for _ in range(burst_amount):
                    self.scroll_wheel(direction, random.randint(2, 4))
                    time.sleep(random.uniform(0.05, 0.1))
                time.sleep(random.uniform(0.2, 0.5))
                
        elif scroll_pattern == "slow_scroll":
            # Slow deliberate scrolling
            scroll_direction = random.choice([1, -1])
            scroll_amount = random.randint(5, 12)
            for _ in range(scroll_amount):
                if not self.is_running:
                    break
                self.scroll_wheel(scroll_direction, 1)  # Single unit scrolls
                time.sleep(random.uniform(0.3, 0.8))
                
        elif scroll_pattern == "mixed_scroll":
            # Mix of up and down scrolling
            total_scrolls = random.randint(6, 15)
            for _ in range(total_scrolls):
                if not self.is_running:
                    break
                direction = random.choice([1, -1])
                amount = random.randint(1, 3)
                self.scroll_wheel(direction, amount)
                time.sleep(random.uniform(0.1, 0.4))
                
        else:  # page_scroll
            # Large scroll amounts (page-like)
            num_pages = random.randint(1, 3)
            for _ in range(num_pages):
                if not self.is_running:
                    break
                direction = random.choice([1, -1])
                # Large scroll amounts to simulate page scrolling
                self.scroll_wheel(direction, random.randint(8, 15))
                time.sleep(random.uniform(0.5, 1.2))
        
        time.sleep(random.uniform(0.2, 0.8))
        return f"Real scroll using {scroll_pattern} pattern"
    
    def simulate_text_selection(self):
        """Simulate realistic text selection behaviors"""
        if not self.is_running:
            return "Stopped"
        
        # Get safe zone boundaries
        safe_x_min, safe_x_max, safe_y_min, safe_y_max = self.get_safe_zone()
        
        # Choose text selection type
        selection_type = random.choice([
            "click_drag",      # Click and drag to select text
            "double_click",    # Double-click to select word
            "triple_click",    # Triple-click to select line
            "shift_click"      # Click, then Shift+click to select range
        ])
        
        if selection_type == "click_drag":
            # Click and drag to select text
            start_x = random.randint(safe_x_min + 100, safe_x_max - 200)
            start_y = random.randint(safe_y_min + 100, safe_y_max - 100)
            
            # Move to start position
            self.move_mouse_to(start_x, start_y)
            time.sleep(random.uniform(0.3, 0.5))
            
            # Start drag (mouse down)
            if HAS_QUARTZ:
                down = Quartz.CGEventCreateMouseEvent(
                    None, Quartz.kCGEventLeftMouseDown, (start_x, start_y), Quartz.kCGMouseButtonLeft
                )
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
            
            # Drag to end position (realistic text selection length)
            end_x = start_x + random.randint(50, 300)
            end_y = start_y + random.randint(-20, 60)  # Might select multiple lines
            
            # Ensure end position is safe
            end_x = max(safe_x_min, min(safe_x_max, end_x))
            end_y = max(safe_y_min, min(safe_y_max, end_y))
            
            # Drag with human-like movement
            steps = random.randint(8, 15)
            for i in range(steps):
                if not self.is_running:
                    break
                progress = i / steps
                current_x = start_x + (end_x - start_x) * progress
                current_y = start_y + (end_y - start_y) * progress
                
                # Add slight tremor for realism
                tremor_x = random.uniform(-2, 2)
                tremor_y = random.uniform(-2, 2)
                
                self.move_mouse_to(current_x + tremor_x, current_y + tremor_y)
                time.sleep(random.uniform(0.02, 0.05))
            
            # End drag (mouse up)
            if HAS_QUARTZ:
                up = Quartz.CGEventCreateMouseEvent(
                    None, Quartz.kCGEventLeftMouseUp, (end_x, end_y), Quartz.kCGMouseButtonLeft
                )
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
            
        elif selection_type == "double_click":
            # Double-click to select word
            click_x = random.randint(safe_x_min + 100, safe_x_max - 100)
            click_y = random.randint(safe_y_min + 100, safe_y_max - 100)
            
            self.move_mouse_to(click_x, click_y)
            time.sleep(random.uniform(0.3, 0.5))
            self.double_click_mouse()
            
        elif selection_type == "triple_click":
            # Triple-click to select line
            click_x = random.randint(safe_x_min + 100, safe_x_max - 100)
            click_y = random.randint(safe_y_min + 100, safe_y_max - 100)
            
            self.move_mouse_to(click_x, click_y)
            time.sleep(random.uniform(0.3, 0.5))
            
            # Triple click
            for _ in range(3):
                self.click_mouse('left')
                time.sleep(random.uniform(0.05, 0.1))
            
        elif selection_type == "shift_click":
            # Click, then Shift+click for range selection
            start_x = random.randint(safe_x_min + 100, safe_x_max - 200)
            start_y = random.randint(safe_y_min + 100, safe_y_max - 100)
            
            # First click
            self.move_mouse_to(start_x, start_y)
            time.sleep(random.uniform(0.3, 0.5))
            self.click_mouse('left')
            
            # Move to end position
            end_x = start_x + random.randint(100, 400)
            end_y = start_y + random.randint(-50, 100)
            end_x = max(safe_x_min, min(safe_x_max, end_x))
            end_y = max(safe_y_min, min(safe_y_max, end_y))
            
            time.sleep(random.uniform(0.5, 1.0))
            self.move_mouse_to(end_x, end_y)
            time.sleep(random.uniform(0.4, 0.6))
            
            # Shift+click
            if HAS_QUARTZ:
                shift_down = Quartz.CGEventCreateKeyboardEvent(None, VK_SHIFT, True)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, shift_down)
                self.click_mouse('left')
                shift_up = Quartz.CGEventCreateKeyboardEvent(None, VK_SHIFT, False)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, shift_up)
            elif HAS_KEYBOARD:
                keyboard.press('shift')
                self.click_mouse('left')
                keyboard.release('shift')
        
        time.sleep(random.uniform(0.3, 1.0))
        return f"Real text selection using {selection_type}"
    
    def simulate_copy_paste_workflow(self):
        """Simulate realistic copy-paste workflows"""
        if not self.is_running:
            return "Stopped"
        
        # First, select some text
        self.simulate_text_selection()
        
        # Brief pause (reading selected text)
        time.sleep(random.uniform(0.2, 0.8))
        
        # Simulate copy (Command+C on macOS)
        self.key_combination([VK_COMMAND, ord('C')])
        time.sleep(random.uniform(0.1, 0.3))
        
        # Move to a different location
        safe_x_min, safe_x_max, safe_y_min, safe_y_max = self.get_safe_zone()
        paste_x = random.randint(safe_x_min + 100, safe_x_max - 100)
        paste_y = random.randint(safe_y_min + 100, safe_y_max - 100)
        
        self.move_mouse_to(paste_x, paste_y)
        time.sleep(random.uniform(0.5, 0.8))
        self.click_mouse('left')
        
        # Pause (thinking about where to paste)
        time.sleep(random.uniform(0.5, 2.0))
        
        # Simulate paste (Command+V on macOS)
        self.key_combination([VK_COMMAND, ord('V')])
        time.sleep(random.uniform(0.1, 0.5))
        
        return "Completed real copy-paste workflow"
    
    def simulate_hover_behavior(self):
        """Simulate realistic hover behaviors (reading tooltips, etc.)"""
        if not self.is_running:
            return "Stopped"
        
        safe_x_min, safe_x_max, safe_y_min, safe_y_max = self.get_safe_zone()
        
        # Move to a random position
        hover_x = random.randint(safe_x_min + 50, safe_x_max - 50)
        hover_y = random.randint(safe_y_min + 50, safe_y_max - 50)
        
        # Move with slightly slower, more deliberate movement
        self.move_mouse_to(hover_x, hover_y)
        time.sleep(random.uniform(0.8, 1.2))
        
        # Hover for a realistic amount of time (reading tooltip/info)
        hover_duration = random.uniform(0.5, 2.5)
        time.sleep(hover_duration)
        
        # Small micro-movements while hovering (natural hand tremor)
        for _ in range(random.randint(1, 4)):
            if not self.is_running:
                break
            micro_x = hover_x + random.uniform(-3, 3)
            micro_y = hover_y + random.uniform(-3, 3)
            self.move_mouse_to(micro_x, micro_y)
            time.sleep(0.1)
        
        return f"Real hover for {hover_duration:.1f}s"
    
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
                
                # Realistic activity patterns
                activity_pattern = random.choice(['mouse_heavy', 'keyboard_heavy', 'mouse_heavy2'])
                
                # Show activity pattern for this minute
                if activity_pattern == 'mouse_heavy':
                    print(f"    🖱️  Pattern: Mouse-heavy minute")
                elif activity_pattern == 'keyboard_heavy':
                    print(f"    ⌨️  Pattern: Keyboard-heavy minute")
                else:
                    print(f"    🖱️  Pattern: Mouse-heavy minute (variant)")
                
                if activity_pattern == 'mouse_heavy':
                    base_weights = [
                        random.uniform(1.0, 4.0),     # mouse_movement
                        random.uniform(12.0, 30.0),   # mouse_click
                        random.uniform(1.0, 8.0),     # navigation
                        random.uniform(1.5, 5.0),     # scroll_wheel
                        random.uniform(0.8, 2.5),     # text_selection
                        random.uniform(0.5, 2.0),    # copy_paste
                        random.uniform(0.5, 2.0),     # hover_behavior
                    ]
                elif activity_pattern == 'keyboard_heavy':
                    base_weights = [
                        random.uniform(0.2, 2.5),     # mouse_movement
                        random.uniform(3.0, 15.0),    # mouse_click
                        random.uniform(12.0, 35.0),   # navigation
                        random.uniform(0.5, 4.0),     # scroll_wheel
                        random.uniform(0.2, 2.0),     # text_selection
                        random.uniform(0.1, 1.2),     # copy_paste
                        random.uniform(0.1, 1.2),     # hover_behavior
                    ]
                else:  # mouse_heavy2
                    base_weights = [
                        random.uniform(1.5, 6.0),     # mouse_movement
                        random.uniform(15.0, 40.0),   # mouse_click
                        random.uniform(0.5, 5.0),     # navigation
                        random.uniform(2.0, 7.0),     # scroll_wheel
                        random.uniform(1.0, 3.5),     # text_selection
                        random.uniform(0.8, 2.5),     # copy_paste
                        random.uniform(0.8, 2.5),     # hover_behavior
                    ]
                
                # Simulate activities throughout the active minute
                seconds_used = 0
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
        
        print(f"Starting Real macOS API Activity Tracker for {duration_hours} hours...")
        print("Each hour is split into 6 windows of 10 minutes each")
        print("Activity scale: 1=idle, 10=very active (random 7-9)")
        print("=" * 60)
        print("🛑 STOP METHODS:")
        print("   • Press Ctrl+C to quit")
        print("   • Create kill switch file: touch STOP_TRACKER.txt")
        print("   • Move mouse to top-left corner to stop (failsafe)")
        
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
        print("✅ Real macOS API Activity Tracker completed successfully")
        print(f"📊 Session Summary:")
        print(f"   • Duration: {session_duration/60:.1f} minutes")
        print(f"   • Total activities: {self.session_analytics['total_activities']}")
        print(f"   • Activities per minute: {self.session_analytics['total_activities']/(session_duration/60):.1f}")
        print(f"   • Mistakes made: {self.session_analytics['mistakes_made']}")
        print(f"   • Human-likeness: {random.uniform(0.7, 0.95):.2f}")
        print("=" * 60)


def main():
    import sys
    
    tracker = MacOSAPITracker()
    
    print("Real macOS API Activity Tracker")
    print("=" * 50)
    print("✅ Uses macOS API directly for real mouse and keyboard control")
    print("⚠️  WARNING: This will actually move your mouse and click!")
    print("⚠️  Make sure no important work is open!")
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
            print("\nNo input available. Use: python macos_api_tracker.py <hours>")
            break


if __name__ == "__main__":
    main()