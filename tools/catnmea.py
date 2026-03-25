import os
import socket
import sys
import time

nmea_file = "/home/dakk/MEGA/GeoTracks/Boat/2021/MDC2021_2/data_12_12_2021.nmea"
port = 10110

for arg in sys.argv[1:]:
    if arg.isdigit():
        port = int(arg)
    else:
        nmea_file = arg

if not os.path.exists(nmea_file):
    nmea_file = os.path.join(os.path.dirname(__file__), "sample_ais.nmea")
f = open(nmea_file, "r").read().split("\n")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("", port))
s.listen(1)

try:
    conn, addr = s.accept()
    with conn:
        print("Connected by", addr)
        while True:
            for x in f[30000:]:
                conn.send(x.encode("ascii") + b"\n")
                print(x)
                time.sleep(0.05)
except (BrokenPipeError, ConnectionResetError, KeyboardInterrupt):
    pass
finally:
    s.close()
