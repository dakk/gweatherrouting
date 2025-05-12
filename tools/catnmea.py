f = (
    open("/home/dakk/MEGA/GeoTracks/Boat/2021/MDC2021_2/data_12_12_2021.nmea", "r")
    .read()
    .split("\n")
)

# Create a tcp socket receiving connections
import socket
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("", 10110))
s.listen(1)

conn, addr = s.accept()
with conn:
    print("Connected by", addr)
    while True:
        for x in f[30000:]:
            try:
                conn.send(x.encode("ascii") + "\n".encode("ascii"))
                print(x)
                time.sleep(0.1)
            except:
                conn.close()
                s.close()
