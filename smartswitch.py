import paho.mqtt.client as mqtt

BROKER = "test.mosquitto.org"
PORT = 1883

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("esp12f/#")  # Subscribe to all relay topics

def on_message(client, userdata, msg):
    print(f"{msg.topic} -> {msg.payload.decode()}")

client = mqtt.Client("PythonTester")
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)

# Example: toggle relay 1
client.publish("esp12f/relay1", "ON")

client.loop_forever()