# Combined Scheduler: Timer + Alarm + Calendar for ESP12F
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime, timedelta
import threading
import os

class CombinedScheduler:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # Store all schedules
        self.timers = []
        self.alarms = []
        self.events = []
        
        # Data files
        self.timers_file = "active_timers.json"
        self.events_file = "calendar_events.json"
        
        # MQTT topics - Unified for ESP12F
        self.topic_switch_base = "smartSwitch/app/cmd"
        self.topic_status = "smart/status"
        
        # Timer topics
        self.topic_add_timer = "philos/timer/add"
        self.topic_cancel_timer = "philos/timer/cancel"
        self.topic_list_timers = "philos/timer/list"
        
        # Alarm topics
        self.topic_add_alarm = "smart/alarm/add"
        self.topic_delete_alarm = "smart/alarm/delete"
        self.topic_list_alarms = "smart/alarm/list"
        
        # Calendar topics
        self.topic_add_event = "philos/calendar/add"
        self.topic_delete_event = "philos/calendar/delete"
        self.topic_list_events = "philos/calendar/list"
        
        # Load existing data
        self.load_timers()
        self.load_events()
        
        print("🤖 Combined Scheduler: Timer + Alarm + Calendar Initialized")
        print(f"📊 Loaded {len(self.timers)} timers, {len(self.alarms)} alarms, {len(self.events)} events")
    
    # ========== TIMER FUNCTIONS ==========
    def load_timers(self):
        try:
            if os.path.exists(self.timers_file):
                with open(self.timers_file, 'r') as f:
                    saved_timers = json.load(f)
                    for timer in saved_timers:
                        timer['end_time'] = datetime.fromisoformat(timer['end_time'])
                    self.timers = saved_timers
                print(f"✅ Loaded {len(self.timers)} timers")
        except Exception as e:
            print(f"❌ Error loading timers: {e}")
            self.timers = []
    
    def save_timers(self):
        try:
            timers_to_save = []
            for timer in self.timers:
                timer_copy = timer.copy()
                timer_copy['end_time'] = timer['end_time'].isoformat()
                timers_to_save.append(timer_copy)
            with open(self.timers_file, 'w') as f:
                json.dump(timers_to_save, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving timers: {e}")
    
    def add_timer(self, payload):
        try:
            timer_data = json.loads(payload)
            required = ['id', 'hours', 'minutes', 'seconds', 'switch', 'action']
            if not all(field in timer_data for field in required):
                print("❌ Invalid timer data")
                return
            
            duration = timedelta(
                hours=timer_data['hours'],
                minutes=timer_data['minutes'],
                seconds=timer_data['seconds']
            )
            end_time = datetime.now() + duration
            
            timer = {
                'id': timer_data['id'],
                'duration': f"{timer_data['hours']:02d}:{timer_data['minutes']:02d}:{timer_data['seconds']:02d}",
                'end_time': end_time,
                'switch': timer_data['switch'],
                'action': timer_data['action'],
                'label': timer_data.get('label', 'Timer'),
                'created_at': datetime.now(),
                'active': True
            }
            
            self.timers.append(timer)
            self.save_timers()
            remaining = end_time - datetime.now()
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            print(f"⏱️ Timer added: {timer['label']}")
            print(f"   Switch {timer['switch']} -> {timer['action']} in {hours:02d}:{minutes:02d}:{seconds:02d}")
            
            self.client.publish(self.topic_status, f"TIMER_ADDED:{timer['id']}")
            
        except Exception as e:
            print(f"💥 Error adding timer: {e}")
    
    def cancel_timer(self, payload):
        try:
            timer_id = payload
            initial_count = len(self.timers)
            self.timers = [t for t in self.timers if t['id'] != timer_id]
            
            if len(self.timers) < initial_count:
                self.save_timers()
                print(f"🗑 Timer {timer_id} cancelled")
                self.client.publish(self.topic_status, f"TIMER_CANCELLED:{timer_id}")
            else:
                print(f"⚠️ Timer {timer_id} not found")
                
        except Exception as e:
            print(f"💥 Error cancelling timer: {e}")
    
    # ========== ALARM FUNCTIONS ==========
    def add_alarm(self, payload):
        try:
            alarm_data = json.loads(payload)
            required = ['channel', 'hour', 'minute', 'action', 'days']
            if not all(field in alarm_data for field in required):
                print("❌ Invalid alarm data")
                return
            
            alarm = {
                'id': len(self.alarms) + 1,
                'channel': alarm_data['channel'],
                'hour': alarm_data['hour'],
                'minute': alarm_data['minute'],
                'action': alarm_data['action'],
                'days': alarm_data['days'],
                'enabled': True
            }
            
            self.alarms.append(alarm)
            print(f"⏰ Alarm added: Switch {alarm['channel']} - {alarm['hour']:02d}:{alarm['minute']:02d} - {alarm['action']}")
            self.client.publish(self.topic_status, f"ALARM_ADDED:{alarm['channel']}:{alarm['hour']:02d}:{alarm['minute']:02d}")
            
        except Exception as e:
            print(f"💥 Error adding alarm: {e}")
    
    def delete_alarm(self, payload):
        try:
            alarm_id = int(payload)
            self.alarms = [a for a in self.alarms if a['id'] != alarm_id]
            print(f"🗑 Alarm {alarm_id} deleted")
            self.client.publish(self.topic_status, f"ALARM_DELETED:{alarm_id}")
        except:
            print("❌ Error deleting alarm")
    
    # ========== CALENDAR FUNCTIONS ==========
    def load_events(self):
        try:
            if os.path.exists(self.events_file):
                with open(self.events_file, 'r') as f:
                    self.events = json.load(f)
                print(f"✅ Loaded {len(self.events)} calendar events")
        except Exception as e:
            print(f"❌ Error loading events: {e}")
            self.events = []
    
    def save_events(self):
        try:
            with open(self.events_file, 'w') as f:
                json.dump(self.events, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving events: {e}")
    
    def add_event(self, payload):
        try:
            event_data = json.loads(payload)
            required = ['id', 'date', 'time', 'switch', 'action', 'repeatMode']
            if not all(field in event_data for field in required):
                print("❌ Invalid event data")
                return
            
            event_datetime_str = f"{event_data['date']} {event_data['time']}"
            event_datetime = datetime.strptime(event_datetime_str, "%Y-%m-%d %H:%M")
            
            event = {'id': event_data['id'],
                'datetime': event_datetime.strftime("%Y-%m-%d %H:%M"),
                'switch': event_data['switch'],
                'action': event_data['action'],
                'label': event_data.get('label', 'Calendar Event'),
                'repeatMode': event_data['repeatMode'],
                'lastExecuted': None,
                'enabled': True
            }
            self.events.append(event)
            self.save_events()
            
            print(f"📅 Event added: {event['label']}")
            print(f"   {event['datetime']} - Switch {event['switch']} - {event['action']}")
            self.client.publish(self.topic_status, f"CALENDAR_ADDED:{event['id']}")
            
        except Exception as e:
            print(f"💥 Error adding event: {e}")
    
    def delete_event(self, payload):
        try:
            event_id = payload
            initial_count = len(self.events)
            self.events = [e for e in self.events if e['id'] != event_id]
            
            if len(self.events) < initial_count:
                self.save_events()
                print(f"🗑 Event {event_id} deleted")
                self.client.publish(self.topic_status, f"CALENDAR_DELETED:{event_id}")
            else:
                print(f"⚠️ Event {event_id} not found")
                
        except Exception as e:
            print(f"💥 Error deleting event: {e}")
    
    # ========== SCHEDULE CHECKING ==========
    def check_timers(self):
        now = datetime.now()
        timers_to_remove = []
        
        for timer in self.timers:
            if timer['active'] and now >= timer['end_time']:
                print(f"🎯 TIMER COMPLETED: {timer['label']}")
                switch_topic = f"{self.topic_switch_base}{timer['switch']}"
                self.client.publish(switch_topic, timer['action'])
                self.client.publish(self.topic_status, f"TIMER_COMPLETED:{timer['id']}")
                timer['active'] = False
                timers_to_remove.append(timer)
        
        if timers_to_remove:
            self.timers = [t for t in self.timers if t not in timers_to_remove]
            self.save_timers()
    
    def check_alarms(self):
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        current_day = now.weekday() + 1  # Monday=1, Sunday=7
        
        for alarm in self.alarms:
            if (alarm['enabled'] and 
                alarm['hour'] == current_hour and 
                alarm['minute'] == current_minute and
                current_day in alarm['days']):
                
                print(f"🚨 ALARM TRIGGERED: Switch {alarm['channel']}")
                switch_topic = f"{self.topic_switch_base}{alarm['channel']}"
                self.client.publish(switch_topic, alarm['action'])
                self.client.publish(self.topic_status, f"ALARM_TRIGGERED:{alarm['channel']}")
    
    def should_execute_event(self, event, now):
        if not event['enabled']:
            return False
        
        event_time = datetime.strptime(event['datetime'], "%Y-%m-%d %H:%M")
        current_time = now.replace(second=0, microsecond=0)
        event_time = event_time.replace(year=now.year, month=now.month, day=now.day)
        
        if event_time != current_time:
            return False
        
        repeat_mode = event['repeatMode']
        original_event_date = datetime.strptime(event['datetime'], "%Y-%m-%d %H:%M")
        
        if repeat_mode == 'once':
            return original_event_date.date() == now.date()
        elif repeat_mode == 'daily':
            return True
        elif repeat_mode == 'weekly':
            return original_event_date.weekday() == now.weekday()
        elif repeat_mode == 'monthly':
            return original_event_date.day == now.day
        elif repeat_mode == 'yearly':
            return (original_event_date.month == now.month and 
                    original_event_date.day == now.day)
        
        return False
    
    def check_events(self):
        now = datetime.now()
        
        for event in self.events:
            if self.should_execute_event(event, now):
                last_executed = event.get('lastExecuted')
                if last_executed and last_executed == now.strftime("%Y-%m-%d %H:%M"):
                    continue
                    
                print(f"🎯 CALENDAR EVENT: {event['label']}")
                switch_topic = f"{self.topic_switch_base}{event['switch']}"
                self.client.publish(switch_topic, event['action'])
                self.client.publish(self.topic_status, f"CALENDAR_TRIGGERED:{event['id']}")
                
                event['lastExecuted'] = now.strftime("%Y-%m-%d %H:%M")
                self.save_events()
    
    # ========== MQTT HANDLERS ==========
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Connected to MQTT broker")
            
            # Subscribe to all topics
            client.subscribe(self.topic_add_timer)
            client.subscribe(self.topic_cancel_timer)
            client.subscribe(self.topic_list_timers)
            client.subscribe(self.topic_add_alarm)
            client.subscribe(self.topic_delete_alarm)
            client.subscribe(self.topic_list_alarms)
            client.subscribe(self.topic_add_event)
            client.subscribe(self.topic_delete_event)
            client.subscribe(self.topic_list_events)
            
            print("📡 Subscribed to all scheduler topics")
            self.start_schedule_checker()
            
        else:
            print(f"❌ Connection failed with code: {rc}")
    
    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            if topic == self.topic_add_timer:
                self.add_timer(payload)
            elif topic == self.topic_cancel_timer:
                self.cancel_timer(payload)
            elif topic == self.topic_add_alarm:
                self.add_alarm(payload)
            elif topic == self.topic_delete_alarm:
                self.delete_alarm(payload)
            elif topic == self.topic_add_event:
                self.add_event(payload)
            elif topic == self.topic_delete_event:
                self.delete_event(payload)
            elif topic in [self.topic_list_timers, self.topic_list_alarms, self.topic_list_events]:
                self.list_all()
                
        except Exception as e:
            print(f"💥 Error processing message: {e}")
    
    def list_all(self):
        print("\n📋 COMBINED SCHEDULES:")
        print(f"⏱️  Timers: {len(self.timers)}")
        print(f"⏰  Alarms: {len(self.alarms)}")
        print(f"📅 Events: {len(self.events)}")
        print()
    
    def start_schedule_checker(self):
        def schedule_check_loop():
            while True:
                self.check_timers()
                self.check_alarms()
                self.check_events()
                time.sleep(1)
        
        thread = threading.Thread(target=schedule_check_loop, daemon=True)
        thread.start()
        print("⏰ Combined schedule checker started")
    
    def start(self, broker='broker.emqx.io', port=1883):
        try:
            print(f"🚀 Connecting to MQTT broker: {broker}:{port}")
            self.client.connect(broker, port, 60)
            
            print("\n" + "="*70)
            print("🤖 COMBINED SCHEDULER - TIMER + ALARM + CALENDAR")
            print("="*70)
            print("📡 MQTT Topics:")
            print(f"   Timer:    {self.topic_add_timer}")
            print(f"   Alarm:    {self.topic_add_alarm}")
            print(f"   Calendar: {self.topic_add_event}")
            print(f"   Commands: {self.topic_switch_base}1-4")
            print(f"   Status:   {self.topic_status}")
            print("="*70 + "\n")
            
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            print("\n🛑 Combined scheduler stopped by user")
            self.client.disconnect()
        except Exception as e:
            print(f"💥 Failed to start: {e}")

if __name__ == "__main__":
    scheduler = CombinedScheduler()
    scheduler.start()


# from flask import Flask
# import paho.mqtt.client as mqtt

# app = Flask(__name__)

# # MQTT Settings
# MQTT_BROKER = "test.mosquitto.org"
# MQTT_PORT = 1883
# client = mqtt.Client()

# def on_connect(client, userdata, flags, rc):
#     print("✅ Connected to MQTT Broker with code:", rc)

# client.on_connect = on_connect
# client.connect(MQTT_BROKER, MQTT_PORT, 60)
# client.loop_start()

# @app.route('/')
# def home():
#     return "Smart Switch Cloud is Live! MQTT Connected ✅"

# @app.route('/on/<int:relay_id>')
# def turn_on(relay_id):
#     topic = f"esp12f/relay{relay_id}"
#     client.publish(topic, "ON")
#     return f"Relay {relay_id} turned ON"

# @app.route('/off/<int:relay_id>')
# def turn_off(relay_id):
#     topic = f"esp12f/relay{relay_id}"
#     client.publish(topic, "OFF")
#     return f"Relay {relay_id} turned OFF"

# @app.route('/status/<int:relay_id>')
# def status(relay_id):
#     topic = f"esp12f/relay{relay_id}/status"
#     client.publish(topic, "REQUEST")
#     return f"Requested status of relay {relay_id}"

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=10000)
