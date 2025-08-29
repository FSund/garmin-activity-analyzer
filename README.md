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

### Plot running pace and heart rate over time

Plot average pace (minutes per kilometer) and heart rate in separate subplots:

    uv run python plot_pace.py

List all running activities with pace and heart rate without plotting:

    uv run python plot_pace.py --list

Save plot to a specific file:

    uv run python plot_pace.py --output my_pace_hr.png

Use a different activities directory:

    uv run python plot_pace.py --activities-dir path/to/activities

This should produce something like this

![Example](res/example.png)