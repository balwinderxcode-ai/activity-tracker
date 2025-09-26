#!/usr/bin/env python3
"""
Debug version of Activity Tracker to identify duration issues
"""

import sys
import time
from datetime import datetime

def debug_main():
    print("🔍 DEBUG: Activity Tracker")
    print("=" * 50)
    print(f"Command line arguments: {sys.argv}")
    print(f"Number of arguments: {len(sys.argv)}")
    
    if len(sys.argv) > 1:
        try:
            hours = float(sys.argv[1])
            print(f"✅ Hours parsed successfully: {hours}")
            print(f"✅ Duration in seconds: {hours * 3600}")
            print(f"✅ Duration in minutes: {hours * 60}")
            
            # Simulate the tracking logic
            start_time = time.time()
            end_time = start_time + (hours * 3600)
            
            print(f"✅ Start time: {datetime.fromtimestamp(start_time).strftime('%H:%M:%S')}")
            print(f"✅ End time: {datetime.fromtimestamp(end_time).strftime('%H:%M:%S')}")
            print(f"✅ Expected duration: {hours} hours")
            
            # Calculate windows
            windows = int(hours * 6)
            print(f"✅ Expected windows: {windows}")
            
            # Test the loop logic
            current_time = start_time
            window_count = 0
            
            print(f"\n🔄 Testing loop logic:")
            while current_time < end_time and window_count < 5:  # Limit to 5 windows for testing
                window_start = current_time
                window_end = min(current_time + 600, end_time)  # 10 minutes = 600 seconds
                window_duration_minutes = (window_end - window_start) / 60
                
                print(f"  Window {window_count + 1}:")
                print(f"    Start: {datetime.fromtimestamp(window_start).strftime('%H:%M:%S')}")
                print(f"    End: {datetime.fromtimestamp(window_end).strftime('%H:%M:%S')}")
                print(f"    Duration: {window_duration_minutes:.1f} minutes")
                
                current_time = window_end
                window_count += 1
                
                # Simulate some processing time
                time.sleep(0.1)
            
            print(f"\n✅ Loop completed after {window_count} windows")
            print(f"✅ Final time: {datetime.fromtimestamp(current_time).strftime('%H:%M:%S')}")
            print(f"✅ Total elapsed: {(current_time - start_time) / 60:.1f} minutes")
            
        except ValueError as e:
            print(f"❌ Error parsing hours: {e}")
            return
    else:
        print("❌ No arguments provided - would enter interactive mode")
        print("Usage: python3 debug_tracker.py <hours>")

if __name__ == "__main__":
    debug_main()
