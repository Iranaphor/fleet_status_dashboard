#!/usr/bin/env python3
import os
import sys
import yaml
import time
import threading
import subprocess
import paho.mqtt.client as mqtt

from actions import git_status, git_branch, git_remote, robot_name, battery, last_online, ssid, ip

# Read configuration from a YAML file
CONFIG_FILE = os.environ.get('MRS_FLEET_DASHBOARD_CONFIG_PATH')

def load_config(config_file):
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

# Dictionary mapping action names to functions
ACTION_FUNCTIONS = {
    'git_status': git_status,
    'git_branch': git_branch,
    'git_remote': git_remote,
    'robot_name': robot_name,
    'battery': battery,
    'last_online': last_online,
    'ssid': ssid,
    'ip': ip
}

# MQTT Publisher
class MQTTPublisher:
    def __init__(self, broker_ip, broker_port, namespace):
        self.namespace = namespace.rstrip('/')
        try:
            print('running with paho version post-2.0.0')
            ver = mqtt.CallbackAPIVersion.VERSION1
            self.client = mqtt.Client(ver, 'status_publisher')
        except Exception as e:
            print(str(e))
            print('running with paho version pre-2.0.0')
            self.client = mqtt.Client('status_publisher')

        while True:
            try:
                # If you need authentication or TLS, configure here
                self.client.connect(broker_ip, broker_port)
                # Start a background loop to handle network events
                self.client.loop_start()
                break
            except Exception as e:
                print(str(e))

    def publish(self, topic, message):
        full_topic = f"{self.namespace}{topic}"
        self.client.publish(full_topic, message, retain=True)
        print(f"Published: {message}")
        #print(f"Published to {full_topic}: {message}")

# Worker thread for running actions repeatedly
def action_worker(repo_name, action_name, repo_config, action_config, publisher, manufacturer, robot_name, topic_group):
    hz = action_config.get('hz', 1)  # default to 1 Hz if not specified
    # Convert frequency to period (seconds)
    period = 1 / hz if hz > 0 else 1
    action_func = ACTION_FUNCTIONS.get(action_name)
    if action_func is None:
        print(f"Action '{action_name}' not implemented.")
        return
    topic = f"/{manufacturer}/{robot_name}/{topic_group}/{repo_name}/{action_name}"
    while True:
        # Execute the action function with the repo configuration
        result = action_func(repo_config)
        # Publish the result to MQTT
        publisher.publish(topic, result)
        time.sleep(period)

def main():
    # Load configuration
    config = load_config(CONFIG_FILE)

    # Retrieve configuration sections
    robot_ws = config.get('workspace_dashboard', {}).get('robot_ws', {})
    research_ws = config.get('workspace_dashboard', {}).get('research_ws', {})
    dashboard_ws = config.get('workspace_dashboard', {}).get('dashboard_ws', {})
    meta = config.get('workspace_dashboard', {}).get('meta', {})

    # Retrieve other diagnostics
    repositories = config.get('repositories', {})
    actions = config.get('actions', {})
    publish_config = config.get('publish', {}).get('mqtt', {})

    # Use an environment variable or default for robot_name
    manufacturer = os.environ.get('ROBOT_MANUFACTURER')
    serial_number = os.environ.get('ROBOT_SERIAL_NUMBER')
    robot_name = os.environ.get('ROBOT_NAME')

    # Initialize MQTT publisher
    #broker_ip = publish_config.get('broker_ip', 'local')
    #broker_port = publish_config.get('broker_port', 1883)
    broker_ip = os.environ.get('MQTT_BROKER_IP')
    broker_port = int(os.environ.get('MQTT_BROKER_PORT'))
    namespace = os.environ.get('MQTT_BROKER_NS')
    publisher = MQTTPublisher(broker_ip, broker_port, namespace)

    # For each workspace, schedule its actions in separate threads
    topic_group = 'dashboard/workspaces'
    for ws_name, ws_config in [['robot_ws', robot_ws], ['research_ws', research_ws], ['dashboard_ws', dashboard_ws]]:
        ws_actions = ws_config.get('actions', [])
        for action_name in ws_actions:
            action_config = actions.get(action_name, {})
            t = threading.Thread(
                target=action_worker,
                args=(ws_name, action_name, ws_config, action_config, publisher, manufacturer, serial_number, topic_group),
                daemon=True
            )
            t.start()
            print(f"Started thread for dashboard workspace repo '{ws_name}' action '{action_name}'.")

    # For each meta action, schedule its actions in separate threads
    topic_group = 'dashboard'
    for action_name in meta.get('actions', []):
        action_config = actions.get(action_name, {})
        t = threading.Thread(
            target=action_worker,
            args=('meta', action_name, None, action_config, publisher, manufacturer, serial_number, topic_group),
            daemon=True
        )
        t.start()
        print(f"Started thread for dashboard meta action '{action_name}'.")

    # For each repo, schedule its actions in separate threads
    topic_group = 'repositories'
    for repo_name, repo_config in repositories.items():
        repo_actions = repo_config.get('actions', [])
        for action_name in repo_actions:
            action_config = actions.get(action_name, {})
            t = threading.Thread(
                target=action_worker,
                args=(repo_name, action_name, repo_config, action_config, publisher, manufacturer, serial_number, topic_group),
                daemon=True
            )
            t.start()
            print(f"Started thread for repo '{repo_name}' action '{action_name}'.")

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")

if __name__ == '__main__':
    main()
