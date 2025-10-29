#!/usr/bin/env bash
# Helper to install the user systemd unit and timer for DaystillRemedhan.
# Usage: bash install_systemd_user.sh
# This will copy files to $HOME/.config/systemd/user/, create a sample env file at
# $HOME/.config/daystill/daystill.env (edit it to set your BOT_TOKEN/CHANNEL_ID/TARGET_DATE),
# and print the systemctl --user commands to enable/start the timer.

set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_UNIT_DIR="$HOME/.config/systemd/user"
DAYSTILL_CONF_DIR="$HOME/.config/daystill"

mkdir -p "$TARGET_UNIT_DIR"
mkdir -p "$DAYSTILL_CONF_DIR"

cp -v "$DIR/daystill.service" "$TARGET_UNIT_DIR/"
cp -v "$DIR/daystill.timer" "$TARGET_UNIT_DIR/"

ENV_FILE="$DAYSTILL_CONF_DIR/daystill.env"
if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<EOF
# Edit these values before enabling the timer
# Example:
# BOT_TOKEN=8373361785:AAAA...yourtoken...
# CHANNEL_ID=@DaystillRemedhan
# TARGET_DATE=2026-03-10

# BOT_TOKEN=
# CHANNEL_ID=
# TARGET_DATE=2026-02-16
EOF
  echo "Created example env file: $ENV_FILE"
else
  echo "Env file already exists: $ENV_FILE"
fi

cat <<EOF
Files copied to: $TARGET_UNIT_DIR
Edit the file $ENV_FILE and set BOT_TOKEN, CHANNEL_ID and TARGET_DATE.
Then run these commands to enable the timer (user-level systemd):

  systemctl --user daemon-reload
  systemctl --user enable --now daystill.timer

To check status and logs:

  systemctl --user status daystill.timer
  systemctl --user status daystill.service
  journalctl --user -u daystill.service

If you want to stop:

  systemctl --user disable --now daystill.timer

EOF
