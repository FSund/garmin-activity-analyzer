import argparse
import json
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils import process_activity_data


def analyze_multiple_activities(directory="activities"):
    activity_stats = []
    json_files = Path(directory).glob("*_details.json")
    json_files = list(json_files)
    if not json_files:
        raise RuntimeError(f"Input directory \"{directory}\" is empty")

    print(f'Analyzing {len(json_files)} json files from directory "{directory}"')

    for json_file in json_files:
        try:
            timestamp = json_file.name.split("_")[0]

            with open(json_file, "r") as f:
                details_json = json.load(f)

            # Get kilometer stats
            km_stats = process_activity_data(details_json)

            # Filter out invalid paces and first 2 kilometers
            valid_splits = km_stats[
                (km_stats["interval_pace"].notna())
                & (~np.isinf(km_stats["interval_pace"]))
                & (km_stats["interval_pace"] > 0)
                & (km_stats["km_interval"] >= 2)  # Skip first 2 km
            ]

            if valid_splits.empty:
                print(f"Warning: No valid splits found after km 2 in {json_file}")
                continue

            # Find fastest valid split
            fastest_split = valid_splits.loc[valid_splits["interval_pace"].idxmin()]
            
            # Format pace
            pace = fastest_split.interval_pace
            minutes = int(pace)
            seconds = (pace - minutes)*60
            seconds = round(seconds)
            # print(f"Fastest pace: {minutes:02d}:{seconds:02d}")

            activity_stats.append(
                {
                    "timestamp": datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S%z"),
                    "distance": valid_splits["sumDistance"].max() / 1000,
                    "fastest_km": fastest_split["km_interval"],
                    "fastest_pace": fastest_split["interval_pace"],
                    "fastest_pace_str": f"{minutes:02d}:{seconds:02d}",
                    "hr_at_fastest": fastest_split["directHeartRate"],
                }
            )

        except Exception as e:
            print(f"Error processing {json_file}: {str(e)}")

    if not activity_stats:
        print("No valid activities found")
        return pd.DataFrame()

    results_df = pd.DataFrame(activity_stats)
    results_df.sort_values("timestamp", inplace=True)

    return results_df


def plot_trends(results_df, window=5, show_distance=True):
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

    # Create figure with three subplots sharing x-axis
    if show_distance:
        fig, (ax1, ax3) = plt.subplots(
            2, 1, figsize=(12, 8), height_ratios=[2, 1], sharex=True
        )
    else:
        fig, ax1 = plt.subplots(figsize=(12, 6))

    ax2 = ax1.twinx()  # Create twin axis for heart rate

    # Plot pace data
    line1 = ax1.plot(
        results_df["timestamp"],
        results_df["fastest_pace"],
        marker="o",
        linestyle="",
        color="C0",
        alpha=0.3,
        label="Pace",
    )
    line1_rolling = ax1.plot(
        results_df["timestamp"],
        rolling_pace,
        marker="",
        linestyle="-",
        color="C0",
        linewidth=2,
        label=f"Pace ({window}-activity rolling avg)",
    )

    ax1.set_ylabel("Pace (min/km)", color="C0")
    ax1.tick_params(axis="y", labelcolor="C0")

    # Invert the pace axis
    ax1.invert_yaxis()

    # Plot heart rate data
    line2 = ax2.plot(
        results_df["timestamp"],
        results_df["hr_at_fastest"],
        marker="o",
        linestyle="",
        color="C1",
        alpha=0.3,
        label="Heart Rate",
    )
    line2_rolling = ax2.plot(
        results_df["timestamp"],
        rolling_hr,
        marker="",
        linestyle="-",
        color="C1",
        linewidth=2,
        label=f"Heart Rate ({window}-activity rolling avg)",
    )

    ax2.set_ylabel("Heart Rate (bpm)", color="C1")
    ax2.tick_params(axis="y", labelcolor="C1")

    # Add legend to top plot
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2)

    # Plot distance bars
    if show_distance:
        ax3.bar(
            results_df["timestamp"],
            results_df["distance"],
            alpha=0.6,
            color="C2",
            label="Distance",
        )
        ax3.set_ylabel("Distance (km)", color="C2")
        ax3.tick_params(axis="y", labelcolor="C2")
        ax3.grid(True, axis="y")
        ax3.legend()

    # Format x-axis
    plt.xticks(rotation=45)

    # Add titles
    ax1.set_title(
        "Fastest Split Pace and Heart Rate Over Time (After km 2)\n(Higher = Faster Pace)"
    )

    # Adjust layout
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("activities_dir", nargs="?", default="./activities")
    args = parser.parse_args()

    results = analyze_multiple_activities(args.activities_dir)
    plot_trends(results, show_distance=True)
