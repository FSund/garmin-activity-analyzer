import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
from pathlib import Path
import math
import numpy as np

from analysis import process_activity_data, analyze_activity


def analyze_multiple_activities(directory="activities"):
    # Store results for each activity
    activity_stats = []

    # Get all details.json files
    json_files = Path(directory).glob("*_details.json")

    for json_file in json_files:
        try:
            # Extract timestamp from filename
            timestamp = json_file.name.split("_")[0]

            # Load and process the activity
            with open(json_file, "r") as f:
                details_json = json.load(f)

            # Get kilometer stats
            km_stats = process_activity_data(details_json)

            # Filter out invalid paces and first 2 kilometers
            valid_splits = km_stats[
                (km_stats["pace"].notna())
                & (~np.isinf(km_stats["pace"]))
                & (km_stats["pace"] > 0)
                & (km_stats["km_interval"] >= 2)  # Skip first 2 km
            ]

            if valid_splits.empty:
                print(f"Warning: No valid splits found in {json_file}")
                continue

            # Find fastest valid split
            fastest_split = valid_splits.loc[valid_splits["pace"].idxmin()]

            if not math.isfinite(fastest_split["pace"]):
                breakpoint()

            # Store results
            activity_stats.append(
                {
                    "timestamp": datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S%z"),
                    "distance": km_stats["km_interval"].max(),
                    "fastest_km": fastest_split["km_interval"],
                    "fastest_pace": fastest_split["pace"],
                    "hr_at_fastest": fastest_split["directHeartRate"],
                }
            )

        except Exception as e:
            print(f"Error processing {json_file}: {str(e)}")

    # Convert to DataFrame and sort by date
    results_df = pd.DataFrame(activity_stats)
    results_df.sort_values("timestamp", inplace=True)

    # Format the results
    # results_df['pace_formatted'] = results_df['fastest_pace'].apply(
    #     lambda x: f"{int(x)}:{int((x % 1) * 60):02d}"
    # )
    results_df["pace_formatted"] = results_df["fastest_pace"]

    return results_df


def print_activity_summary(results_df):
    print("\nActivity Analysis Summary:")
    print("=" * 80)
    print(f"Total Activities Analyzed: {len(results_df)}")
    print("\nFastest Kilometers:")
    print("-" * 80)
    print("Date           Distance  Fastest KM  Pace    Heart Rate")
    print("-" * 80)

    for _, row in results_df.iterrows():
        print(
            f"{row['timestamp'].strftime('%Y-%m-%d')}  {row['distance']:6.1f}km  "
            f"KM {row['fastest_km']:3.0f}     {row['pace_formatted']}    {row['hr_at_fastest']:3.0f} bpm"
        )


def plot_trends(results_df):
    if results_df.empty:
        print("No data to plot")
        return

    # Create figure with two y-axes
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()
    # fig, axes = plt.subplots(2)
    # ax1, ax2 = axes

    # Plot pace with inverted y-axis
    line1 = ax1.plot(
        results_df["timestamp"],
        results_df["fastest_pace"],
        # 'b-o',
        color="C0",
        label="Pace",
    )
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Pace (min/km)", color="C0")
    ax1.tick_params(axis="y", labelcolor="C0")

    # Invert the pace axis
    ax1.invert_yaxis()
    ax1.set_ylim([10, 5])

    # Rotate x-axis dates for better readability
    plt.xticks(rotation=45)

    # Plot heart rate
    line2 = ax2.plot(
        results_df["timestamp"],
        results_df["hr_at_fastest"],
        # 'r-o',
        color="C1",
        label="Heart Rate",
    )
    ax2.set_ylabel("Heart Rate (bpm)", color="C1")
    ax2.tick_params(axis="y", labelcolor="C1")

    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    plt.title("Fastest Split Pace and Heart Rate Over Time\n(Higher = Faster Pace)")
    plt.grid(True)

    # Adjust layout to prevent date labels from being cut off
    plt.tight_layout()

    plt.show()


def plot_trends_with_rolling(results_df, window=5):
    if results_df.empty:
        print("No data to plot")
        return

    # Calculate rolling averages
    rolling_pace = (
        results_df["fastest_pace"].rolling(window=window, min_periods=1).mean()
    )
    rolling_hr = (
        results_df["hr_at_fastest"].rolling(window=window, min_periods=1).mean()
    )

    # Create figure with two y-axes
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()

    # Plot pace data
    line1 = ax1.plot(
        results_df["timestamp"],
        results_df["fastest_pace"],
        "bo",
        alpha=0.3,
        label="Pace",
    )
    line1_rolling = ax1.plot(
        results_df["timestamp"],
        rolling_pace,
        "b-",
        linewidth=2,
        label=f"Pace ({window}-activity rolling avg)",
    )

    ax1.set_xlabel("Date")
    ax1.set_ylabel("Pace (min/km)", color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")

    # Invert the pace axis
    ax1.invert_yaxis()
    ax1.set_ylim([9.25, 6.25])

    plt.xticks(rotation=45)

    # Plot heart rate data
    line2 = ax2.plot(
        results_df["timestamp"],
        results_df["hr_at_fastest"],
        "ro",
        alpha=0.3,
        label="Heart Rate",
    )
    line2_rolling = ax2.plot(
        results_df["timestamp"],
        rolling_hr,
        "r-",
        linewidth=2,
        label=f"Heart Rate ({window}-activity rolling avg)",
    )

    ax2.set_ylabel("Heart Rate (bpm)", color="red")
    ax2.tick_params(axis="y", labelcolor="red")

    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2)

    plt.title(
        "Fastest Split Pace and Heart Rate Over Time (After km 2)\n(Higher = Faster Pace)"
    )
    plt.grid(True)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # Keep existing analysis code
    print("\nSingle Activity Analysis:")
    with open(
        "activities/2024-11-20T14:19:54+00:00_17582889898_details.json", "r"
    ) as f:
        details_json = json.load(f)
    analyze_activity(details_json)

    # Add multi-activity analysis
    print("\nMulti-Activity Analysis:")
    results = analyze_multiple_activities()
    print_activity_summary(results)

    # plot_trends(results)
    plot_trends_with_rolling(results)
