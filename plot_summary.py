#!/usr/bin/env python3
"""
Plot running pace and heart rate for all running activities from Garmin activity summary files.

This script searches for all *_summary.json files in the activities directory,
filters for running activities (typeKey == "running"), and creates a two-panel plot:
- Top panel: Average pace (minutes per kilometer) with inverted y-axis so faster paces appear higher
- Bottom panel: Average heart rate trends over time
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
        list: List of tuples (datetime, average_speed_m_s, average_hr, activity_name)
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
            
            # Extract average speed and heart rate from summaryDTO
            summary_dto = data.get("summaryDTO", {})
            avg_speed = summary_dto.get("averageSpeed")
            avg_hr = summary_dto.get("averageHR")
            
            if avg_speed is not None:
                activity_name = data.get("activityName", "Unknown")
                activities.append((timestamp, avg_speed, avg_hr, activity_name))
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
    Plot average pace over time as minutes per kilometer with inverted y-axis,
    and average heart rate on a separate subplot below.
    
    Args:
        activities (list): List of tuples (datetime, average_speed_m_s, average_hr, activity_name)
        output_file (str, optional): File path to save the plot
    """
    if not activities:
        print("No activities to plot")
        return
    
    timestamps, speeds, heart_rates, names = zip(*activities)
    
    # Filter out activities without heart rate data
    valid_data = [(ts, speed, hr, name) for ts, speed, hr, name in activities if hr is not None]
    if len(valid_data) != len(activities):
        print(f"Warning: {len(activities) - len(valid_data)} activities missing heart rate data")
    
    if valid_data:
        timestamps_hr, _, heart_rates_filtered, _ = zip(*valid_data)
    else:
        timestamps_hr, heart_rates_filtered = [], []
    
    # Convert speed from m/s to pace in minutes per kilometer
    paces_min_per_km = [1000 / (speed * 60) for speed in speeds]
    
    # Create subplot layout: pace on top, heart rate on bottom
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    
    # Plot pace on the top subplot
    color1 = 'tab:blue'
    ax1.plot(timestamps, paces_min_per_km, 'o', color=color1, markersize=4, label='Pace')
    ax1.set_ylabel('Pace (minutes per kilometer)')
    ax1.tick_params(axis='y')
    ax1.invert_yaxis()  # Invert y-axis so faster times (lower values) are higher
    ax1.grid(True, alpha=0.3)
    ax1.set_title('Running Pace Over Time')
    
    # Add pace trend line
    timestamps_numeric = [ts.timestamp() for ts in timestamps]
    z_pace = np.polyfit(timestamps_numeric, paces_min_per_km, 1)
    p_pace = np.poly1d(z_pace)
    trend_direction = "improving" if z_pace[0] < 0 else "declining"
    ax1.plot(timestamps, p_pace(timestamps_numeric), "--", color="black", alpha=0.6, 
             linewidth=2, label=f'Trend: {abs(z_pace[0]*86400):.3f} sec/km per day ({trend_direction})')
    
    # Add pace statistics lines
    mean_pace = float(np.mean(paces_min_per_km))
    std_pace = float(np.std(paces_min_per_km))
    # ax1.axhline(y=mean_pace, color='green', linestyle=':', alpha=0.7,
    #             label=f'Mean: {mean_pace:.2f} min/km')
    ax1.legend(loc='upper left')
    
    # Plot heart rate on the bottom subplot
    color2 = 'tab:red'
    if heart_rates_filtered:
        ax2.plot(timestamps_hr, heart_rates_filtered, 'o', color=color2, markersize=4, label='Heart Rate')
        ax2.set_ylabel('Average Heart Rate (bpm)')
        ax2.tick_params(axis='y')
        ax2.grid(True, alpha=0.3)
        ax2.set_title('Heart Rate Over Time')
        
        # Add heart rate trend line
        timestamps_hr_numeric = [ts.timestamp() for ts in timestamps_hr]
        z_hr = np.polyfit(timestamps_hr_numeric, heart_rates_filtered, 1)
        p_hr = np.poly1d(z_hr)
        hr_trend_direction = "increasing" if z_hr[0] > 0 else "decreasing"
        ax2.plot(timestamps_hr, p_hr(timestamps_hr_numeric), "--", color="black", alpha=0.6, 
                 linewidth=2, label=f'Trend: {abs(z_hr[0]*86400):.2f} bpm per day ({hr_trend_direction})')
        
        # Add heart rate statistics lines
        mean_hr = float(np.mean(heart_rates_filtered))
        # ax2.axhline(y=mean_hr, color='darkred', linestyle=':', alpha=0.7,
        #             label=f'Mean: {mean_hr:.0f} bpm')
        ax2.legend(loc='upper left')
    else:
        ax2.text(0.5, 0.5, 'No heart rate data available', 
                 transform=ax2.transAxes, ha='center', va='center', fontsize=14)
        ax2.set_ylabel('Heart Rate (bpm)')
    
    # Set shared x-axis label and formatting
    ax2.set_xlabel('Timestamp')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Print statistics
    print("\nPace Statistics:")
    print(f"Total activities: {len(activities)}")
    print(f"Mean pace: {mean_pace:.2f} min/km")
    print(f"Standard deviation: {std_pace:.2f} min/km")
    print(f"Best pace (fastest): {min(paces_min_per_km):.2f} min/km")
    print(f"Worst pace (slowest): {max(paces_min_per_km):.2f} min/km")
    print(f"Pace range: {max(paces_min_per_km) - min(paces_min_per_km):.2f} min/km")
    
    if heart_rates_filtered:
        mean_hr = float(np.mean(heart_rates_filtered))
        std_hr = float(np.std(heart_rates_filtered))
        print("\nHeart Rate Statistics:")
        print(f"Activities with HR data: {len(heart_rates_filtered)}")
        print(f"Mean heart rate: {mean_hr:.0f} bpm")
        print(f"Standard deviation: {std_hr:.1f} bpm")
        print(f"Min heart rate: {min(heart_rates_filtered):.0f} bpm")
        print(f"Max heart rate: {max(heart_rates_filtered):.0f} bpm")
        print(f"HR range: {max(heart_rates_filtered) - min(heart_rates_filtered):.0f} bpm")
    else:
        print("\nNo heart rate data available")
    
    # Date range
    print(f"Date range: {min(timestamps).date()} to {max(timestamps).date()}")
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {output_file}")
    
    plt.show()


def main():
    parser = argparse.ArgumentParser(description='Plot running pace and heart rate for running activities')
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
            for timestamp, speed, hr, name in activities:
                pace_min_per_km = 1000 / (speed * 60)
                hr_str = f"{hr:.0f} bpm" if hr is not None else "No HR"
                print(f"{timestamp.date()} - {name}: {pace_min_per_km:.2f} min/km, {hr_str}")
        else:
            # Plot the activities
            plot_running_speeds(activities, args.output)
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
