# Installation and Setup Processes
Requires python3 and pip install paho-mqtt

Setup to autorun as follows:
```sh
cd setup
. setup.sh
nano $HOME/.profile
```

Edit the `.profile` file to add the environment variables.


# Launch the Dashboard
To launch the dashboard cd into the node-red directory, then use:
```sh
. launch.sh
```

Access the dashboard workspace on: `http://localhost:1881`

Access the dashboard UI on: `http://localhost:1881/ui`

# Uninstall Process
follow the below to uninstall the setup:
```sh
cd setup
. uninstall.sh
```

## Environment Variables:
The following environment variables must be set:
```sh
export ROBOT_MANUFACTURER='agilex'
export ROBOT_SERIAL_NUMBER='LM-0000548'
export ROBOT_NAME='LIMO_0548'

export MQTT_BROKER_IP='mqtt.broker.ip'
export MQTT_BROKER_PORT='1883'
export MQTT_BROKER_NS='mrs_fleet_dashboard'
```
