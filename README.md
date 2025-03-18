# To Install on Robot

### Installation and Setup Processes
Setup to autorun as follows:
```sh
cd setup
. setup.sh
```

The status publisher requires python3 and pip install paho-mqtt. These are defined in `python/setup.sh`

### Environment Variables:
Edit the `.profile` file to add the environment variables.

```sh
nano $HOME/.profile
```

The following environment variables must be set.
```sh
export ROBOT_MANUFACTURER='agilex'
export ROBOT_SERIAL_NUMBER='LM-0000548'
export ROBOT_NAME='LIMO_0548'

export MQTT_BROKER_IP='mqtt.broker.ip'
export MQTT_BROKER_PORT='1883'
export MQTT_BROKER_NS='mrs_fleet_dashboard'
```

### Config File
The default configuration is defined in `setup/config.yaml`, you can make a copy of this in a new directory to make changes. Ensure you point to the new config file location in `$HOME/.profile`

```sh
export MQTT_BROKER_NS='mrs_fleet_dashboard'
```

### Uninstall on Robot
follow the below to uninstall the setup:
```sh
cd setup
. uninstall.sh
```

# To Install the Dashboard

### Installation and Setup Processes
To install the dashboard system, use the following:
```sh
cd dashboard
. install.sh
```

### Launch the Dashboard
To launch the dashboard cd into the node-red directory, then use:
```sh
cd dashboard
. launch.sh
```

Access the dashboard workspace on: `http://localhost:1881`

Access the dashboard UI on: `http://localhost:1881/ui`

### Uninstall Dashboard
follow the below to uninstall the setup:
```sh
cd dashboard
. uninstall.sh
```
