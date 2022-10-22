import RPi.GPIO as GPIO
import time, threading
from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory, PNOperationType
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

pnconfig = PNConfiguration()

pnconfig.subscribe_key = 'Your subscribe key'
pnconfig.publish_key = 'Your publish key'
pnconfig.user_id = 'Unique ID for the device'
pubnub = PubNub(pnconfig)

my_channel = "johns_sd3b_pi_channel"
sensors_list = ["buzzer"]
data = {}

def my_publish_callback(envelope, status):
    # check was the request successfully completed
    if not status.is_error():
        pass # Message was sucessfully published
    else:
        pass # Handle the publish message error. Can more details about the error by looking at the 'cateogey' property


class MySubscribeCallback(SubscribeCallback):
    def presence(self, pubnub, presence):
        pass # handle incoming presence data

    def status(self, pubnub, status):
        if status.category == PNStatusCategory.PNUnexpectedDisconnectCategory:
            pass # What should you do if connection drops

        elif status.category == PNStatusCategory.PNConnectedCategory:
            # Connect event. Publish something
            pubnub.publish().channel(my_channel).message("Hello World").pn_async(my_publish_callback)
        
        elif status.category == PNStatusCategory.PNReconnectedCategory:
            pass
            # This happens when disconnected and then reconnected

        elif status.category == PNStatusCategory.PNDecryptionErrorCategory:
            pass
            # Client configured to encrypt messages and the live feed recevies plain text

    def message(self, pubnub, message):
        try:
            print(message.message, " : ", type(message.message))
            msg = message.message
            print("Received json: ", msg)
            keys = list(msg.keys())
            if(key[0]) == "event": #{"event" : {"sensors_name":True}}
                self.handle_event(msg)
        except Exception as e:
            print("Received: ", message.message)
            print(e)


    def handle_event(self, msg):
        global data
        event_data = msg["event"]
        keys = list(event_data.keys())
        if key[0] in sensors_list:
            if event_data[key[0]] is True:
                data["alarm"] = True
            elif event_data[key[0]] is False:
                data["alarm"] = False

def publish(pub_channel, msg):
    pubnub.publish().channel(pub_channel).message(msg).pn_async(my_publish_callback)

PIR_pin = 23
Buzzer_pin = 24

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_pin, GPIO.IN)
GPIO.setup(Buzzer_pin, GPIO.OUT)

def beep(repeat):
    for i in range(0, repeat):
        for pulse in range(60):
            GPIO.output(Buzzer_pin, True)
            time.sleep(0.001)
            GPIO.output(Buzzer_pin, False)
            time.sleep(0.001)
        time.sleep(0.02)


def motion_detection():
    data["alarm"] = False
    trigger = False
    while True:
        if GPIO.input(PIR_pin):
            print("Motion detected")
            beep(4)
            trigger = True
            publish(my_channel, {"motion":"Yes"})
            time.sleep(1)
        elif trigger:
            publish(my_channel, {"motion":"No"})
            trigger = False
        if data["alarm"]:
            beep(2)


if __name__ == '__main__':
    sensors_thread = threading.Thread(target=motion_detection)
    sensors_thread.start()
    pubnub.add_listener(MySubscribeCallback())
    pubnub.subscribe().channels(my_channel).execute()
