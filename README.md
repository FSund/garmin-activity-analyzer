# garmin-activity-analyzer

## Usage

Install dependencies

    uv sync

### Download activities from Garmin Connect

Download all activities via

    uv run garmin-backup --backup-dir=activities <username or email>

### Analyze runs

    uv run python plot_summary.py

This should produce something like this

![Example](res/example.png)