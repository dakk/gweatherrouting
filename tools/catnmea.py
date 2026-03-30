import os
import socket
import sys
import time

nmea_file = None
port = 10110

for arg in sys.argv[1:]:
    if arg.isdigit():
        port = int(arg)
    else:
        nmea_file = arg

if nmea_file:
    f = open(nmea_file, "r").read().split("\n")
else:
    samples_dir = os.path.join(os.path.dirname(__file__), "samples")
    sample_ais = (
        open(os.path.join(samples_dir, "ais_23_03_2026.nmea"), "r").read().split("\n")
    )
    data_12_12 = (
        open(os.path.join(samples_dir, "data_12_12_2021.nmea"), "r").read().split("\n")
    )
    f = [line for pair in zip(sample_ais, data_12_12) for line in pair]
    f += sample_ais[len(data_12_12) :] + data_12_12[len(sample_ais) :]

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("", port))
s.listen(1)

print(f"NMEA server listening on port {port} ({len(f)} sentences loaded)")
print("Waiting for connection...")

line_index = 0

try:
    while True:
        conn, addr = s.accept()
        print(f"Connected by {addr}, resuming from sentence {line_index}")
        try:
            with conn:
                while True:
                    conn.send(f[line_index].encode("ascii") + b"\n")
                    print(f[line_index])
                    line_index = (line_index + 1) % len(f)
                    time.sleep(0.05)
        except (BrokenPipeError, ConnectionResetError):
            print(f"Client disconnected at sentence {line_index}. Waiting for reconnection...")
except KeyboardInterrupt:
    pass
finally:
    s.close()
