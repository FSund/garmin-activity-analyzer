# garmin-activity-analyzer

## Download activities from Garmin Connect

Install the package `garminexport` with `impersonate_browser` support to circumvent Cloudflare's bot protection

    pip install 'garminexport[impersonate_browser]'

Then download all activities

    garmin-backup --backup-dir=activities <username or email>

## Analyze runs

    python plot_activities.py activities/
