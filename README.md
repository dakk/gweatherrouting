# GWeatherRouting

GWeatherRouting is an opensource sailing route calculator written in python and:
- Gtk3 for the desktop version (Linux/Mac/Windows)
- Kivy for the mobile version (iOS/Android)

![Routing in progress](https://github.com/dakk/gweatherrouting/raw/master/media/routing_process.gif)

![Routing in progress](https://github.com/dakk/gweatherrouting/raw/master/media/routing_process2.png)

## Features

- Multi-point sailing weather routing
- Boat / polar integrated database
- Grib1 and Grib2 support, with downloader for openskiron
- GPX support for importing and exporting POIs and tracks
- Session manager for storing POIs, tracks and routings
- Chart rendering: 
    - GeoJSON (coastlines included)
    - KAP, GeoTiff charts and other raster formats
- Gtk3 interface
- Mobile version



## Installation

First, install the following dependencies using your OS package manager:
- osm-gps-map (version 1.2.0)
- eccodes

Install libweatherrouting:

```bash
git clone https://github.com/dakk/libweatherrouting
cd libweatherrouting
sudo python3 setup.py install
```

Then checkout the repository and run:
```sudo python3 setup.py install```

Start the software running:
```gweatherrouting```


## Planned features

- Customizable routing calculator
- Vector Nautical charts CM73
- Raster Nautical charts (KAP)
- Ortodromic track render
- Sailchart rendering
- NMEA interface
- AIS rendering
- Boat realtime dashboard
- Mobile version


## License

Read the LICENSE file.
