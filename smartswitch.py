from flask import Flask
import paho.mqtt.client as mqtt

app = Flask(__name__)

# MQTT Settings
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("✅ Connected to MQTT Broker with code:", rc)

client.on_connect = on_connect
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

@app.route('/')
def home():
    return "Smart Switch Cloud is Live! MQTT Connected ✅"

@app.route('/on/<int:relay_id>')
def turn_on(relay_id):
    topic = f"esp12f/relay{relay_id}"
    client.publish(topic, "ON")
    return f"Relay {relay_id} turned ON"

@app.route('/off/<int:relay_id>')
def turn_off(relay_id):
    topic = f"esp12f/relay{relay_id}"
    client.publish(topic, "OFF")
    return f"Relay {relay_id} turned OFF"

@app.route('/status/<int:relay_id>')
def status(relay_id):
    topic = f"esp12f/relay{relay_id}/status"
    client.publish(topic, "REQUEST")
    return f"Requested status of relay {relay_id}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
