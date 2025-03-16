#!/bin/bash

# Define the autostart directory and file
AUTOSTART_DIR="$HOME/.config/autostart"
AUTOSTART_FILE="$AUTOSTART_DIR/myscript.desktop"

# Define the profile file
PROFILE_FILE="$HOME/.profile"

# Define the environment variables to remove
ENV_VARS=(
    "export ROBOT_MANUFACTURER="
    "export ROBOT_SERIAL_NUMBER="
    "export ROBOT_NAME="
    "export MQTT_BROKER_IP="
    "export MQTT_BROKER_PORT="
    "export MQTT_BROKER_NS="
    "export MRS_FLEET_DASHBOARD_CONFIG_PATH="
)

# Remove the autostart file
if [ -f "$AUTOSTART_FILE" ]; then
    rm "$AUTOSTART_FILE"
    echo "Removed autostart file: $AUTOSTART_FILE"
else
    echo "Autostart file not found, skipping."
fi

# Backup the original profile file
cp "$PROFILE_FILE" "$PROFILE_FILE.bak"

# Remove environment variables from .profile
echo "Removing environment variables from $PROFILE_FILE..."
for VAR in "${ENV_VARS[@]}"; do
    sed -i "/^$VAR/d" "$PROFILE_FILE"
done

echo "Environment variables removed."

# Reload .profile to apply changes immediately
source "$PROFILE_FILE"

echo "Undo setup complete. Your system is now restored to its previous state."
