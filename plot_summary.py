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
        list: List of tuples (datetime, average_speed_m_s, average_hr, distance_m, activity_name)
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
            
            # Extract average speed, heart rate, and distance from summaryDTO
            summary_dto = data.get("summaryDTO", {})
            avg_speed = summary_dto.get("averageSpeed")
            avg_hr = summary_dto.get("averageHR")
            distance = summary_dto.get("distance")
            
            if avg_speed is not None:
                activity_name = data.get("activityName", "Unknown")
                activities.append((timestamp, avg_speed, avg_hr, distance, activity_name))
            else:
                print(f"Warning: No average speed found for {file_path.name}")
                
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error processing {file_path.name}: {e}")
            continue
    
    print(f"Found {running_count} running activities with speed data")
    
    # Sort by timestamp
    activities.sort(key=lambda x: x[0])
    
    return activities


def calculate_weekly_distances(activities):
    """
    Calculate weekly running distances in kilometers.
    
    Args:
        activities (list): List of tuples (datetime, average_speed_m_s, average_hr, distance_m, activity_name)
        
    Returns:
        tuple: (week_dates, weekly_distances_km)
            week_dates: List of datetime objects representing the start of each week (Monday)
            weekly_distances_km: List of total distances in kilometers for each week
    """
    from collections import defaultdict
    import datetime as dt
    
    weekly_distances = defaultdict(float)
    
    for timestamp, _, _, distance, _ in activities:
        if distance is not None:
            # Find the Monday of the week containing this activity
            days_since_monday = timestamp.weekday()
            week_start = timestamp - dt.timedelta(days=days_since_monday)
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Add distance in kilometers
            weekly_distances[week_start] += distance / 1000.0
    
    # Sort by week and return as lists
    sorted_weeks = sorted(weekly_distances.items())
    week_dates = [week for week, _ in sorted_weeks]
    distances_km = [distance for _, distance in sorted_weeks]
    
    return week_dates, distances_km


def plot_running_speeds(activities, output_file=None):
    """
    Plot average pace over time as minutes per kilometer with inverted y-axis,
    average heart rate on a separate subplot, and weekly distances as a bar chart.
    
    Args:
        activities (list): List of tuples (datetime, average_speed_m_s, average_hr, distance_m, activity_name)
        output_file (str, optional): File path to save the plot
    """
    if not activities:
        print("No activities to plot")
        return
    
    timestamps, speeds, heart_rates, distances, names = zip(*activities)
    
    # Filter out activities without heart rate data
    valid_hr_data = [(ts, speed, hr, dist, name) for ts, speed, hr, dist, name in activities if hr is not None]
    if len(valid_hr_data) != len(activities):
        print(f"Warning: {len(activities) - len(valid_hr_data)} activities missing heart rate data")
    
    if valid_hr_data:
        timestamps_hr, _, heart_rates_filtered, _, _ = zip(*valid_hr_data)
    else:
        timestamps_hr, heart_rates_filtered = [], []
    
    # Calculate weekly distances
    week_dates, weekly_distances_km = calculate_weekly_distances(activities)
    
    # Convert speed from m/s to pace in minutes per kilometer
    paces_min_per_km = [1000 / (speed * 60) for speed in speeds]
    
    # Create subplot layout: pace on top, heart rate in middle, weekly distances on bottom
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 14), sharex=True)
    
    # Plot pace on the top subplot
    color1 = 'tab:blue'
    ax1.plot(timestamps, paces_min_per_km, 'o', color=color1, alpha=0.7, markersize=4, label='Pace')
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
             linewidth=2, label=f'Trend: {abs(z_pace[0]*86400*30):.3f} sec/km per month ({trend_direction})')

    # Add pace statistics lines
    mean_pace = float(np.mean(paces_min_per_km))
    std_pace = float(np.std(paces_min_per_km))
    ax1.legend(loc='upper left')
    
    # Plot heart rate on the middle subplot
    color2 = 'tab:red'
    if heart_rates_filtered:
        ax2.plot(timestamps_hr, heart_rates_filtered, 'o', color=color2, alpha=0.7, markersize=4, label='Heart Rate')
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
                 linewidth=2, label=f'Trend: {abs(z_hr[0]*86400*30):.2f} bpm per month ({hr_trend_direction})')

        # Add heart rate statistics lines
        mean_hr = float(np.mean(heart_rates_filtered))
        ax2.legend(loc='upper left')
    else:
        ax2.text(0.5, 0.5, 'No heart rate data available', 
                 transform=ax2.transAxes, ha='center', va='center', fontsize=14)
        ax2.set_ylabel('Heart Rate (bpm)')
    
    # Plot weekly distances on the bottom subplot
    color3 = 'tab:green'
    if week_dates and weekly_distances_km:
        # Calculate bar width (approximately 6 days to leave some space between bars)
        if len(week_dates) > 1:
            bar_width = (week_dates[1] - week_dates[0]).days * 0.8
        else:
            bar_width = 6
        
        ax3.bar(week_dates, weekly_distances_km, width=bar_width, color=color3, alpha=0.7, label='Weekly Distance')
        ax3.set_ylabel('Distance (kilometers)')
        ax3.tick_params(axis='y')
        ax3.grid(True, alpha=0.3)
        ax3.set_title('Weekly Running Distance')
        
        # Add statistics
        mean_weekly_km = float(np.mean(weekly_distances_km))
        ax3.legend(loc='upper left')
    else:
        ax3.text(0.5, 0.5, 'No distance data available', 
                 transform=ax3.transAxes, ha='center', va='center', fontsize=14)
        ax3.set_ylabel('Distance (km)')
    
    # Set shared x-axis label and formatting
    ax3.set_xlabel('Date')
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
    
    if week_dates and weekly_distances_km:
        mean_weekly_km = float(np.mean(weekly_distances_km))
        std_weekly_km = float(np.std(weekly_distances_km))
        total_km = float(np.sum(weekly_distances_km))
        print("\nWeekly Distance Statistics:")
        print(f"Total weeks with activities: {len(weekly_distances_km)}")
        print(f"Total distance: {total_km:.1f} km")
        print(f"Mean weekly distance: {mean_weekly_km:.1f} km")
        print(f"Standard deviation: {std_weekly_km:.1f} km")
        print(f"Max weekly distance: {max(weekly_distances_km):.1f} km")
        print(f"Min weekly distance: {min(weekly_distances_km):.1f} km")
    else:
        print("\nNo distance data available")
    
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
            for timestamp, speed, hr, distance, name in activities:
                pace_min_per_km = 1000 / (speed * 60)
                hr_str = f"{hr:.0f} bpm" if hr is not None else "No HR"
                dist_str = f"{distance/1000:.2f} km" if distance is not None else "No distance"
                print(f"{timestamp.date()} - {name}: {pace_min_per_km:.2f} min/km, {hr_str}, {dist_str}")
        else:
            # Plot the activities
            plot_running_speeds(activities, args.output)
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
