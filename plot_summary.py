#!/usr/bin/env python3
"""
Plot running pace and heart rate for all running activities from Garmin activity summary files.

This script searches for all *_summary.json files in the activities directory,
filters for running activities (typeKey == "running"), and creates a two-panel plot:
- Top panel: Average pace (minutes per kilometer) with inverted y-axis so faster paces appear higher
- Bottom panel: Average heart rate trends over time
"""

import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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


def calculate_weekly_longest_runs(activities):
    """
    Calculate the longest run each week in kilometers.
    
    Args:
        activities (list): List of tuples (datetime, average_speed_m_s, average_hr, distance_m, activity_name)
        
    Returns:
        tuple: (week_dates, longest_runs_km)
            week_dates: List of datetime objects representing the start of each week (Monday)
            longest_runs_km: List of longest run distances in kilometers for each week
    """
    from collections import defaultdict
    import datetime as dt
    
    weekly_longest = defaultdict(float)
    
    for timestamp, _, _, distance, _ in activities:
        if distance is not None:
            # Find the Monday of the week containing this activity
            days_since_monday = timestamp.weekday()
            week_start = timestamp - dt.timedelta(days=days_since_monday)
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Keep track of the longest run in each week
            distance_km = distance / 1000.0
            weekly_longest[week_start] = max(weekly_longest[week_start], distance_km)
    
    # Sort by week and return as lists
    sorted_weeks = sorted(weekly_longest.items())
    week_dates = [week for week, _ in sorted_weeks]
    longest_runs_km = [distance for _, distance in sorted_weeks]
    
    return week_dates, longest_runs_km


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
    
    # Calculate weekly longest runs
    week_dates_longest, weekly_longest_km = calculate_weekly_longest_runs(activities)
    
    # Convert speed from m/s to pace in minutes per kilometer
    paces_min_per_km = [1000 / (speed * 60) for speed in speeds]
    
    # Create subplot layout: pace on top, heart rate in middle, weekly distances on bottom
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        subplot_titles=('Running Pace Over Time', 'Heart Rate Over Time', 'Weekly Running Distance and Longest Run'),
        specs=[[{"secondary_y": False}],
               [{"secondary_y": False}],
               [{"secondary_y": True}]],
        vertical_spacing=0.05
    )
    
    # Plot pace on the top subplot
    fig.add_trace(
        go.Scatter(
            x=timestamps, 
            y=paces_min_per_km, 
            mode='markers', 
            name='Pace',
            marker=dict(color='blue', size=6, opacity=0.7),
            hovertemplate='Date: %{x}<br>Pace: %{y:.2f} min/km<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Add pace trend line
    timestamps_numeric = [ts.timestamp() for ts in timestamps]
    z_pace = np.polyfit(timestamps_numeric, paces_min_per_km, 1)
    p_pace = np.poly1d(z_pace)
    trend_direction = "improving" if z_pace[0] < 0 else "declining"
    # Convert from min/km per second to sec/km per month: multiply by 86400*30*60
    pace_change_sec_per_month = abs(z_pace[0] * 86400 * 30 * 60)
    
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=p_pace(timestamps_numeric),
            mode='lines',
            name=f'Trend: {pace_change_sec_per_month:.1f} sec/km per month ({trend_direction})',
            line=dict(color='black', dash='dash', width=2),
            hovertemplate='Date: %{x}<br>Trend: %{y:.2f} min/km<extra></extra>'
        ),
        row=1, col=1
    )

    # Add pace statistics lines
    mean_pace = float(np.mean(paces_min_per_km))
    std_pace = float(np.std(paces_min_per_km))
    
    # Plot heart rate on the middle subplot
    if heart_rates_filtered:
        fig.add_trace(
            go.Scatter(
                x=timestamps_hr, 
                y=heart_rates_filtered, 
                mode='markers', 
                name='Heart Rate',
                marker=dict(color='red', size=6, opacity=0.7),
                hovertemplate='Date: %{x}<br>HR: %{y:.0f} bpm<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Add heart rate trend line
        timestamps_hr_numeric = [ts.timestamp() for ts in timestamps_hr]
        z_hr = np.polyfit(timestamps_hr_numeric, heart_rates_filtered, 1)
        p_hr = np.poly1d(z_hr)
        hr_trend_direction = "increasing" if z_hr[0] > 0 else "decreasing"
        
        fig.add_trace(
            go.Scatter(
                x=timestamps_hr,
                y=p_hr(timestamps_hr_numeric),
                mode='lines',
                name=f'HR Trend: {abs(z_hr[0]*86400*30):.2f} bpm per month ({hr_trend_direction})',
                line=dict(color='black', dash='dash', width=2),
                hovertemplate='Date: %{x}<br>HR Trend: %{y:.0f} bpm<extra></extra>'
            ),
            row=2, col=1
        )

        # Add heart rate statistics lines
        mean_hr = float(np.mean(heart_rates_filtered))
    else:
        fig.add_annotation(
            text='No heart rate data available',
            x=0.5, y=0.5,
            xref='x2', yref='y2',
            showarrow=False,
            font=dict(size=14)
        )
    
    # Plot weekly distances on the bottom subplot
    if week_dates and weekly_distances_km:
        # Plot total weekly distance as bars
        fig.add_trace(
            go.Bar(
                x=week_dates, 
                y=weekly_distances_km, 
                name='Total Weekly Distance',
                marker=dict(color='green', opacity=0.7),
                hovertemplate='Week of: %{x}<br>Total Distance: %{y:.1f} km<extra></extra>'
            ),
            row=3, col=1
        )
        
        # Plot longest runs on secondary y-axis
        if week_dates_longest and weekly_longest_km:
            fig.add_trace(
                go.Scatter(
                    x=week_dates_longest, 
                    y=weekly_longest_km, 
                    mode='markers+lines',
                    name='Longest Run',
                    marker=dict(color='orange', size=6),
                    line=dict(color='orange', width=2),
                    hovertemplate='Week of: %{x}<br>Longest Run: %{y:.1f} km<extra></extra>'
                ),
                row=3, col=1, secondary_y=True
            )
        
        # Add statistics for total distance
        mean_weekly_km = float(np.mean(weekly_distances_km))
    else:
        fig.add_annotation(
            text='No distance data available',
            x=0.5, y=0.5,
            xref='x3', yref='y3',
            showarrow=False,
            font=dict(size=14)
        )
    
    # Update layout and axes
    fig.update_layout(
        # height=1000,
        title_text="Running Activity Analysis",
        showlegend=True,
        hovermode='x unified'
    )
    
    # Update y-axes
    fig.update_yaxes(title_text="Pace (minutes per kilometer)", autorange="reversed", row=1, col=1)
    fig.update_yaxes(title_text="Average Heart Rate (bpm)", row=2, col=1)
    fig.update_yaxes(title_text="Total Distance (kilometers)", row=3, col=1)
    if week_dates_longest and weekly_longest_km:
        fig.update_yaxes(title_text="Longest Run (kilometers)", secondary_y=True, row=3, col=1)
    
    # Update x-axes
    fig.update_xaxes(title_text="Date", row=3, col=1)
    
    # Add grid
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    
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
    
    if week_dates_longest and weekly_longest_km:
        mean_longest_km = float(np.mean(weekly_longest_km))
        std_longest_km = float(np.std(weekly_longest_km))
        print("\nWeekly Longest Run Statistics:")
        print(f"Total weeks with longest runs: {len(weekly_longest_km)}")
        print(f"Mean longest run: {mean_longest_km:.1f} km")
        print(f"Standard deviation: {std_longest_km:.1f} km")
        print(f"Longest single run: {max(weekly_longest_km):.1f} km")
        print(f"Shortest longest run: {min(weekly_longest_km):.1f} km")
    else:
        print("\nNo longest run data available")
    
    # Date range
    print(f"Date range: {min(timestamps).date()} to {max(timestamps).date()}")
    
    if output_file:
        if output_file.endswith('.html'):
            fig.write_html(output_file)
            print(f"Interactive plot saved to {output_file}")
            fig.show()
        else:
            # For other formats, use write_image (requires kaleido)
            try:
                fig.write_image(output_file, width=1200, height=1000)
                print(f"Plot saved to {output_file}")
            except Exception as e:
                print(f"Error saving image: {e}")
                print("Consider installing kaleido for static image export: pip install kaleido")
                # Fallback to HTML
                html_file = output_file.rsplit('.', 1)[0] + '.html'
                fig.write_html(html_file)
                print(f"Saved as interactive HTML instead: {html_file}")


def main():
    parser = argparse.ArgumentParser(description='Plot running pace and heart rate for running activities')
    parser.add_argument('--activities-dir', default='activities',
                        help='Directory containing activity files (default: activities)')
    parser.add_argument('--output', '-o', help='Output file path for the plot', default='plot.html')
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
