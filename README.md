# garmin-activity-analyzer

## Usage

Install dependencies

    uv sync

### Download activities from Garmin Connect

Use the package `garminexport` with `impersonate_browser` support to circumvent Cloudflare's bot protection.

Download all activities via

    uv run garmin-backup --backup-dir=activities <username or email>

### Analyze runs

    uv run python plot_activities.py activities/

### Plot running speeds over time

Plot average speed for all running activities:

    uv run python plot_running_speeds.py

List all running activities without plotting:

    uv run python plot_running_speeds.py --list

Save plot to a specific file:

    uv run python plot_running_speeds.py --output my_speeds.png

Use a different activities directory:

    uv run python plot_running_speeds.py --activities-dir path/to/activities

This should produce something like this

![Example](res/example.png)