#!/usr/bin/env python3
"""
Plot average speed for all running activities from Garmin activity summary files.

This script searches for all *_summary.json files in the activities directory,
filters for running activities (typeKey == "running"), and plots their average speeds
over time.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from pathlib import Path
import argparse


def load_running_activities(activities_dir="activities"):
    """
    Load all running activities from summary.json files.
    
    Args:
        activities_dir (str): Directory containing the activity files
        
    Returns:
        list: List of tuples (datetime, average_speed, activity_name)
    """
    activities = []
    activities_path = Path(activities_dir)
    
    # Find all summary.json files
    summary_files = list(activities_path.glob("*_summary.json"))
    
    if not summary_files:
        raise FileNotFoundError(f"No summary files found in {activities_dir}")
    
    print(f"Found {len(summary_files)} summary files")
    
    running_count = 0
    for file_path in summary_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Check if this is a running activity
            activity_type = data.get("activityTypeDTO", {}).get("typeKey")
            if activity_type != "running":
                continue
                
            running_count += 1
            
            # Extract the timestamp from filename
            timestamp_str = file_path.name.split('_')[0]
            timestamp = datetime.fromisoformat(timestamp_str.replace('T', ' ').replace('+00:00', ''))
            
            # Extract average speed from summaryDTO
            summary_dto = data.get("summaryDTO", {})
            avg_speed = summary_dto.get("averageSpeed")
            
            if avg_speed is not None:
                activity_name = data.get("activityName", "Unknown")
                activities.append((timestamp, avg_speed, activity_name))
            else:
                print(f"Warning: No average speed found for {file_path.name}")
                
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error processing {file_path.name}: {e}")
            continue
    
    print(f"Found {running_count} running activities with speed data")
    
    # Sort by timestamp
    activities.sort(key=lambda x: x[0])
    
    return activities


def plot_running_speeds(activities, output_file=None):
    """
    Plot average speeds over time.
    
    Args:
        activities (list): List of tuples (datetime, average_speed, activity_name)
        output_file (str, optional): File path to save the plot
    """
    if not activities:
        print("No activities to plot")
        return
    
    timestamps, speeds, names = zip(*activities)
    
    # Convert speed from m/s to km/h for better readability
    speeds_kmh = [speed * 3.6 for speed in speeds]
    
    # Create the plot
    plt.figure(figsize=(12, 8))
    
    # Plot the data
    plt.plot(timestamps, speeds_kmh, 'b-o', markersize=4, linewidth=1.5, alpha=0.7)
    
    # Add a trend line
    timestamps_numeric = [ts.timestamp() for ts in timestamps]
    z = np.polyfit(timestamps_numeric, speeds_kmh, 1)
    p = np.poly1d(z)
    plt.plot(timestamps, p(timestamps_numeric), "r--", alpha=0.8, linewidth=2, 
             label=f'Trend: {z[0]:.3f} km/h per day')
    
    # Customize the plot
    plt.title('Running Average Speed Over Time', fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Average Speed (km/h)', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Format x-axis
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Add statistics to the plot
    mean_speed = float(np.mean(speeds_kmh))
    std_speed = float(np.std(speeds_kmh))
    plt.axhline(y=mean_speed, color='green', linestyle=':', alpha=0.7,
                label=f'Mean: {mean_speed:.2f} km/h')
    plt.axhline(y=mean_speed + std_speed, color='orange', linestyle=':', alpha=0.5,
                label=f'+1 STD: {mean_speed + std_speed:.2f} km/h')
    plt.axhline(y=mean_speed - std_speed, color='orange', linestyle=':', alpha=0.5,
                label=f'-1 STD: {mean_speed - std_speed:.2f} km/h')
    
    # Update legend
    plt.legend()
    
    # Print statistics
    print("\nStatistics:")
    print(f"Total activities: {len(activities)}")
    print(f"Mean speed: {mean_speed:.2f} km/h")
    print(f"Standard deviation: {std_speed:.2f} km/h")
    print(f"Min speed: {min(speeds_kmh):.2f} km/h")
    print(f"Max speed: {max(speeds_kmh):.2f} km/h")
    print(f"Speed range: {max(speeds_kmh) - min(speeds_kmh):.2f} km/h")
    
    # Date range
    print(f"Date range: {min(timestamps).date()} to {max(timestamps).date()}")
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {output_file}")
    
    plt.show()


def main():
    parser = argparse.ArgumentParser(description='Plot average speed for running activities')
    parser.add_argument('--activities-dir', default='activities',
                        help='Directory containing activity files (default: activities)')
    parser.add_argument('--output', '-o', help='Output file path for the plot')
    parser.add_argument('--list', action='store_true',
                        help='List all running activities without plotting')
    
    args = parser.parse_args()
    
    try:
        # Load running activities
        activities = load_running_activities(args.activities_dir)
        
        if args.list:
            # Just list the activities
            print(f"\nFound {len(activities)} running activities:")
            for timestamp, speed, name in activities:
                speed_kmh = speed * 3.6
                print(f"{timestamp.date()} - {name}: {speed_kmh:.2f} km/h")
        else:
            # Plot the activities
            plot_running_speeds(activities, args.output)
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
