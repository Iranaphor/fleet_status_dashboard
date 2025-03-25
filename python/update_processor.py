#!/usr/bin/env python3
import os
import re
import time
import yaml
import subprocess
from urllib.parse import urlparse

import paho.mqtt.client as mqtt

from actions import sp


def is_url(string):
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def is_valid_git_branch(name: str) -> bool:
    # Disallowed characters and patterns
    invalid_patterns = [
        r'[\000-\037\177]',  # ASCII control characters
        r'[\~\^:\?\*\[\\]',  # Special characters
        r'\.\.',             # Double dots
        r'//@',              # Double slash at start
        r'//',               # Consecutive slashes
        r'@{',               # Reflog syntax
        r'\.$',              # Ends with a dot
        r'\.lock$',          # Ends with ".lock"
        r'^/',               # Starts with slash
        r'/$',               # Ends with slash
        r'^-$',              # Only a dash
        r'^-',               # Starts with dash
        r'^@$',              # Just "@"
        r'\s',               # Whitespace
    ]

    for pattern in invalid_patterns:
        if re.search(pattern, name):
            return False

    # Empty names are not allowed
    if not name:
        return False

    return True


class DashboardUpdater:
    def __init__(self, config_path, robot_manufacturer, robot_serial_number, mqtt_broker_ip, mqtt_broker_port, mqtt_broker_ns):
        self.config_path = config_path
        self.robot_manufacturer = robot_manufacturer
        self.robot_serial_number = robot_serial_number
        self.robot_name = robot_serial_number  # Alias
        self.mqtt_broker_ip = mqtt_broker_ip
        self.mqtt_broker_port = mqtt_broker_port
        self.mqtt_broker_ns = mqtt_broker_ns

        self.workspace_data = {
            "robot_ws": {},
            "research_ws": {},
            "dashboard_ws": {}
        }
        self.update_data = {
            "robot_ws": {},
            "research_ws": {},
            "dashboard_ws": {}
        }

        self.config = self.load_config()
        self.repos = self.config["workspace_dashboard"]

        # MQTT client setup
        client_name = f'status_updater_{self.robot_manufacturer}_{self.robot_serial_number}'
        try:
            print('running with paho version post-2.0.0')
            ver = mqtt.CallbackAPIVersion.VERSION1
            self.client = mqtt.Client(ver, client_name)
        except Exception as e:
            print(str(e))
            print('running with paho version pre-2.0.0')
            self.client = mqtt.Client(client_name)

        self.client.user_data_set({"repos": self.repos})
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def load_config(self):
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def update_repo(self, repo_dir, new_remote, new_branch, workspace):

        # Check url and branch are valid
        if not is_url(new_remote):
            print(f"Invalid URL {new_remote}")
            return        
        if not is_valid_git_branch(new_branch):
            print(f"Invalid branch {new_remote} --branch {new_branch}")
            return

        try:
            print('\n---\n')
            subprocess.run(['git', 'remote', 'add', 'dashboard', new_remote], cwd=repo_dir, timeout=30)
            subprocess.run(['git', 'fetch', 'dashboard'], cwd=repo_dir, timeout=30)
            subprocess.run(['git', 'checkout', f'dashboard/{new_branch}', '-B', f'{new_branch}'], cwd=repo_dir, timeout=30)
            print(f"Updated repo at {repo_dir} to branch {new_branch} with remote {new_remote}")
        except Exception as e:
            print(f"Error updating repo {repo_dir}: {e}")
        self.update_data[workspace] = {}

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected to MQTT broker with result code {rc}\n")
        for ws in ["robot_ws", "research_ws", "dashboard_ws"]:
            # Define namespace
            base = f"{self.mqtt_broker_ns}/{self.robot_manufacturer}/{self.robot_serial_number}/dashboard"
            # To get new repo to load
            client.subscribe(f"{base}/updates/{ws}/remote")
            client.subscribe(f"{base}/updates/{ws}/branch")
            client.subscribe(f"{base}/updates/{ws}/date")
            client.subscribe(f"{base}/updates/{ws}/time")
            client.subscribe(f"{base}/updates/{ws}/token")
            # To get current status of repos
            client.subscribe(f"{base}/status/{ws}")
            client.subscribe(f"{base}/workspaces/{ws}/git_status")
        # To get new command to run
        client.subscribe(f"{base}/updates/command/command")

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        try:
            payload = msg.payload.decode('utf-8')
        except Exception as e:
            print(f"Error decoding JSON from topic {topic}: {e}")
            return

        topic_parts = topic.split("/")
        workspace = topic_parts[-2]
        sub_topic = topic_parts[-1]

        # Save current status
        if "dashboard/workspaces" in topic:
            if self.workspace_data[workspace] != payload:
                print('WORKSPACE STATUS UPDATE >>', workspace, payload)
                self.workspace_data[workspace] = payload

        # Execute command
        elif "dashboard/updates/command" in topic:
            print('\n----------\n', sub_topic, payload)
        
            # Format return topic and command
            new_topic = topic.replace('/command/command', '/command/result')
            pay = payload.replace('"','')

            # Run command
            result = subprocess.run(pay, 
                                    cwd=os.path.expanduser('~'), 
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    shell=True)
            if result.returncode == 0:

                # Prepare and publish result
                result = result.stdout.strip()
                client.publish(new_topic, result)



        # Update repo once all fields are received
        elif "dashboard/updates" in topic:
            print('\n----------\n', sub_topic, payload)
            self.update_data[workspace][sub_topic] = payload.replace('"', '')
            if all(k in self.update_data[workspace] for k in ["remote", "branch", "date", "time", "token"]):
                repo_config = userdata.get('repos', {}).get(workspace)
                if repo_config:
                    self.update_repo(repo_config.get("dir"), self.update_data[workspace]["remote"], self.update_data[workspace]["branch"], workspace)

    def run(self):
        while True:
            try:
                self.client.connect(self.mqtt_broker_ip, self.mqtt_broker_port)
                self.client.loop_start()
                break
            except Exception as e:
                print(str(e))
        print('Connection without failure!')

if __name__ == '__main__':
    # Define environment variables here
    CONFIG_FILE = os.getenv('MRS_FLEET_DASHBOARD_CONFIG_PATH')
    ROBOT_MANUFACTURER = os.getenv("ROBOT_MANUFACTURER")
    ROBOT_SERIAL_NUMBER = os.getenv("ROBOT_SERIAL_NUMBER")
    MQTT_BROKER_IP = os.getenv("MQTT_BROKER_IP")
    MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", 1883))
    MQTT_BROKER_NS = os.getenv("MQTT_BROKER_NS")

    updater = DashboardUpdater(
        config_path=CONFIG_FILE,
        robot_manufacturer=ROBOT_MANUFACTURER,
        robot_serial_number=ROBOT_SERIAL_NUMBER,
        mqtt_broker_ip=MQTT_BROKER_IP,
        mqtt_broker_port=MQTT_BROKER_PORT,
        mqtt_broker_ns=MQTT_BROKER_NS
    )

    updater.run()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")