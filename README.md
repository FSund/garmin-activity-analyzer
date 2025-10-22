# garmin-activity-analyzer

## Usage

Install dependencies

    uv sync

Download all activities

    uv run get_activities.py

Analyze runs

    uv run python plot_summary.py

This should produce something like this

![Example](res/example.png)

## Download activitiy details from Garmin Connect

To download detailed activity data (.tcx, .gpx and .fit) from Garmin Connect, you can use the `garmin-backup` tool

    uv run garmin-backup --backup-dir=activities <username or email>

This is a bit flaky, probably due to anti-bot measures, but can be nice for backup purposes.