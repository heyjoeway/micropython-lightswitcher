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

# =============================================================================

from umqtt.robust import MQTTClient

def mqtt_callback(topic, payload):
    print((topic, payload))
    topic = topic.decode('utf-8')
    payload = payload.decode('utf-8')
    if topic == settings["mqtt"]["topic"] + settings["mqtt"]["subtopic_set"]:
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

SLEEP_TIME = 0.25 # sec
AVAIL_INTERVAL = 10 # sec

avail_timer = AVAIL_INTERVAL

while True:
    time.sleep(SLEEP_TIME)
    
    wifi_ensure_connected()
    mqtt.check_msg()
    avail_timer += SLEEP_TIME
    if avail_timer >= AVAIL_INTERVAL:
        avail_timer = 0
        mqtt.publish(settings["mqtt"]["topic"] + settings["mqtt"]["subtopic_avail"], "online")
