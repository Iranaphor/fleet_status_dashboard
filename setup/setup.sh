#!/bin/bash

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define paths to the Python scripts relative to this script
SCRIPT1_PATH="$(realpath "$SCRIPT_DIR/../python/status_publisher.py")"
SCRIPT2_PATH="$(realpath "$SCRIPT_DIR/../python/update_processor.py")"

# Define the autostart directory and file
AUTOSTART_DIR="$HOME/.config/autostart"
AUTOSTART_FILE="$AUTOSTART_DIR/myscript.desktop"

# Ensure the directory exists
mkdir -p "$AUTOSTART_DIR"

# Write the .desktop file content
cat <<EOF > "$AUTOSTART_FILE"
[Desktop Entry]
Type=Application
Exec=python3 "$SCRIPT1_PATH" & python3 "$SCRIPT2_PATH"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=MRS Fleet Dashboard Scripts
Comment=Runs the publisher and updator scripts for the MRS Dashboard after desktop loads
EOF

# Ensure correct permissions
chmod +x "$AUTOSTART_FILE"

# Confirm success
echo "Autostart file created at: $AUTOSTART_FILE"
echo "Your Python scripts ($SCRIPT1_PATH and $SCRIPT2_PATH) will now run after the desktop loads."


# Define the profile file
PROFILE_FILE="$HOME/.profile"

# Define environment variables
ENV_VARS=(
    "export ROBOT_MANUFACTURER="
    "export ROBOT_SERIAL_NUMBER="
    "export ROBOT_NAME="
    "export MQTT_BROKER_IP="
    "export MQTT_BROKER_PORT="
    "export MQTT_BROKER_NS="
)

# Append environment variables to .profile if they are not already present
echo "Updating $PROFILE_FILE with required environment variables..."
for VAR in "${ENV_VARS[@]}"; do
    if ! grep -q "^$VAR" "$PROFILE_FILE"; then
        echo "$VAR" >> "$PROFILE_FILE"
        echo "Added: $VAR"
    else
        echo "Already present: $VAR"
    fi
done

# Reload .profile to apply the changes immediately
source "$PROFILE_FILE"
echo "Environment variables updated and loaded."

echo "ENSURE YOU SET THE ENVIRONMENT VARIABLES IN ~/.profile NOW"

echo "Setup complete. Please restart your system for full effect."
