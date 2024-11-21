# garmin-activity-analyzer

## Usage

Install dependencies

    pip install -r requirements.txt

### Download activities from Garmin Connect

Use the package `garminexport` with `impersonate_browser` support to circumvent Cloudflare's bot protection.

Download all activities via

    garmin-backup --backup-dir=activities <username or email>

### Analyze runs

    python plot_activities.py activities/

This should produce something like this

![Example](res/example.png)