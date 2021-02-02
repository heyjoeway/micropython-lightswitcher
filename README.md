# micropython-lightswitcher
A quick n' dirty micropython script to control light switches using MQTT and servos. (to be paired with Home Assistant)
For the physical part of this project (not done by me) see here: https://www.thingiverse.com/thing:1156995

## Config
This assumes you know how to set up Home Assistant and Mosquitto (or another compatible MQTT server). You'll also need to have already flashed MicroPython to whatever device you're using.

## Home Assistant Config Example
Loosely follows the included `settings.example.json`:
```yaml
switch:
  - platform: mqtt
    unique_id: example_switch1
    name: "Example Switch"
    state_topic: "example/switch1/state"
    command_topic: "example/switch1/set"
    availability:
      - topic: "example/switch1/available"
    payload_on: "ON"
    payload_off: "OFF"
    state_on: "ON"
    state_off: "OFF"
    optimistic: false
    qos: 0
    retain: true
```

### Micropython
Upload `settings.json` (use `settings.example.json` as a guide) using WebREPL (http://micropython.org/webrepl/).
Then upload `main.py`.
