import requests
import json
import time
import random

# --- Configuration ---
SERVER_URL = "http://127.0.0.1:8080/data"
SEND_INTERVAL_SECONDS = 10  # Send data every 10 seconds

def main():
    """Simulates an ESP32 sensor sending data to the central server."""
    print(f"Starting ESP32 Sensor Simulator. Sending data to {SERVER_URL} every {SEND_INTERVAL_SECONDS} seconds.")
    print("Press Ctrl+C to stop.")

    while True:
        try:
            # Generate some random but realistic data
            rssi = -random.randint(30, 110)
            snr = round(random.uniform(-5.0, 10.0), 1)
            packet_size = random.choice([16, 32, 64])

            payload = {
                "rssi": rssi,
                "snr": snr,
                "size": packet_size
            }

            print(f"Sending data: {payload}")

            response = requests.post(SERVER_URL, json=payload, timeout=5)
            response.raise_for_status()  # Raise an exception for bad status codes

            print(f"Server responded with status code: {response.status_code}")
            print(f"Response body: {response.json()}")

        except requests.exceptions.RequestException as e:
            print(f"Error sending data: {e}")

        except KeyboardInterrupt:
            print("\nSimulator stopped.")
            break

        time.sleep(SEND_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
