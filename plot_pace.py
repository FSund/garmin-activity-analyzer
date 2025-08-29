#!/usr/bin/env python3
"""
Plot running pace for all running activities from Garmin activity summary files.

This script searches for all *_summary.json files in the activities directory,
filters for running activities (typeKey == "running"), and plots their average pace
(minutes per kilometer) over time with an inverted y-axis so faster paces appear higher.
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
        list: List of tuples (datetime, average_speed_m_s, activity_name)
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
    Plot average pace over time as minutes per kilometer with inverted y-axis.
    
    Args:
        activities (list): List of tuples (datetime, average_speed_m_s, activity_name)
        output_file (str, optional): File path to save the plot
    """
    if not activities:
        print("No activities to plot")
        return
    
    timestamps, speeds, names = zip(*activities)
    
    # Convert speed from m/s to pace in minutes per kilometer
    # pace (min/km) = 1000 / (speed_m_s * 60) = 1000/60 / speed_m_s = 16.667 / speed_m_s
    paces_min_per_km = [1000 / (speed * 60) for speed in speeds]
    
    # Create the plot
    plt.figure(figsize=(12, 8))
    
    # Plot the data
    plt.plot(timestamps, paces_min_per_km, 'b-o', markersize=4, linewidth=1.5, alpha=0.7)
    
    # Add a trend line
    timestamps_numeric = [ts.timestamp() for ts in timestamps]
    z = np.polyfit(timestamps_numeric, paces_min_per_km, 1)
    p = np.poly1d(z)
    trend_direction = "improving" if z[0] < 0 else "declining"
    plt.plot(timestamps, p(timestamps_numeric), "r--", alpha=0.8, linewidth=2, 
             label=f'Trend: {abs(z[0]*86400):.3f} sec/km per day ({trend_direction})')
    
    # Customize the plot
    plt.title('Running Pace Over Time', fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Pace (minutes per kilometer)', fontsize=12)
    plt.gca().invert_yaxis()  # Invert y-axis so faster times (lower values) are higher
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # Format x-axis
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Add statistics to the plot
    mean_pace = float(np.mean(paces_min_per_km))
    std_pace = float(np.std(paces_min_per_km))
    plt.axhline(y=mean_pace, color='green', linestyle=':', alpha=0.7,
                label=f'Mean: {mean_pace:.2f} min/km')
    plt.axhline(y=mean_pace + std_pace, color='orange', linestyle=':', alpha=0.5,
                label=f'+1 STD: {mean_pace + std_pace:.2f} min/km')
    plt.axhline(y=mean_pace - std_pace, color='orange', linestyle=':', alpha=0.5,
                label=f'-1 STD: {mean_pace - std_pace:.2f} min/km')    # Update legend
    plt.legend()
    
    # Print statistics
    print("\nStatistics:")
    print(f"Total activities: {len(activities)}")
    print(f"Mean pace: {mean_pace:.2f} min/km")
    print(f"Standard deviation: {std_pace:.2f} min/km")
    print(f"Best pace (fastest): {min(paces_min_per_km):.2f} min/km")
    print(f"Worst pace (slowest): {max(paces_min_per_km):.2f} min/km")
    print(f"Pace range: {max(paces_min_per_km) - min(paces_min_per_km):.2f} min/km")
    
    # Date range
    print(f"Date range: {min(timestamps).date()} to {max(timestamps).date()}")
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {output_file}")
    
    plt.show()


def main():
    parser = argparse.ArgumentParser(description='Plot running pace for running activities')
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
                pace_min_per_km = 1000 / (speed * 60)
                print(f"{timestamp.date()} - {name}: {pace_min_per_km:.2f} min/km")
        else:
            # Plot the activities
            plot_running_speeds(activities, args.output)
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
