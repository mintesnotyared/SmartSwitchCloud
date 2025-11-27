from flask import Flask, jsonify
import threading
import time
from smartswitch import CombinedScheduler

app = Flask(__name__)
scheduler = None

@app.route('/')
def home():
    return jsonify({
        "status": "Running",
        "service": "Smart Switch Scheduler",
        "timers": len(scheduler.timers) if scheduler else 0,
        "alarms": len(scheduler.alarms) if scheduler else 0,
        "events": len(scheduler.events) if scheduler else 0
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

def start_scheduler():
    global scheduler
    scheduler = CombinedScheduler()
    scheduler.start()

if __name__ == '__main__':
    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
