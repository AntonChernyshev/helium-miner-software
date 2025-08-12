from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import datetime

app = Flask(__name__)

# --- In-memory data stores (for demonstration purposes) ---
received_data = []
monitored_miners = {}

# --- Configuration ---
GHOST_TIMEOUT_SECONDS = 75  # 75 seconds for testing

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Helium Network Anomaly Detector</title>
    <meta http-equiv="refresh" content="10">
    <style>
        body { font-family: sans-serif; margin: 2em; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 2em;}
        th, td { border: 1px solid #dddddd; text-align: left; padding: 8px; }
        th { background-color: #f2f2f2; }
        .container { display: flex; gap: 2em; }
        .col { flex: 1; }
        form { margin-bottom: 2em; }
        .status-ghost { color: red; font-weight: bold; }
        .status-ok { color: green; }
    </style>
</head>
<body>
    <h1>Helium Network Anomaly Detector</h1>

    <div class="container">
        <div class="col">
            <h2>Register "Ghost" Miner for Monitoring</h2>
            <form action="/add_miner" method="post">
                <label for="mac">Miner MAC:</label><br>
                <input type="text" id="mac" name="mac" required><br>
                <label for="lat">Claimed Latitude:</label><br>
                <input type="text" id="lat" name="lat" required><br>
                <label for="lon">Claimed Longitude:</label><br>
                <input type="text" id="lon" name="lon" required><br><br>
                <input type="submit" value="Monitor Miner">
            </form>

            <h2>Monitored "Ghost" Miners</h2>
            {% if monitored_miners %}
            <table>
                <tr>
                    <th>MAC</th>
                    <th>Claimed Location</th>
                    <th>Status</th>
                    <th>Last Heard</th>
                </tr>
                {% for mac, miner in monitored_miners.items() %}
                <tr>
                    <td>{{ mac }}</td>
                    <td>{{ "%.4f"|format(miner.lat) }}, {{ "%.4f"|format(miner.lon) }}</td>
                    <td class="status-{{ 'ghost' if miner.is_ghost else 'ok' }}">{{ miner.status }}</td>
                    <td>{{ miner.last_heard.strftime('%Y-%m-%d %H:%M:%S') if miner.last_heard else 'Never' }}</td>
                </tr>
                {% endfor %}
            </table>
            {% else %}
            <p>No miners are being monitored.</p>
            {% endif %}
        </div>

        <div class="col">
            <h2>Live Data from ESP32 Sensors</h2>
            <table>
                <tr>
                    <th>Timestamp</th>
                    <th>RSSI (dBm)</th>
                    <th>SNR (dB)</th>
                    <th>Packet Size (bytes)</th>
                    <th>Sensor IP</th>
                </tr>
                {% for item in data %}
                <tr>
                    <td>{{ item.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</td>
                    <td>{{ item.rssi }}</td>
                    <td>{{ item.snr }}</td>
                    <td>{{ item.size }}</td>
                    <td>{{ item.ip }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
</body>
</html>
"""

def check_ghosts():
    """Checks for ghost miners and updates their status."""
    now = datetime.datetime.now()
    for mac, miner in monitored_miners.items():
        if miner.get('last_heard'):
            if (now - miner['last_heard']).total_seconds() > GHOST_TIMEOUT_SECONDS:
                miner['status'] = 'Suspected Ghost!'
                miner['is_ghost'] = True
                print(f"Miner {mac} is now a suspected ghost.")

@app.route('/')
def index():
    """Serves the main page with monitored miners and received data."""
    check_ghosts()  # Check for ghosts every time the page is loaded
    return render_template_string(HTML_TEMPLATE, data=received_data, monitored_miners=monitored_miners)

@app.route('/add_miner', methods=['POST'])
def add_miner():
    """Endpoint to add a new miner to monitor."""
    mac = request.form.get('mac')
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    if mac and lat and lon:
        monitored_miners[mac] = {
            'lat': float(lat),
            'lon': float(lon),
            'last_heard': datetime.datetime.now(), # Assume heard now to avoid immediate ghost status
            'status': 'Monitoring...',
            'is_ghost': False
        }
        print(f"Started monitoring miner: {mac}")
    return redirect(url_for('index'))


@app.route('/data', methods=['POST'])
def receive_data():
    """API endpoint to receive data from ESP32 sensors."""
    if not request.is_json:
        return jsonify({"error": "Invalid request: not JSON"}), 400

    data = request.get_json()

    if 'rssi' not in data or 'snr' not in data or 'size' not in data:
        return jsonify({"error": "Missing required fields"}), 400

    now = datetime.datetime.now()
    data['timestamp'] = now
    data['ip'] = request.remote_addr

    # For now, any received packet updates the 'last_heard' for ALL monitored miners.
    # A real implementation would check location proximity.
    for mac in monitored_miners:
        monitored_miners[mac]['last_heard'] = now
        monitored_miners[mac]['status'] = 'Active'
        monitored_miners[mac]['is_ghost'] = False

    print(f"Received data: {data}")
    received_data.insert(0, data)
    if len(received_data) > 100:
        received_data.pop()

    return jsonify({"status": "success", "received": data}), 201

if __name__ == '__main__':
    # Run the Flask server
    app.run(host='0.0.0.0', port=8080, debug=False)
