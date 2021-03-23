import ujson

settings = None
with open("settings.json", 'r') as f:
    settings = ujson.loads(f.read())

# =============================================================================

import network
import time

sta_if = None
def wifi_connect():
    global sta_if
    global ap_if

    # Disable access point
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect(settings["wifi"]["ssid"], settings["wifi"]["pass"]) # Connect to an AP
    
    for i in range(20):
        if sta_if.isconnected():
            return
        time.sleep(1)

def wifi_ensure_connected():
    while not sta_if.isconnected():
        wifi_connect()

wifi_connect()

import webrepl

# =============================================================================

import machine
def init_switch_servo():
    global pin
    global pwm
    pin = machine.Pin(settings["servo"]["pin"])
    pwm = machine.PWM(pin)
    pwm.freq(50)

    # Power on self test (optional)
    #pwm.duty(settings["servo"]["duty_on"])
    #time.sleep(1)
    #pwm.duty(0)
    #time.sleep(.1)
    #pwm.duty(settings["servo"]["duty_off"])
    #time.sleep(1)
    #pwm.duty(0)
    #time.sleep(.1)

def mqtt_callback_switch_servo(topic, payload):
    if topic != settings["mqtt"]["topic"] + settings["mqtt"]["subtopic_set"]:
        return

    if payload == "ON":
        print("Turning on")
        mqtt.publish(settings["mqtt"]["topic"] + settings["mqtt"]["subtopic_state"], "ON")
        pwm.duty(settings["servo"]["duty_on"])
        time.sleep(0.5)
        pwm.duty(settings["servo"]["duty_mid"])
        time.sleep(0.5)
        pwm.duty(0)
    elif payload == "OFF":
        print("Turning off")
        mqtt.publish(settings["mqtt"]["topic"] + settings["mqtt"]["subtopic_state"], "OFF")
        pwm.duty(settings["servo"]["duty_off"])
        time.sleep(0.5)
        pwm.duty(settings["servo"]["duty_mid"])
        time.sleep(0.5)
        pwm.duty(0)


def init_button():
    global pin
    global button_value
    global button_switch_state
    pin = machine.Pin(settings["button"]["pin"], machine.Pin.IN, machine.Pin.PULL_UP)
    button_value = 1
    button_switch_state = True


def loop_button():
    global pin
    global button_value
    global button_switch_state
    pin_value = pin.value()
    if button_value != pin_value:
        button_value = pin_value
        if button_value == 0:
            button_switch_state = not button_switch_state
            msg = "ON" if button_switch_state else "OFF"
            print(msg)
            mqtt.publish(settings["mqtt"]["topic"] + settings["mqtt"]["subtopic_state"], msg)


types = {
    "button": {
        "init": init_button,
        "loop": loop_button
    },
    "switch_servo": {
        "init": init_switch_servo,
        "mqtt_callback": mqtt_callback_switch_servo
    }
}

type_data = types.get(settings["type"], None)
if type_data:
    type_initfunc = type_data.get("init", None)
    if type_initfunc:
        type_initfunc()

# =============================================================================
from umqtt.robust import MQTTClient

def mqtt_callback(topic, payload):
    print((topic, payload))
    topic = topic.decode('utf-8')
    payload = payload.decode('utf-8')

    type_data = types.get(settings["type"], None)
    if type_data:
        type_mqttfunc = type_data.get("mqtt_callback", None)
        if type_mqttfunc:
            type_mqttfunc(topic, payload)

mqtt = MQTTClient(
    settings["mqtt"]["clientId"],
    settings["mqtt"]["host"],
    user=settings["mqtt"]["user"],
    password=settings["mqtt"]["pass"],
    port=settings["mqtt"]["port"]
)
mqtt.set_callback(mqtt_callback)
mqtt.connect()
mqtt.subscribe(settings["mqtt"]["topic"] + settings["mqtt"]["subtopic_set"])

mqtt.publish(settings["mqtt"]["topic"] + settings["mqtt"]["subtopic_state"], "ON")

SLEEP_TIME = 1.0 / 60.0 # sec

AVAIL_INTERVAL = 10 # sec
avail_timer = AVAIL_INTERVAL

MSG_INTERVAL = 0.25 # sec
msg_timer = MSG_INTERVAL

def loop():
    type_data = types.get(settings["type"], None)
    if type_data:
        type_loopfunc = type_data.get("loop", None)
        if type_loopfunc:
            type_loopfunc()

while True:
    time.sleep(SLEEP_TIME)

    loop()

    avail_timer += SLEEP_TIME
    if avail_timer >= AVAIL_INTERVAL:
        avail_timer = 0
        wifi_ensure_connected()
        mqtt.publish(settings["mqtt"]["topic"] + settings["mqtt"]["subtopic_avail"], "online")

    msg_timer += SLEEP_TIME
    if msg_timer >= MSG_INTERVAL:
        msg_timer = 0
        mqtt.check_msg()