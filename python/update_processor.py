#!/usr/bin/env python3
import os
import sys
import yaml
import json
import time
import threading
import subprocess
import paho.mqtt.client as mqtt

# Path to configuration file
CONFIG_FILE = os.getenv('MRS_FLEET_DASHBOARD_CONFIG_PATH')

# Retrieve manufacturer and serial number from environment variables
ROBOT_MANUFACTURER = os.getenv("ROBOT_MANUFACTURER")
ROBOT_SERIAL_NUMBER = os.getenv("ROBOT_SERIAL_NUMBER")
ROBOT_NAME = os.getenv("ROBOT_SERIAL_NUMBER")

# Retrieve mqtt broker details
MQTT_BROKER_IP = os.getenv("MQTT_BROKER_IP")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT"))
MQTT_BROKER_NS = os.getenv("MQTT_BROKER_NS")

# Global dictionary to store workspace data
workspace_data = {
    "robot_ws": {},
    "research_ws": {}
}

update_data = {
    "robot_ws": {},
    "research_ws": {}
}


def load_config(config_file):
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def update_repo(repo_dir, new_remote, new_branch, workspace):
    """
    Update the repository's remote and branch.
    """
    print(update_data)
    try:
        print('\n---\n')
        subprocess.run(['git', 'remote', 'add', 'dashboard', new_remote], cwd=repo_dir, timeout=30)
        print('\n---\n')
        subprocess.run(['git', 'fetch', 'dashboard'], cwd=repo_dir, timeout=30)
        print('\n---\n')
        subprocess.run(['git', 'checkout', f'dashboard/{new_branch}', '-B', f'{new_branch}'], cwd=repo_dir, timeout=30)
        print('\n---\n')
        print(f"Updated repo at {repo_dir} to branch {new_branch} with remote {new_remote}")
    except Exception as e:
        print(f"Error updating repo {repo_dir}: {e}")

    # Reset the update_data after performing the update
    update_data[workspace] = {}


def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {str(rc)}\n")

    for ws in ["robot_ws", "research_ws"]:
        client.subscribe(f"{MQTT_BROKER_NS}/{ROBOT_MANUFACTURER}/{ROBOT_SERIAL_NUMBER}/dashboard/updates/{ws}/remote")
        client.subscribe(f"{MQTT_BROKER_NS}/{ROBOT_MANUFACTURER}/{ROBOT_SERIAL_NUMBER}/dashboard/updates/{ws}/branch")
        client.subscribe(f"{MQTT_BROKER_NS}/{ROBOT_MANUFACTURER}/{ROBOT_SERIAL_NUMBER}/dashboard/updates/{ws}/date")
        client.subscribe(f"{MQTT_BROKER_NS}/{ROBOT_MANUFACTURER}/{ROBOT_SERIAL_NUMBER}/dashboard/updates/{ws}/time")
        client.subscribe(f"{MQTT_BROKER_NS}/{ROBOT_MANUFACTURER}/{ROBOT_SERIAL_NUMBER}/dashboard/updates/{ws}/token")
        client.subscribe(f"{MQTT_BROKER_NS}/{ROBOT_MANUFACTURER}/{ROBOT_SERIAL_NUMBER}/dashboard/status/{ws}")
        client.subscribe(f"{MQTT_BROKER_NS}/{ROBOT_MANUFACTURER}/{ROBOT_SERIAL_NUMBER}/dashboard/workspaces/{ws}/git_status")


def on_message(client, userdata, msg):
    topic = msg.topic
    try:
        payload = msg.payload.decode('utf-8')
    except Exception as e:
        print(f"Error decoding JSON from topic {topic}: {e}")
        return
    topic_parts = topic.split("/")
    workspace = topic_parts[-2]
    sub_topic = topic_parts[-1]

    if "dashboard/workspaces" in topic:
        if workspace_data[workspace] != payload:
            print('WORKSPACE STATUS UPDATE >> ', workspace, payload, '\n')
            workspace_data[workspace] = payload
    elif "dashboard/updates" in topic:
        print(sub_topic, payload)
        update_data[workspace][sub_topic] = payload.replace('"','')
        if all(key in update_data[workspace] for key in ["remote", "branch", "date", "time", "token"]):
            print('\n')
            repo_config = userdata.get('repos', {}).get(workspace)
            print(repo_config)
            if repo_config:
                print('repo_config')
                update_repo(repo_config.get("dir"), update_data[workspace]["remote"], update_data[workspace]["branch"], workspace)


def main():
    config = load_config(CONFIG_FILE)
    repos = config["workspace_dashboard"]

    # Set up MQTT client
    client = None
    try:
        print('running with paho version post-2.0.0')
        ver = mqtt.CallbackAPIVersion.VERSION1
        client = mqtt.Client(ver, "dashboard_subscriber")
    except Exception as e:
        print(str(e))
        print('running with paho version pre-2.0.0')
        client = mqtt.Client("dashboard_subscriber")
    print('\n')

    client.user_data_set({"repos": repos})
    client.on_connect = on_connect
    client.on_message = on_message
    #broker_ip = config.get("publish", {}).get("mqtt", {}).get("broker_ip", "localhost")
    #broker_port = config.get("publish", {}).get("mqtt", {}).get("broker_port", 1883)
    broker_ip = MQTT_BROKER_IP
    broker_port = MQTT_BROKER_PORT

    while True:
        try:
            # If you need authentication or TLS, configure here
            client.connect(broker_ip, broker_port, 60)
            # Start a background loop to handle network events
            client.loop_start()
            break
        except Exception as e:
            print(str(e))



if __name__ == '__main__':
    main()
