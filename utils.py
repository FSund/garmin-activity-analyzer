import json

import matplotlib.pyplot as plt
import pandas as pd


def process_activity_data(details_json):
    # Extract metric descriptors and their indices
    metrics_map = {
        descriptor["key"]: descriptor["metricsIndex"]
        for descriptor in details_json["metricDescriptors"]
    }

    # Invert map
    metrics_map = dict((v, k) for k, v in metrics_map.items())

    # Create DataFrame from activity metrics
    data = []
    for metric in details_json["activityDetailMetrics"]:
        data.append(metric["metrics"])

    df = pd.DataFrame(data)

    # Rename columns based on metric descriptors
    df.rename(columns=metrics_map, inplace=True)

    # Calculate cumulative distance in kilometers
    df["distance_km"] = df["sumDistance"] / 1000

    # Calculate pace (minutes per kilometer)
    time_diff = df["sumDuration"].diff()
    distance_diff = df["sumDistance"].diff() / 1000  # Convert to kilometers
    df["pace"] = (time_diff / 60) / distance_diff  # Minutes per kilometer

    # Group data by kilometer intervals
    df["km_interval"] = df["distance_km"].apply(lambda x: int(x))

    # Calculate averages per kilometer
    km_stats = (
        df.groupby("km_interval")
        .agg({"directHeartRate": "mean", "pace": "mean"})
        .reset_index()
    )

    return km_stats


def plot_activity_stats(km_stats):
    # Create figure with two y-axes
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()

    # Plot heart rate
    line1 = ax1.plot(
        km_stats["km_interval"],
        km_stats["directHeartRate"],
        color="red",
        label="Heart Rate",
    )
    ax1.set_xlabel("Distance (km)")
    ax1.set_ylabel("Heart Rate (bpm)", color="red")
    ax1.tick_params(axis="y", labelcolor="red")

    # Plot pace
    line2 = ax2.plot(
        km_stats["km_interval"], km_stats["pace"], color="blue", label="Pace"
    )
    ax2.set_ylabel("Pace (min/km)", color="blue")
    ax2.tick_params(axis="y", labelcolor="blue")

    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

    plt.title("Heart Rate and Pace per Kilometer")
    plt.grid(True)
    plt.show()


# Example usage with the provided data
def analyze_activity(details_json: pd.DataFrame, plot: bool):
    km_stats = process_activity_data(details_json)
    if plot:
        plot_activity_stats(km_stats)

    # Print summary statistics
    print("\nActivity Summary:")
    print(f"Total Distance: {km_stats['km_interval'].max():.2f} km")
    print("\nPer Kilometer Stats:")
    print(km_stats.round(2))


if __name__ == "__main__":
    with open(
        "activities/2024-11-20T14:19:54+00:00_17582889898_details.json", "r"
    ) as f:
        details_json = json.load(f)

    analyze_activity(details_json)
