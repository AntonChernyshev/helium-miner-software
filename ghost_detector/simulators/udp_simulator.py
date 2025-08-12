import socket
import json
import random
import time
import argparse

def create_stat_packet(mac, stat_data):
    """Creates a PUSH_DATA packet with a stat object."""
    token = random.randint(0, 0xFFFF)

    try:
        mac_bytes = bytes.fromhex(mac.replace(":", ""))
        if len(mac_bytes) != 8:
            raise ValueError("MAC address must be 8 bytes long")
    except ValueError as e:
        print(f"Error: Invalid MAC address format. Please use an 8-byte hex string (e.g., 0102030405060708). Details: {e}")
        return None

    # Protocol version (2), token, PUSH_DATA identifier (0x00)
    header = b'\x02' + token.to_bytes(2, 'little') + b'\x00' + mac_bytes

    json_payload = json.dumps({"stat": stat_data})

    return header + json_payload.encode('utf-8')

def main(args):
    """Continuously sends stat packets to the target."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print("UDP Gateway Simulator started.")
    print(f"Target: {args.ip}:{args.port}")
    print(f"Gateway MAC: {args.mac}")
    print(f"Location: Lat={args.lat}, Lon={args.lon}, Alt={args.alt}")
    print(f"Sending packets every {args.interval} seconds.")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            stat_payload = {
                "time": time.strftime("%Y-%m-%d %H:%M:%S GMT", time.gmtime()),
                "lati": args.lat,
                "long": args.lon,
                "alti": args.alt,
                "rxnb": 0,
                "rxok": 0,
                "rxfw": 0,
                "ackr": 100.0,
                "dwnb": 0,
                "txnb": 0
            }

            packet = create_stat_packet(args.mac, stat_payload)

            if packet:
                print(f"[{time.strftime('%H:%M:%S')}] Sending stat packet...")
                # print(f"Payload: {json.dumps({'stat': stat_payload})}") # Uncomment for verbose payload
                sock.sendto(packet, (args.ip, args.port))

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\nSimulator stopped by user.")
    finally:
        sock.close()
        print("Socket closed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LoRa Gateway UDP Simulator for Helium")
    parser.add_argument('--mac', type=str, default="AABBCCDDEEFF0011", help="Gateway MAC address (8-byte hex string)")
    parser.add_argument('--lat', type=float, default=40.7128, help="Latitude of the gateway")
    parser.add_argument('--lon', type=float, default=-74.0060, help="Longitude of the gateway")
    parser.add_argument('--alt', type=int, default=10, help="Altitude of the gateway in meters")
    parser.add_argument('--ip', type=str, default="127.0.0.1", help="Target IP address of the server")
    parser.add_argument('--port', type=int, default=1680, help="Target port of the server")
    parser.add_argument('--interval', type=int, default=30, help="Interval in seconds to send packets")

    args = parser.parse_args()
    main(args)
