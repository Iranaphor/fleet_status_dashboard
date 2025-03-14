#!/usr/bin/env python3
import os
import sys
import yaml
import time
import threading
import subprocess
import paho.mqtt.client as mqtt

# Read configuration from a YAML file
CONFIG_FILE = './status_config.yaml'  # adjust the path as needed

def load_config(config_file):
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

# Action: git_status
def git_status(repo_config):
    """
    Run 'git status' in the specified repo directory.
    Returns the output or error.
    """
    repo_dir = repo_config.get('dir')
    try:
        result = subprocess.run(
            ['git', 'status'],
            cwd=repo_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Exception: {str(e)}"

# Dictionary mapping action names to functions
ACTION_FUNCTIONS = {
    'git_status': git_status,
    # add more actions here as needed
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

        # If you need authentication or TLS, configure here
        self.client.connect(broker_ip, broker_port)
        # Start a background loop to handle network events
        self.client.loop_start()

    def publish(self, topic, message):
        full_topic = f"{self.namespace}{topic}"
        self.client.publish(full_topic, message)
        print(f"Published to {full_topic}: {message}")

# Worker thread for running actions repeatedly
def action_worker(repo_name, action_name, repo_config, action_config, publisher, robot_name):
    hz = action_config.get('hz', 1)  # default to 1 Hz if not specified
    # Convert frequency to period (seconds)
    period = 1 / hz if hz > 0 else 1
    action_func = ACTION_FUNCTIONS.get(action_name)
    if action_func is None:
        print(f"Action '{action_name}' not implemented.")
        return
    topic = f"/{robot_name}/{repo_name}/{action_name}"
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
    repos = config.get('repos', {})
    actions = config.get('actions', {})
    publish_config = config.get('publish', {}).get('mqtt', {})

    # Use an environment variable or default for robot_name
    robot_name = os.environ.get('ROBOT_NAME', 'default_robot')

    # Initialize MQTT publisher
    broker_ip = publish_config.get('broker_ip', 'localhost')
    broker_port = publish_config.get('broker_port', 1883)
    namespace = publish_config.get('namespace', '')
    publisher = MQTTPublisher(broker_ip, broker_port, namespace)

    # For each repo, schedule its actions in separate threads
    for repo_name, repo_config in repos.items():
        repo_actions = repo_config.get('actions', [])
        for action_name in repo_actions:
            action_config = actions.get(action_name, {})
            t = threading.Thread(
                target=action_worker,
                args=(repo_name, action_name, repo_config, action_config, publisher, robot_name),
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
