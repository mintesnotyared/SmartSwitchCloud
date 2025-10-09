import time
import paho.mqtt.client as mqtt

# ---------- MQTT Settings ----------
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_CLIENT = "SmartSwitchCloudClient"

# Relay topics
RELAY_TOPICS = ["esp12f/relay1", "esp12f/relay2", "esp12f/relay3", "esp12f/relay4"]

# Keep track of last sent command
last_command = [None, None, None, None]

# ---------- MQTT Callbacks ----------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker")
        # Subscribe to status topics to know relay states
        for topic in RELAY_TOPICS:
            client.subscribe(topic + "/status")
    else:
        print("⚠️ Failed to connect, return code:", rc)

def on_message(client, userdata, msg):
    global last_command
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"📩 Message received: {topic} -> {payload}")

    # Update local last command if ESP reports state change
    for i, relay in enumerate(RELAY_TOPICS):
        if topic == relay + "/status":
            last_command[i] = payload

# ---------- MQTT Client Setup ----------
client = mqtt.Client(MQTT_CLIENT)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# ---------- Function to Send Relay Command ----------
def send_relay(relay_index, state):
    topic = RELAY_TOPICS[relay_index]
    client.publish(topic, state, qos=1)
    last_command[relay_index] = state
    print(f"➡️ Sent {state} to {topic}")

# ---------- Function to Restore ESP Wi-Fi ----------
def restore_esp_wifi():
    client.publish("esp12f/resetwifi", "RESET", qos=1)
    print("🧹 Wi-Fi restore command sent to ESP")

# ---------- Example Usage ----------
if __name__ == "__main__":
    time.sleep(2)  # Wait for MQTT connection

    print("🔹 Sending example relay commands...")
    send_relay(0, "ON")   # Relay 1 ON
    send_relay(1, "OFF")  # Relay 2 OFF
    send_relay(2, "ON")   # Relay 3 ON
    send_relay(3, "OFF")  # Relay 4 OFF

    time.sleep(1)
    print("🔹 Restore ESP Wi-Fi if needed")
    # restore_esp_wifi()

    print("📡 Running... Press Ctrl+C to exit")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n❌ Exiting...")
        client.loop_stop()
        client.disconnect()
