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

try:
    conn, addr = s.accept()
    with conn:
        print("Connected by", addr)
        while True:
            for x in f:
                conn.send(x.encode("ascii") + b"\n")
                print(x)
                time.sleep(0.05)
except (BrokenPipeError, ConnectionResetError, KeyboardInterrupt):
    pass
finally:
    s.close()
