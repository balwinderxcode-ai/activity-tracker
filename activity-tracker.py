#!/usr/bin/env python3
"""
Activity Tracker
Simulates realistic user activity to test time tracking systems
"""

import time
import random
import pyautogui
import keyboard
import threading
from datetime import datetime, timedelta
import json
import os

class ActivityTracker:
    def __init__(self):
        self.is_running = False
        self.error_count = 0
        self.max_errors = 100  # Maximum errors before stopping (increased for longer runs)
        self.config = self.load_config()
        self.kill_switch_file = "STOP_TRACKER.txt"  # Kill switch file
        
        # Human-like behavior state
        self.session_start_time = time.time()
        self.fatigue_level = 0.0  # 0.0 = fresh, 1.0 = very tired
        self.focus_level = random.uniform(0.7, 1.0)  # Current focus level
        self.mouse_precision = random.uniform(0.8, 1.0)  # How precise mouse movements are
        self.last_activity_time = time.time()
        self.consecutive_active_minutes = 0
        self.break_needed = False
        
        # Personal quirks and habits
        self.perfectionist_level = random.uniform(0.1, 0.8)  # How often to correct "mistakes"
        self.distraction_proneness = random.uniform(0.05, 0.2)  # Likelihood of getting distracted
        
        # Anti-detection features
        self.activity_history = []  # Track recent activities for pattern avoidance
        self.timing_history = []    # Track timing patterns
        self.last_activity_type = None
        self.repetition_count = 0
        self.pattern_detection_threshold = 3  # Avoid repeating same activity too much
        self.timing_jitter_base = random.uniform(0.8, 1.2)  # Personal timing signature
        self.micro_delay_signature = random.uniform(0.02, 0.08)  # Unique micro-delay pattern
        
        # Behavioral fingerprint (unique to this "person")
        self.click_pressure_variation = random.uniform(0.05, 0.15)
        
        # Initialize window pattern storage for scattered idle/active minutes
        self.current_window_idle_pattern = []
        self.movement_style = random.choice(['smooth', 'jerky', 'deliberate', 'quick'])
        self.mistake_frequency = random.uniform(0.02, 0.08)  # How often to make "mistakes"
        
        # Disable pyautogui failsafe for continuous operation
        pyautogui.FAILSAFE = False
        
        # MacBook Pro 15-inch 2018 Retina Display configuration
        self.screen_width, self.screen_height = 2880, 1800
        
    def check_kill_switch(self):
        """Check if kill switch file exists to stop the tracker"""
        if os.path.exists(self.kill_switch_file):
            print(f"\n🛑 KILL SWITCH ACTIVATED!")
            print(f"Found kill switch file: {self.kill_switch_file}")
            print("Stopping tracker immediately...")
            self.is_running = False
            # Remove the kill switch file
            try:
                os.remove(self.kill_switch_file)
                print("✅ Kill switch file removed")
            except Exception as e:
                print(f"⚠️  Could not remove kill switch file: {e}")
            return True
        return False
    
    def load_config(self):
        """Load configuration from file or create default"""
        default_config = {
            "mouse_movement_interval": (1, 5),  # seconds between movements
            "click_probability": 0.3,  # 30% chance of clicking
            "idle_periods": {
                "min_duration": 5,  # seconds
                "max_duration": 30
            },
            "activity_patterns": {
                "coding": {
                    "mouse_movement_frequency": 0.9,
                    "click_frequency": 0.8
                },
                "browsing": {
                    "mouse_movement_frequency": 0.95,
                    "click_frequency": 0.9
                },
                "research": {
                    "mouse_movement_frequency": 0.92,
                    "click_frequency": 0.85
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
    
    
    def handle_error(self, error, context="Unknown"):
        """Handle errors gracefully with recovery mechanisms"""
        self.error_count += 1
        error_msg = f"Error in {context}: {str(error)}"
        
        # Log error details for debugging
        print(f"⚠️  Error #{self.error_count}/{self.max_errors} in {context}: {str(error)}")
        
        if self.error_count >= self.max_errors:
            print(f"🛑 Maximum errors ({self.max_errors}) reached. Stopping tracker.")
            self.is_running = False
            return False
        
        # Implement recovery strategies based on error type
        if "pyautogui" in str(error).lower():
            time.sleep(1)  # Brief pause before continuing
        elif "keyboard" in str(error).lower():
            pass  # Continue without keyboard listener
        elif "screen" in str(error).lower():
            pass  # Use fallback dimensions
        
        return True  # Continue operation
    
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
        
        # Time-based focus patterns
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 11:  # Morning peak
            self.focus_level *= 1.2
        elif 13 <= current_hour <= 15:  # Post-lunch dip
            self.focus_level *= 0.8
        elif 16 <= current_hour <= 18:  # Afternoon recovery
            self.focus_level *= 1.1
        
        self.focus_level = min(1.0, self.focus_level)
        
    
    def get_human_adjusted_delay(self, base_delay):
        """Get delay adjusted for current human state"""
        # Slower when tired or unfocused
        fatigue_multiplier = 1.0 + (self.fatigue_level * 0.5)
        focus_multiplier = 2.0 - self.focus_level  # Less focus = slower
        
        adjusted_delay = base_delay * fatigue_multiplier * focus_multiplier
        
        # Add random human variation
        variation = random.uniform(0.8, 1.3)
        return adjusted_delay * variation
    
    def should_take_break(self):
        """Determine if a break should be taken"""
        if self.break_needed:
            return True
        
        # Random break chance increases with fatigue
        break_chance = self.fatigue_level * 0.1 + self.distraction_proneness
        return random.random() < break_chance
    
    def simulate_micro_break(self):
        """Simulate a micro-break (distraction, checking phone, etc.)"""
        if not self.is_running:
            return
            
        break_type = random.choice([
            "phone_check",
            "stretch", 
            "drink_water",
            "look_away",
            "deep_breath"
        ])
        
        break_duration = random.uniform(5, 30)  # 5-30 seconds
        
        time.sleep(break_duration)
        
        # Slightly restore focus and reset break need
        self.focus_level = min(1.0, self.focus_level + 0.1)
        if break_duration > 20:
            self.consecutive_active_minutes = max(0, self.consecutive_active_minutes - 5)
            self.break_needed = False
    
    def get_time_based_activity_modifier(self):
        """Get activity level modifier based on current time"""
        current_time = datetime.now()
        hour = current_time.hour
        day_of_week = current_time.weekday()  # 0=Monday, 6=Sunday
        
        # Base activity level by hour (24-hour format)
        hourly_patterns = {
            0: 0.1, 1: 0.05, 2: 0.05, 3: 0.05, 4: 0.05, 5: 0.1,   # Late night/early morning
            6: 0.3, 7: 0.5, 8: 0.7, 9: 0.9, 10: 1.0, 11: 1.0,     # Morning ramp-up
            12: 0.6, 13: 0.4, 14: 0.5, 15: 0.7, 16: 0.8, 17: 0.9,  # Lunch dip & recovery
            18: 0.8, 19: 0.6, 20: 0.5, 21: 0.4, 22: 0.3, 23: 0.2   # Evening wind-down
        }
        
        base_modifier = hourly_patterns.get(hour, 0.5)
        
        # Day of week adjustments
        if day_of_week == 0:  # Monday - slow start
            base_modifier *= 0.8
        elif day_of_week == 4:  # Friday - distracted
            base_modifier *= 0.9
        elif day_of_week >= 5:  # Weekend - different pattern
            base_modifier *= 0.6
        
        # Add some randomness
        random_factor = random.uniform(0.8, 1.2)
        
        return base_modifier * random_factor
    
    def is_break_time(self):
        """Check if it's a natural break time"""
        current_time = datetime.now()
        hour = current_time.hour
        minute = current_time.minute
        
        # Common break times
        break_times = [
            (10, 15),  # 10:15 AM - morning break
            (12, 0),   # 12:00 PM - lunch
            (15, 30),  # 3:30 PM - afternoon break
            (17, 0),   # 5:00 PM - end of day
        ]
        
        for break_hour, break_minute in break_times:
            if hour == break_hour and abs(minute - break_minute) <= 15:
                return True
        
        return False
    
    def get_work_intensity_schedule(self):
        """Get work intensity based on realistic work schedule"""
        current_time = datetime.now()
        hour = current_time.hour
        day_of_week = current_time.weekday()
        
        # Weekend has different patterns
        if day_of_week >= 5:
            return random.uniform(0.3, 0.7)  # Lower weekend activity
        
        # Weekday patterns
        if 6 <= hour <= 8:  # Early morning
            return random.uniform(0.4, 0.8)
        elif 9 <= hour <= 11:  # Morning peak
            return random.uniform(0.8, 1.0)
        elif 12 <= hour <= 13:  # Lunch time
            return random.uniform(0.2, 0.5)
        elif 14 <= hour <= 16:  # Afternoon work
            return random.uniform(0.7, 0.9)
        elif 17 <= hour <= 19:  # End of day wrap-up
            return random.uniform(0.5, 0.8)
        else:  # Off hours
            return random.uniform(0.1, 0.4)
    
    def add_anti_detection_jitter(self, base_delay):
        """Add sophisticated timing jitter to avoid detection"""
        # Personal timing signature (consistent but not robotic)
        signature_multiplier = self.timing_jitter_base
        
        # Add micro-variations based on "muscle memory"
        muscle_memory_variation = random.uniform(0.95, 1.05)
        
        # Add occasional larger variations (human inconsistency)
        if random.random() < 0.1:  # 10% chance of larger variation
            inconsistency_factor = random.uniform(0.5, 2.0)
        else:
            inconsistency_factor = 1.0
        
        # Combine all factors
        jittered_delay = base_delay * signature_multiplier * muscle_memory_variation * inconsistency_factor
        
        # Add micro-delay signature (unique to this person)
        jittered_delay += self.micro_delay_signature
        
        return max(0.01, jittered_delay)  # Never go below 10ms
    
    def avoid_repetitive_patterns(self, candidate_activity):
        """Avoid repetitive patterns that look robotic"""
        # Track activity history
        if len(self.activity_history) >= 10:
            self.activity_history.pop(0)  # Keep only last 10 activities
        
        # Check for repetition
        if candidate_activity == self.last_activity_type:
            self.repetition_count += 1
        else:
            self.repetition_count = 0
            
        # If we're repeating too much, force a different activity
        if self.repetition_count >= self.pattern_detection_threshold:
            # Choose a different activity
            all_activities = ["mouse_movement", "mouse_click", "navigation", "tab_switching", 
                            "scroll_wheel", "text_selection", "copy_paste", "hover_behavior"]
            different_activities = [a for a in all_activities if a != candidate_activity]
            
            if different_activities:
                new_activity = random.choice(different_activities)
                return new_activity
        
        return candidate_activity
    
    def simulate_human_mistakes(self):
        """Simulate realistic human mistakes and corrections"""
        if not self.is_running:
            return
            
        if random.random() > self.mistake_frequency:
            return  # No mistake this time
            
        try:
            mistake_type = random.choice([
                "double_click",     # Accidental double-click
                "wrong_selection",  # Select wrong text then reselect
                "mouse_slip"        # Move mouse then correct position
            ])
            
            if mistake_type == "double_click":
                # Accidental extra click
                safe_x_min, safe_x_max, safe_y_min, safe_y_max = self.get_safe_zone()
                click_x = random.randint(safe_x_min + 100, safe_x_max - 100)
                click_y = random.randint(safe_y_min + 100, safe_y_max - 100)
                
                pyautogui.moveTo(click_x, click_y, duration=self.add_anti_detection_jitter(0.3))
                pyautogui.click()
                time.sleep(self.add_anti_detection_jitter(0.1))
                pyautogui.click()  # Accidental second click
                
            elif mistake_type == "mouse_slip":
                # Move mouse to wrong position then correct
                safe_x_min, safe_x_max, safe_y_min, safe_y_max = self.get_safe_zone()
                
                # Wrong position
                wrong_x = random.randint(safe_x_min, safe_x_max)
                wrong_y = random.randint(safe_y_min, safe_y_max)
                pyautogui.moveTo(wrong_x, wrong_y, duration=self.add_anti_detection_jitter(0.2))
                
                # Pause (realizing wrong position)
                time.sleep(self.add_anti_detection_jitter(random.uniform(0.1, 0.4)))
                
                # Move to correct position
                correct_x = random.randint(safe_x_min, safe_x_max)
                correct_y = random.randint(safe_y_min, safe_y_max)
                pyautogui.moveTo(correct_x, correct_y, duration=self.add_anti_detection_jitter(0.3))
                
            
            # Add natural pause after mistake
            time.sleep(self.add_anti_detection_jitter(random.uniform(0.2, 1.0)))
            
        except Exception as e:
            if not self.handle_error(e, "human_mistakes"):
                return
    
    def add_natural_interruptions(self):
        """Add natural interruptions that humans experience"""
        if not self.is_running:
            return
            
        interruption_chance = 0.02  # 2% chance per activity
        if random.random() > interruption_chance:
            return
            
        interruption_type = random.choice([
            "phone_buzz",       # Check phone notification
            "door_sound",       # Look away from screen
            "drink_sip",        # Take a sip of drink
            "adjust_posture",   # Adjust sitting position
            "check_time",       # Check the time
            "scratch_itch"      # Quick body adjustment
        ])
        
        interruption_duration = random.uniform(1, 8)  # 1-8 seconds
        
        time.sleep(self.add_anti_detection_jitter(interruption_duration))
        
        # Sometimes these interruptions lead to brief activity changes
        if random.random() < 0.3:  # 30% chance
            self.simulate_micro_break()
    
    def get_movement_style_modifier(self):
        """Apply personal movement style to mouse movements"""
        if self.movement_style == 'smooth':
            return {'speed_multiplier': 0.8, 'steps_multiplier': 1.5}
        elif self.movement_style == 'jerky':
            return {'speed_multiplier': 1.3, 'steps_multiplier': 0.7}
        elif self.movement_style == 'deliberate':
            return {'speed_multiplier': 0.6, 'steps_multiplier': 2.0}
        elif self.movement_style == 'quick':
            return {'speed_multiplier': 1.5, 'steps_multiplier': 0.8}
        else:
            return {'speed_multiplier': 1.0, 'steps_multiplier': 1.0}
    
    def initialize_analytics(self):
        """Initialize analytics and intelligence systems"""
        self.session_analytics = {
            'start_time': time.time(),
            'total_activities': 0,
            'activity_breakdown': {},
            'efficiency_score': 0.0,
            'focus_periods': [],
            'break_periods': [],
            'mistakes_made': 0,
            'patterns_avoided': 0,
            'interruptions': 0
        }
        
        self.performance_metrics = {
            'average_response_time': 0.0,
            'consistency_score': 0.0,
            'human_likeness_score': 0.0,
            'anti_detection_score': 0.0
        }
        
        self.adaptive_weights = {
            'mouse_movement': 1.0,
            'mouse_click': 1.0,
            'navigation': 1.0,
            'tab_switching': 1.0,
            'scroll_wheel': 1.0,
            'text_selection': 1.0,
            'copy_paste': 1.0,
            'hover_behavior': 1.0
        }
    
    def analyze_activity_patterns(self):
        """Analyze current activity patterns for optimization"""
        if len(self.activity_history) < 5:
            return  # Need more data
        
        # Analyze recent activity distribution
        recent_activities = self.activity_history[-10:]
        activity_counts = {}
        
        for activity in recent_activities:
            activity_counts[activity] = activity_counts.get(activity, 0) + 1
        
        # Detect if we're being too repetitive
        max_count = max(activity_counts.values()) if activity_counts else 0
        if max_count > 6:  # More than 60% of recent activities are the same
            dominant_activity = max(activity_counts, key=activity_counts.get)
            
            # Reduce weight of dominant activity
            if dominant_activity in self.adaptive_weights:
                self.adaptive_weights[dominant_activity] *= 0.8
        
        # Calculate diversity score
        diversity_score = len(activity_counts) / len(recent_activities) if recent_activities else 0
        self.session_analytics['efficiency_score'] = diversity_score
    
    def update_performance_metrics(self, activity_type, duration):
        """Update performance metrics based on completed activities"""
        self.session_analytics['total_activities'] += 1
        
        # Update activity breakdown
        if activity_type not in self.session_analytics['activity_breakdown']:
            self.session_analytics['activity_breakdown'][activity_type] = 0
        self.session_analytics['activity_breakdown'][activity_type] += 1
        
        # Update average response time
        current_avg = self.performance_metrics['average_response_time']
        total_activities = self.session_analytics['total_activities']
        
        self.performance_metrics['average_response_time'] = (
            (current_avg * (total_activities - 1) + duration) / total_activities
        )
        
        # Calculate human-likeness score based on various factors
        timing_variance = abs(duration - self.performance_metrics['average_response_time'])
        timing_score = max(0, 1.0 - (timing_variance / 2.0))  # Penalize extreme timing differences
        
        mistake_score = min(1.0, self.session_analytics['mistakes_made'] / max(1, total_activities * 0.05))  # 5% mistake rate is optimal
        
        self.performance_metrics['human_likeness_score'] = (timing_score + mistake_score) / 2
    
    def generate_session_report(self):
        """Generate a comprehensive session analytics report"""
        session_duration = time.time() - self.session_analytics['start_time']
        
        report = {
            'session_summary': {
                'duration_minutes': session_duration / 60,
                'total_activities': self.session_analytics['total_activities'],
                'activities_per_minute': self.session_analytics['total_activities'] / (session_duration / 60),
                'efficiency_score': self.session_analytics['efficiency_score'],
                'mistakes_made': self.session_analytics['mistakes_made'],
                'patterns_avoided': self.session_analytics['patterns_avoided'],
                'interruptions': self.session_analytics['interruptions']
            },
            'activity_breakdown': self.session_analytics['activity_breakdown'],
            'performance_metrics': self.performance_metrics,
            'human_behavior_analysis': {
                'fatigue_progression': f"Started: 0.0, Current: {self.fatigue_level:.2f}",
                'focus_stability': f"Current: {self.focus_level:.2f}",
                'movement_style': self.movement_style,
                'personal_quirks': {
                    'mistake_frequency': f"{self.mistake_frequency:.2f}",
                    'distraction_proneness': f"{self.distraction_proneness:.2f}"
                }
            },
            'anti_detection_analysis': {
                'timing_jitter_base': f"{self.timing_jitter_base:.2f}",
                'micro_delay_signature': f"{self.micro_delay_signature:.3f}",
                'pattern_avoidance_active': self.repetition_count < self.pattern_detection_threshold,
                'behavioral_fingerprint': f"Movement: {self.movement_style}, Precision: {self.mouse_precision:.2f}"
            }
        }
        
        return report
    
    def adaptive_learning(self):
        """Adapt behavior based on session performance"""
        if self.session_analytics['total_activities'] < 10:
            return  # Need more data for learning
        
        # Analyze current performance
        human_likeness = self.performance_metrics['human_likeness_score']
        
        # If we're being too robotic, increase randomness
        if human_likeness < 0.6:
            self.timing_jitter_base *= random.uniform(1.1, 1.3)
            self.mistake_frequency *= random.uniform(1.2, 1.5)
        
        # If we're being too chaotic, stabilize a bit
        elif human_likeness > 0.9:
            self.timing_jitter_base *= random.uniform(0.8, 0.9)
            self.mistake_frequency *= random.uniform(0.7, 0.9)
        
        # Adapt activity weights based on success
        self.analyze_activity_patterns()
    
    def get_intelligence_adjusted_weights(self, base_weights):
        """Apply intelligent adjustments to activity weights"""
        adjusted_weights = []
        
        activities = ["mouse_movement", "mouse_click", "navigation", "tab_switching", 
                     "scroll_wheel", "text_selection", "copy_paste", "hover_behavior"]
        
        for i, activity in enumerate(activities):
            if i < len(base_weights):
                adaptive_multiplier = self.adaptive_weights.get(activity, 1.0)
                adjusted_weight = base_weights[i] * adaptive_multiplier
                adjusted_weights.append(adjusted_weight)
            else:
                adjusted_weights.append(0.0)
        
        return adjusted_weights
    
    def get_current_screen_bounds(self):
        """Get the bounds of the main screen only"""
        try:
            # MacBook Pro 15-inch 2018 Retina Display (2880 × 1800)
            screen_x, screen_y = 0, 0
            screen_width, screen_height = 2880, 1800
            return screen_x, screen_y, screen_width, screen_height
                
        except Exception as e:
            # Fallback to MacBook Pro Retina resolution
            return 0, 0, 2880, 1800
    
    def get_safe_zone(self):
        """Get safe zone coordinates for the current screen only"""
        # Get current screen bounds
        screen_x, screen_y, screen_width, screen_height = self.get_current_screen_bounds()
        
        # Define safe zones (avoid edges, title bars, close buttons, etc.)
        margin = 100  # Safe margin from edges
        
        # Calculate safe zone within current screen
        safe_x_min = screen_x + margin
        safe_x_max = screen_x + screen_width - margin
        safe_y_min = screen_y + margin + 50  # Extra margin from top
        safe_y_max = screen_y + screen_height - margin - 50  # Extra margin from bottom
        
        return safe_x_min, safe_x_max, safe_y_min, safe_y_max
    
    def clamp_to_main_screen(self, x, y):
        """Ensure mouse position stays within MacBook Pro Retina display boundaries"""
        # MacBook Pro 15-inch Retina bounds: (0, 0) to (2880, 1800)
        # Add extra safety margin to prevent any edge cases
        clamped_x = max(50, min(2830, x))  # Extra margin from edges
        clamped_y = max(50, min(1750, y))  # Extra margin from edges
        return clamped_x, clamped_y
    
    def force_mouse_to_main_screen(self):
        """Force mouse back to MacBook Pro Retina display if it's outside boundaries"""
        try:
            current_x, current_y = pyautogui.position()
            
            # MacBook Pro 15-inch Retina boundaries: (0, 0) to (2880, 1800)
            main_screen_width = 2880
            main_screen_height = 1800
            
            # If mouse is beyond main screen boundaries, move it back
            if current_x < 0 or current_x >= main_screen_width or current_y < 0 or current_y >= main_screen_height:
                # Move to center of main screen
                center_x = main_screen_width // 2  # 1440
                center_y = main_screen_height // 2  # 900
                pyautogui.moveTo(center_x, center_y, duration=0.1)
                return True
            else:
                return False
        except Exception as e:
            return False
    
    def validate_mouse_position(self, x, y):
        """Validate that mouse position is within MacBook Pro Retina display boundaries"""
        # MacBook Pro 15-inch Retina boundaries: (0, 0) to (2880, 1800)
        main_screen_width = 2880
        main_screen_height = 1800
        
        if x < 0 or x >= main_screen_width or y < 0 or y >= main_screen_height:
            return False
        return True
    
    def safe_move_to(self, x, y, duration=0.1):
        """Safely move mouse to position with HARD boundary enforcement for MacBook Pro Retina"""
        # MacBook Pro 15-inch Retina boundaries: (0, 0) to (2880, 1800)
        main_screen_width = 2880
        main_screen_height = 1800
        
        # HARD BOUNDARY CHECK - force coordinates to stay within main screen
        if x < 0 or x >= main_screen_width or y < 0 or y >= main_screen_height:
            # Force to center of main screen
            safe_x = main_screen_width // 2  # 1440
            safe_y = main_screen_height // 2  # 900
            pyautogui.moveTo(safe_x, safe_y, duration=duration)
            return safe_x, safe_y
        else:
            # Position is valid, move normally
            pyautogui.moveTo(x, y, duration=duration)
            return x, y
    
    def simulate_mouse_movement(self, pattern="coding"):
        """Simulate realistic mouse movements within safe zones"""
        if not self.is_running:
            return "Stopped"
        
        # Force mouse back to main screen if needed
        self.force_mouse_to_main_screen()
            
        try:
            # Get pattern-specific frequency
            frequency = self.config["activity_patterns"][pattern]["mouse_movement_frequency"]
            
            if random.random() > frequency:
                return "Skipped (low frequency)"
            
            # Get safe zone boundaries
            safe_x_min, safe_x_max, safe_y_min, safe_y_max = self.get_safe_zone()
            
            # Generate realistic mouse path within safe zone
            current_x, current_y = pyautogui.position()
            
            # Ensure current position is in safe zone
            current_x = max(safe_x_min, min(safe_x_max, current_x))
            current_y = max(safe_y_min, min(safe_y_max, current_y))
            
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
            
            # Execute the chosen movement pattern
            for _ in range(num_moves):
                if not self.is_running:
                    break
                    
                if movement_type == "large_move":
                    # For large moves, go to completely random positions
                    target_x = random.randint(safe_x_min, safe_x_max)
                    target_y = random.randint(safe_y_min, safe_y_max)
                    
                    # PRE-MOVEMENT BOUNDARY CHECK - ensure target is within main screen
                    main_screen_width = 2880
                    main_screen_height = 1800
                    
                    if target_x < 0 or target_x >= main_screen_width or target_y < 0 or target_y >= main_screen_height:
                        # Force target to center of main screen
                        target_x = main_screen_width // 2  # 1440
                        target_y = main_screen_height // 2  # 900
                else:
                    # Calculate next position (within safe bounds)
                    target_x = max(safe_x_min, min(safe_x_max, 
                                         current_x + random.randint(-max_move, max_move)))
                    target_y = max(safe_y_min, min(safe_y_max, 
                                         current_y + random.randint(-max_move, max_move)))
                    
                    # PRE-MOVEMENT BOUNDARY CHECK - ensure target is within main screen
                    main_screen_width = 2880
                    main_screen_height = 1800
                    
                    if target_x < 0 or target_x >= main_screen_width or target_y < 0 or target_y >= main_screen_height:
                        # Force target to center of main screen
                        target_x = main_screen_width // 2  # 1440
                        target_y = main_screen_height // 2  # 900
                
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
                    
                    # Double-check: clamp to main screen boundaries
                    x, y = self.clamp_to_main_screen(x, y)
                    
                    # Use safe move function to validate position
                    x, y = self.safe_move_to(x, y, duration=random.uniform(0.01, 0.05))
                    
                    # Double-check mouse is still on main screen after movement
                    current_pos = pyautogui.position()
                    main_screen_width = 2880
                    main_screen_height = 1800
                    if (current_pos[0] < 0 or current_pos[0] >= main_screen_width or 
                        current_pos[1] < 0 or current_pos[1] >= main_screen_height):
                        # Force back to safe position
                        safe_x = main_screen_width // 2  # 1440
                        safe_y = main_screen_height // 2  # 900
                        pyautogui.moveTo(safe_x, safe_y, duration=0.1)
                    
                    time.sleep(random.uniform(0.01, 0.03))
                
                current_x, current_y = target_x, target_y
                time.sleep(random.uniform(0.1, 0.3))
            
            return f"{movement_type} ({num_moves} moves, max {max_move}px)"
        
        except Exception as e:
            if not self.handle_error(e, "mouse_movement"):
                return "Error occurred"
            return "Error handled"
    
    def simulate_scroll_wheel(self):
        """Simulate realistic scroll wheel behavior"""
        if not self.is_running:
            return "Stopped"
        
        # Force mouse back to main screen if needed
        self.force_mouse_to_main_screen()
            
        try:
            # Get safe zone boundaries
            safe_x_min, safe_x_max, safe_y_min, safe_y_max = self.get_safe_zone()
        
            # Move to a random safe position before scrolling
            safe_x = random.randint(safe_x_min, safe_x_max)
            safe_y = random.randint(safe_y_min, safe_y_max)
            
            # Use safe move function to validate position
            safe_x, safe_y = self.safe_move_to(safe_x, safe_y, duration=random.uniform(0.1, 0.3))
            
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
                    pyautogui.scroll(scroll_direction * random.randint(1, 3))
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
                        pyautogui.scroll(direction * random.randint(2, 4))
                        time.sleep(random.uniform(0.05, 0.1))
                    time.sleep(random.uniform(0.2, 0.5))
                    
            elif scroll_pattern == "slow_scroll":
                # Slow deliberate scrolling
                scroll_direction = random.choice([1, -1])
                scroll_amount = random.randint(5, 12)
                for _ in range(scroll_amount):
                    if not self.is_running:
                        break
                    pyautogui.scroll(scroll_direction * 1)  # Single unit scrolls
                    time.sleep(random.uniform(0.3, 0.8))
                    
            elif scroll_pattern == "mixed_scroll":
                # Mix of up and down scrolling
                total_scrolls = random.randint(6, 15)
                for _ in range(total_scrolls):
                    if not self.is_running:
                        break
                    direction = random.choice([1, -1])
                    amount = random.randint(1, 3)
                    pyautogui.scroll(direction * amount)
                    time.sleep(random.uniform(0.1, 0.4))
                    
            else:  # page_scroll
                # Large scroll amounts (page-like)
                num_pages = random.randint(1, 3)
                for _ in range(num_pages):
                    if not self.is_running:
                        break
                    direction = random.choice([1, -1])
                    # Large scroll amounts to simulate page scrolling
                    pyautogui.scroll(direction * random.randint(8, 15))
                    time.sleep(random.uniform(0.5, 1.2))
            
            time.sleep(random.uniform(0.2, 0.8))
            return f"Scrolled using {scroll_pattern} pattern"
            
        except Exception as e:
            if not self.handle_error(e, "scroll_wheel"):
                return "Error occurred"
            return "Error handled"
    
    
    def simulate_cursor_sidebar_toggle(self):
        """Simulate toggling Cursor's sidebar (Cmd+B)"""
        if not self.is_running:
            return
            
        try:
            # Simulate sidebar toggle without keyboard shortcuts
            
            # Brief pause for sidebar animation
            time.sleep(random.uniform(0.5, 1.2))
            
            # 50% chance to toggle it back after a short delay
            if random.random() < 0.5:
                time.sleep(random.uniform(1.0, 3.0))
                time.sleep(random.uniform(0.3, 0.8))
                
        except Exception as e:
            if not self.handle_error(e, "cursor_sidebar_toggle"):
                return
    
    def simulate_text_selection(self):
        """Simulate realistic text selection behaviors"""
        if not self.is_running:
            return "Stopped"
            
        try:
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
                pyautogui.moveTo(start_x, start_y, duration=self.get_human_adjusted_delay(0.3))
                
                # Start drag
                pyautogui.mouseDown()
                
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
                    
                    pyautogui.moveTo(current_x + tremor_x, current_y + tremor_y, 
                                   duration=self.get_human_adjusted_delay(0.02))
                
                pyautogui.mouseUp()
                
            elif selection_type == "double_click":
                # Double-click to select word
                click_x = random.randint(safe_x_min + 100, safe_x_max - 100)
                click_y = random.randint(safe_y_min + 100, safe_y_max - 100)
                
                pyautogui.moveTo(click_x, click_y, duration=self.get_human_adjusted_delay(0.3))
                time.sleep(self.get_human_adjusted_delay(0.1))
                pyautogui.doubleClick()
                
            elif selection_type == "triple_click":
                # Triple-click to select line
                click_x = random.randint(safe_x_min + 100, safe_x_max - 100)
                click_y = random.randint(safe_y_min + 100, safe_y_max - 100)
                
                pyautogui.moveTo(click_x, click_y, duration=self.get_human_adjusted_delay(0.3))
                time.sleep(self.get_human_adjusted_delay(0.1))
                pyautogui.click()
                time.sleep(self.get_human_adjusted_delay(0.05))
                pyautogui.click()
                time.sleep(self.get_human_adjusted_delay(0.05))
                pyautogui.click()
                
            elif selection_type == "shift_click":
                # Click, then Shift+click for range selection
                start_x = random.randint(safe_x_min + 100, safe_x_max - 200)
                start_y = random.randint(safe_y_min + 100, safe_y_max - 100)
                
                # First click
                pyautogui.moveTo(start_x, start_y, duration=self.get_human_adjusted_delay(0.3))
                pyautogui.click()
                
                # Move to end position
                end_x = start_x + random.randint(100, 400)
                end_y = start_y + random.randint(-50, 100)
                end_x = max(safe_x_min, min(safe_x_max, end_x))
                end_y = max(safe_y_min, min(safe_y_max, end_y))
                
                time.sleep(self.get_human_adjusted_delay(0.5))
                pyautogui.moveTo(end_x, end_y, duration=self.get_human_adjusted_delay(0.4))
                
                # Shift+click
                pyautogui.click(button='left', clicks=1, interval=0, _pause=False)
                
            
            time.sleep(self.get_human_adjusted_delay(random.uniform(0.3, 1.0)))
            return f"Selected text using {selection_type}"
            
        except Exception as e:
            if not self.handle_error(e, "text_selection"):
                return "Error occurred"
            return "Error handled"
    
    def simulate_copy_paste_workflow(self):
        """Simulate realistic copy-paste workflows"""
        if not self.is_running:
            return "Stopped"
            
        try:
            # First, select some text
            self.simulate_text_selection()
            
            # Brief pause (reading selected text)
            time.sleep(self.get_human_adjusted_delay(random.uniform(0.2, 0.8)))
            
            # Simulate copy/paste workflow without keyboard shortcuts
            
            # Pause (thinking about where to paste)
            time.sleep(self.get_human_adjusted_delay(random.uniform(0.5, 2.0)))
            
            # Move to a different location
            safe_x_min, safe_x_max, safe_y_min, safe_y_max = self.get_safe_zone()
            paste_x = random.randint(safe_x_min + 100, safe_x_max - 100)
            paste_y = random.randint(safe_y_min + 100, safe_y_max - 100)
            
            pyautogui.moveTo(paste_x, paste_y, duration=self.get_human_adjusted_delay(0.5))
            pyautogui.click()
            
            # Simulate paste action without keyboard shortcuts
            time.sleep(self.get_human_adjusted_delay(random.uniform(0.1, 0.5)))
            
            time.sleep(self.get_human_adjusted_delay(random.uniform(0.3, 1.0)))
            return "Completed copy-paste workflow"
            
        except Exception as e:
            if not self.handle_error(e, "copy_paste_workflow"):
                return "Error occurred"
            return "Error handled"
    
    def simulate_hover_behavior(self):
        """Simulate realistic hover behaviors (reading tooltips, etc.)"""
        if not self.is_running:
            return "Stopped"
            
        try:
            safe_x_min, safe_x_max, safe_y_min, safe_y_max = self.get_safe_zone()
            
            # Move to a random position
            hover_x = random.randint(safe_x_min + 50, safe_x_max - 50)
            hover_y = random.randint(safe_y_min + 50, safe_y_max - 50)
            
            # Move with slightly slower, more deliberate movement
            pyautogui.moveTo(hover_x, hover_y, duration=self.get_human_adjusted_delay(0.8))
            
            # Hover for a realistic amount of time (reading tooltip/info)
            hover_duration = self.get_human_adjusted_delay(random.uniform(0.5, 2.5))
            time.sleep(hover_duration)
            
            # Small micro-movements while hovering (natural hand tremor)
            for _ in range(random.randint(1, 4)):
                if not self.is_running:
                    break
                micro_x = hover_x + random.uniform(-3, 3)
                micro_y = hover_y + random.uniform(-3, 3)
                pyautogui.moveTo(micro_x, micro_y, duration=0.1)
                time.sleep(0.1)
            
            return f"Hovered for {hover_duration:.1f}s"
            
        except Exception as e:
            if not self.handle_error(e, "hover_behavior"):
                return "Error occurred"
            return "Error handled"
    
    def get_work_rhythm_pattern(self, duration_minutes):
        """Get natural work rhythm pattern based on duration and time of day"""
        current_hour = datetime.now().hour
        
        # Define work rhythm patterns
        if duration_minutes <= 5:
            # Short sessions - high focus
            return {
                "pattern": "short_focus",
                "focus_level": "high",
                "break_frequency": "minimal",
                "activity_variation": 0.1
            }
        elif duration_minutes <= 15:
            # Medium sessions - moderate focus with breaks
            return {
                "pattern": "medium_focus",
                "focus_level": "moderate",
                "break_frequency": "light",
                "activity_variation": 0.2
            }
        elif duration_minutes <= 30:
            # Long sessions - natural rhythm with breaks
            return {
                "pattern": "long_focus",
                "focus_level": "moderate",
                "break_frequency": "normal",
                "activity_variation": 0.3
            }
        else:
            # Very long sessions - extended work with regular breaks
            return {
                "pattern": "extended_work",
                "focus_level": "variable",
                "break_frequency": "regular",
                "activity_variation": 0.4
            }
    
    def apply_work_rhythm_effects(self, base_scale, work_rhythm, minute_num, total_minutes):
        """Apply work rhythm effects to activity scale"""
        # Apply focus level effects
        if work_rhythm["focus_level"] == "high":
            focus_multiplier = random.uniform(1.0, 1.2)
        elif work_rhythm["focus_level"] == "moderate":
            focus_multiplier = random.uniform(0.8, 1.1)
        elif work_rhythm["focus_level"] == "variable":
            # Variable focus - changes throughout the session
            progress = minute_num / total_minutes
            if progress < 0.3:  # Start strong
                focus_multiplier = random.uniform(1.0, 1.2)
            elif progress < 0.7:  # Middle steady
                focus_multiplier = random.uniform(0.9, 1.1)
            else:  # End with some fatigue
                focus_multiplier = random.uniform(0.7, 1.0)
        else:
            focus_multiplier = 1.0
        
        # Apply break frequency effects
        if work_rhythm["break_frequency"] == "minimal":
            break_chance = 0.05
        elif work_rhythm["break_frequency"] == "light":
            break_chance = 0.1
        elif work_rhythm["break_frequency"] == "normal":
            break_chance = 0.15
        elif work_rhythm["break_frequency"] == "regular":
            break_chance = 0.2
        else:
            break_chance = 0.1
        
        # Check if this minute should be a break
        if random.random() < break_chance:
            return max(1, int(base_scale * 0.3))  # Very low activity during breaks
        
        # Apply focus multiplier with variation
        adjusted_scale = base_scale * focus_multiplier
        variation = work_rhythm["activity_variation"]
        final_scale = adjusted_scale + random.uniform(-variation, variation) * base_scale
        
        return max(1, min(10, int(final_scale)))
    
    def simulate_tab_switching(self):
        """Actually switch between tabs in Cursor using keyboard shortcuts and mouse clicks"""
        if not self.is_running:
            return
            
        # High activity: much more frequent tab switching (70% chance per activity)
        if random.random() > 0.7:
            return
            
        # High activity: more tab switches per session (1-5 switches)
        num_switches = random.randint(1, 5)
        
        for _ in range(num_switches):
            if not self.is_running:
                break
                
            # Choose switching method randomly
            switch_method = random.choice([
                "keyboard_shortcut",  # Use Ctrl+Tab, Ctrl+Shift+Tab
                "mouse_click"         # Click on actual tabs
            ])
            
            if switch_method == "keyboard_shortcut":
                # Use keyboard shortcuts for tab switching
                shortcut_type = random.choice([
                    "next_tab",      # Ctrl+Tab (next tab)
                    "prev_tab",      # Ctrl+Shift+Tab (previous tab)
                    "alt_tab"        # Alt+Tab (application switching)
                ])
                
                if shortcut_type == "next_tab":
                    pyautogui.hotkey('ctrl', 'tab')
                elif shortcut_type == "prev_tab":
                    pyautogui.hotkey('ctrl', 'shift', 'tab')
                elif shortcut_type == "alt_tab":
                    pyautogui.hotkey('alt', 'tab')
                    time.sleep(random.uniform(0.1, 0.3))
                    pyautogui.hotkey('alt', 'tab')  # Switch back to Cursor
                    
            else:  # mouse_click
                # Click on actual tabs in Cursor's interface
                self.click_on_tab()
            
            # Random delay between switches
            if num_switches > 1:
                time.sleep(random.uniform(0.3, 1.0))
        
        # Very rare chance to close a tab (1 tab per hour frequency)
        if random.random() < 0.01:  # 1% chance per tab switching session
            self.close_random_tab()
        
        time.sleep(random.uniform(0.5, 2.0))  # Random delay after tab switching
        return f"Switched {num_switches} tabs"
    
    def click_on_tab(self):
        """Click on a random tab in Cursor's tab bar"""
        if not self.is_running:
            return
            
        try:
            # Get safe zone boundaries
            safe_x_min, safe_x_max, safe_y_min, safe_y_max = self.get_safe_zone()
            
            # Tab bar is typically at the top of the window
            # Calculate tab bar area (top 10% of safe zone)
            tab_bar_height = int((safe_y_max - safe_y_min) * 0.1)
            tab_bar_y_min = safe_y_min
            tab_bar_y_max = safe_y_min + tab_bar_height
            
            # Tab bar width (most of the safe zone width)
            tab_bar_x_min = safe_x_min + 50  # Leave some margin
            tab_bar_x_max = safe_x_max - 50
            
            # Click on a random position in the tab bar
            tab_x = random.randint(tab_bar_x_min, tab_bar_x_max)
            tab_y = random.randint(tab_bar_y_min, tab_bar_y_max)
            
            # Move to tab and click
            pyautogui.moveTo(tab_x, tab_y, duration=random.uniform(0.2, 0.5))
            time.sleep(random.uniform(0.1, 0.3))
            pyautogui.click()
            
            
        except Exception as e:
            if not self.handle_error(e, "click_on_tab"):
                return
    
    def close_random_tab(self):
        """Close a random tab (very low frequency - 1 per hour)"""
        if not self.is_running:
            return
            
        try:
            # Get safe zone boundaries
            safe_x_min, safe_x_max, safe_y_min, safe_y_max = self.get_safe_zone()
            
            # Tab bar area
            tab_bar_height = int((safe_y_max - safe_y_min) * 0.1)
            tab_bar_y_min = safe_y_min
            tab_bar_y_max = safe_y_min + tab_bar_height
            
            # Look for close button (X) on the right side of tabs
            # Close buttons are typically on the right side of each tab
            close_x_min = safe_x_max - 200  # Right side of safe zone
            close_x_max = safe_x_max - 20   # Near the edge
            close_y_min = tab_bar_y_min
            close_y_max = tab_bar_y_max
            
            # Click on close button area
            close_x = random.randint(close_x_min, close_x_max)
            close_y = random.randint(close_y_min, close_y_max)
            
            # Move to close button and click
            pyautogui.moveTo(close_x, close_y, duration=random.uniform(0.3, 0.6))
            time.sleep(random.uniform(0.2, 0.4))
            pyautogui.click()
            
            
            # Brief pause after closing tab
            time.sleep(random.uniform(0.5, 1.5))
            
        except Exception as e:
            if not self.handle_error(e, "close_random_tab"):
                return

    def simulate_mouse_clicks(self, scale=5):
        """Simulate completely random mouse clicks in safe zones"""
        if not self.is_running:
            return "Stopped"
        
        # Force mouse back to main screen if needed
        self.force_mouse_to_main_screen()
            
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
            
            # Double-check: clamp to main screen boundaries
            safe_x, safe_y = self.clamp_to_main_screen(safe_x, safe_y)
            
            # Use safe move function to validate position
            safe_x, safe_y = self.safe_move_to(safe_x, safe_y, duration=random.uniform(0.1, 0.3))
            
            # Double-check mouse is still on main screen after movement
            current_pos = pyautogui.position()
            main_screen_width = 2880
            main_screen_height = 1800
            if (current_pos[0] < 0 or current_pos[0] >= main_screen_width or 
                 current_pos[1] < 0 or current_pos[1] >= main_screen_height):
                 
                print(f"🚨 Mouse escaped during click movement! Current: {current_pos}, Main screen: 0-{main_screen_width}, 0-{main_screen_height}")
                # Force back to safe position
                safe_x = main_screen_width // 2  # 1440
                safe_y = main_screen_height // 2  # 900
                pyautogui.moveTo(safe_x, safe_y, duration=0.1)
                print(f"✅ Mouse forced back to main screen center: ({safe_x}, {safe_y})")
            
            # Completely random click type selection (avoid dangerous clicks)
            click_types = ["left", "left", "left", "double"]  # Mostly left clicks, some double
            # Removed right-click and middle-click to avoid context menus
            click_type = random.choice(click_types)
            
            if click_type == "left":
                pyautogui.click()
            elif click_type == "double":
                pyautogui.doubleClick()
            
            
            # Random delay between multiple clicks
            if num_clicks > 1:
                time.sleep(random.uniform(0.05, 0.3))
        
        time.sleep(random.uniform(0.1, 1.0))  # Random delay after all clicks
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
            
            # Press the key
            pyautogui.press(key)
            
            # Random delay between key presses
            if num_keys > 1:
                time.sleep(random.uniform(0.1, 0.4))
        
        time.sleep(random.uniform(0.2, 0.8))  # Random delay after all key presses
        return f"Pressed {num_keys} keys: {', '.join(keys_pressed)}"
    
    def simulate_idle_period(self):
        """Simulate idle periods (no activity)"""
        if not self.is_running:
            return
            
        duration = random.uniform(
            self.config["idle_periods"]["min_duration"],
            self.config["idle_periods"]["max_duration"]
        )
        
        time.sleep(duration)
    
    def simulate_activity_scale(self, scale, duration_minutes=10):
        """Simulate activity based on scale 7-9 with scattered idle/active minutes"""
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        # Calculate idle vs active minutes based on scale
        idle_minutes = 10 - scale  # Scale 7=3 idle, Scale 9=1 idle
        active_minutes = scale     # Scale 7=7 active, Scale 9=9 active
        
        # Generate scattered idle/active pattern for this 10-minute window
        all_minutes = list(range(10))
        idle_minute_positions = random.sample(all_minutes, idle_minutes)
        
                # Suppressed detailed pattern log
        
        # Execute each minute of the 10-minute window
        for minute_num in range(10):
            if not self.is_running:
                break
            
            # Check for kill switch
            if self.check_kill_switch():
                break
            
            # Force mouse back to main screen at start of each minute
            self.force_mouse_to_main_screen()
                
            minute_start = time.time()
            minute_end = min(minute_start + 60, end_time)
            
            # Check if this minute should be idle or active
            is_idle_minute = minute_num in idle_minute_positions
        
            
            if is_idle_minute:
                # Suppressed idle minute detail
                # Skip all activities for idle minutes
                time.sleep(60)  # Wait 1 minute doing nothing
                continue
            else:
                # Suppressed active minute detail
                # High-activity levels for 40-100 activities per minute
                # Scale 7: 40-70, Scale 8: 70-85, Scale 9: 85-100
                
                if scale == 7:
                    target_activities = random.randint(random.randint(17, 25), random.randint(33,40))  # Medium-high activity
                elif scale == 8:
                    target_activities = random.randint(random.randint(33, 47), random.randint(47,55))  # High activity
                else:  # scale == 9
                    target_activities = random.randint(random.randint(47, 55), random.randint(65,75))  # Very high activity
                
                activities_performed = 0
                
                # Apply time-based and human-state modifiers
                time_modifier = self.get_time_based_activity_modifier()
                work_intensity = self.get_work_intensity_schedule()
                
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
                
                # Apply modifiers to weights
                modified_weights = [w * time_modifier * work_intensity for w in base_weights]
                
                # Apply intelligent adjustments
                activity_weights = self.get_intelligence_adjusted_weights(modified_weights)
                
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
                
                while seconds_used < max_active_seconds and time.time() < minute_end and self.is_running and activities_performed < target_activities:
                    # Check for kill switch
                    if self.check_kill_switch():
                        break
                        
                    # Choose activity with anti-detection
                    candidate_activity = random.choices(
                        ["mouse_movement", "mouse_click", "navigation", "tab_switching", "scroll_wheel", "text_selection", "copy_paste", "hover_behavior"],
                        weights=activity_weights
                    )[0]
                    
                    # Apply anti-detection pattern avoidance
                    activity = self.avoid_repetitive_patterns(candidate_activity)
                    
                    # Update activity history
                    self.activity_history.append(activity)
                    self.last_activity_type = activity
                    activities_performed += 1
                    
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
                    elif activity == "tab_switching":
                        result = self.simulate_tab_switching()
                        print(f"    🔄 Tab Switch: {result}")
                    elif activity == "scroll_wheel":
                        result = self.simulate_scroll_wheel()
                        print(f"    📜 Scroll: {result}")
                    elif activity == "text_selection":
                        result = self.simulate_text_selection()
                        print(f"    📝 Text Selection: {result}")
                    elif activity == "copy_paste":
                        result = self.simulate_copy_paste_workflow()
                        print(f"    📋 Copy/Paste: {result}")
                    elif activity == "hover_behavior":
                        result = self.simulate_hover_behavior()
                        print(f"    🎯 Hover: {result}")
                    
                    # Occasionally toggle sidebar (5% chance during any activity)
                    if random.random() < 0.05:
                        self.simulate_cursor_sidebar_toggle()
                    
                    # Simulate human mistakes occasionally
                    if random.random() < self.mistake_frequency:
                        self.simulate_human_mistakes()
                        self.session_analytics['mistakes_made'] += 1
                    
                    # Add natural interruptions
                    self.add_natural_interruptions()
                    
                    # Update consecutive active minutes
                    self.consecutive_active_minutes += 1
                    self.last_activity_time = time.time()
                    
                    activity_duration = time.time() - activity_start
                    
                    # Update performance metrics
                    self.update_performance_metrics(activity, activity_duration)
                    seconds_used += activity_duration
                    
                    # Random delay between activities (reduced for high activity)
                    if seconds_used < max_active_seconds and activities_performed < target_activities:
                        base_delay = random.uniform(0.02, 0.3)  # Much shorter delays
                        human_delay = self.get_human_adjusted_delay(base_delay)
                        final_delay = self.add_anti_detection_jitter(human_delay)
                        time.sleep(final_delay)
                    
                    # Adaptive learning every 20 activities
                    if self.session_analytics['total_activities'] % 20 == 0:
                        self.adaptive_learning()
                
                # Check if break is needed
                if self.should_take_break():
                    self.simulate_micro_break()
                
                # Wait for the minute to complete
                remaining_time = minute_end - time.time()
                if remaining_time > 0:
                    time.sleep(remaining_time)
                
        
    
    def start_tracking(self, duration_hours=1):
        """Start the main tracking loop with 10-minute windows and activity scales"""
        self.is_running = True
        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)
        
        # Initialize analytics and intelligence systems
        self.initialize_analytics()
        
        # Precompute safe zone info (no verbose logging)
        safe_x_min, safe_x_max, safe_y_min, safe_y_max = self.get_safe_zone()
        screen_x, screen_y, screen_width, screen_height = self.get_current_screen_bounds()

        print(f"Starting user activity tracking for {duration_hours} hours...")
        print("Each hour is split into 6 windows of 10 minutes each")
        print("Activity scale: 1=idle, 10=very active (random 7-9)")
        print("=" * 60)
        # Suppressed safety/screen logs
        print("🛑 STOP METHODS:")
        print("   • Press 'q' key to quit")
        print("   • Press 'Cmd+Shift+Q' (macOS shortcut)")
        print("   • Create kill switch file: touch STOP_TRACKER.txt")
        print("   • Use Ctrl+C if keyboard listener fails")
        
        # Start keyboard listener in separate thread (optional - may fail on macOS)
        try:
            keyboard_thread = threading.Thread(target=self.keyboard_listener)
            keyboard_thread.daemon = True
            keyboard_thread.start()
            print("✅ Keyboard listener started (Press 'q' to quit)")
        except Exception as e:
            print("⚠️  Keyboard listener disabled (requires admin privileges)")
            print("   Use Ctrl+C to stop the tracker")
            print(f"   Error: {e}")
        
        try:
            current_time = start_time
            window_count = 0
            
            while current_time < end_time and self.is_running:
                # Check for kill switch
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
                    if not self.handle_error(e, f"window_{window_count}"):
                        break
                
                # Move to next window
                current_time = window_end
                
                # Small break between windows
                if self.is_running and current_time < end_time:
                    time.sleep(random.uniform(2, 5))
                    
        except KeyboardInterrupt:
            print("\nTracking interrupted by user")
        except Exception as e:
            if not self.handle_error(e, "start_tracking"):
                print("Fatal error in tracking, stopping...")
        
        self.stop_tracking()
    
    def keyboard_listener(self):
        """Listen for keyboard shortcuts to stop tracking"""
        try:
            while self.is_running:
                # Check for 'q' key (simple)
                if keyboard.is_pressed('q'):
                    print("\n🛑 'Q' key pressed - Stopping tracking...")
                    self.is_running = False
                    break
                
                # Check for Cmd+Shift+Q (macOS shortcut)
                if (keyboard.is_pressed('cmd') and 
                    keyboard.is_pressed('shift') and 
                    keyboard.is_pressed('q')):
                    print("\n🛑 Cmd+Shift+Q pressed - Stopping tracking...")
                    self.is_running = False
                    break
                
                time.sleep(0.1)
        except OSError as e:
            if "Must be run as administrator" in str(e) or "Error 13" in str(e):
                print("⚠️  Keyboard listener disabled (requires admin permissions)")
                print("   Use Ctrl+C or the kill switch file to stop the tracker")
            else:
                print(f"⚠️  Keyboard listener disabled: {e}")
                print("   Use Ctrl+C or the kill switch file to stop the tracker")
        except Exception as e:
            print(f"⚠️  Keyboard listener disabled: {e}")
            print("   Use Ctrl+C or the kill switch file to stop the tracker")
        
        # Keep thread alive but inactive
        while self.is_running:
            time.sleep(1)
    
    def stop_tracking(self):
        """Stop the tracking and save logs"""
        self.is_running = False
        
        # Clean exit without analytics report
        print("✅ Tracking session completed successfully")
    
    def run_quick_test(self, minutes=5):
        """Run a quick test tracking"""
        print(f"Running quick test for {minutes} minutes...")
        self.start_tracking(duration_hours=minutes/60)

def main():
    import sys
    
    tracker = ActivityTracker()
    
    print("Activity Tracker")
    print("=" * 50)
    print("Activity Scale System:")
    print("- Each hour = 6 windows of 10 minutes each")
    print("- Activity scale: 1=idle, 10=very active")
    print("- Random scale: 7-9 for each window")
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
            print("\nNo input available. Use: python activity-tracker.py <hours>")
            break

if __name__ == "__main__":
    main()
