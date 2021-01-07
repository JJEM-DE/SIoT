import random

from paho.mqtt import client as mqtt_client


broker = 'broker.emqx.io'
port = 1883
topic = "/JM/phone/#"
# generate client ID with pub prefix randomly
client_id = 'JoshPi'
xvar = False
yvar = False
zvar = False
x = 0
y = 0
z = 0

def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        if msg.topic == "/JM/phone/Gyroscope/x":
            global x
            x = float(msg.payload.decode())
            global xvar
            xvar = True
        elif msg.topic == "/JM/phone/Gyroscope/y":
            global y
            y = float(msg.payload.decode())
            global yvar
            yvar = True
        elif msg.topic == "/JM/phone/Gyroscope/z":
            global z
            z = float(msg.payload.decode())
            global zvar
            zvar = True
        elif msg.topic == "/JM/phone/noise/decibels":
            print("Noise level: {:0.2f}".format(float(msg.payload.decode())))
        if xvar == True and yvar == True and zvar == True:
            print("Gyroscope: ({:0.2f},{:0.2f},{:0.2f})".format(x,y,z))
            xvar = False
            yvar = False
            zvar = False


    client.subscribe(topic)
    client.on_message = on_message


def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()



run()
