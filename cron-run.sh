#!/bin/bash
set -e

APP_SCRIPT="/app/src/main.py"
CRON_SCHEDULE="${CRON_SCHEDULE:-0 6 * * *}"
CRON_FILE="/etc/cron.d/app-cron"
LOG_FILE="/var/log/cron.log"

# Check env
: "${GOOGLE_SHEET_FILE:?GOOGLE_SHEET_FILE not set}"
: "${GRAPHS_SHEET_NAME:?GRAPHS_SHEET_NAME not set}"

# Check script
if [ ! -f "$APP_SCRIPT" ]; then
    echo "❌ App script $APP_SCRIPT not found!"
    exit 1
fi

echo "Using CRON_SCHEDULE: $CRON_SCHEDULE"

# Clear existing cron file
: > "$CRON_FILE"

# Export environment variables for cron
cat <<EOF > /etc/cron.env
export GOOGLE_SHEET_FILE="${GOOGLE_SHEET_FILE}"
export GRAPHS_SHEET_NAME="${GRAPHS_SHEET_NAME}"
EOF

# Write cron job
echo "$CRON_SCHEDULE . /etc/cron.env; /usr/local/bin/python $APP_SCRIPT >> $LOG_FILE 2>&1" >> "$CRON_FILE"

# Set permissions
chmod 0644 "$CRON_FILE"
crontab "$CRON_FILE"

# Make sure the log file exists
touch "$LOG_FILE"

# Start cron in foreground and log
cron
tail -F "$LOG_FILE"
