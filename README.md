# GWeatherRouting

GWeatherRouting is an opensource sailing route calculator written in python/gtk3.

![Routing in progress](https://github.com/dakk/gweatherrouting/raw/master/media/routing_process.gif)

## Features

- Multi-point sailing weather routing
- Boat / polar integrated database
- Grib1 and Grib2 support, with downloader for openskiron
- GPX support for importing and exporting POIs and tracks
- Session manager for storing POIs, tracks and routings
- Chart rendering: GeoJSON (coastlines included)
- Gtk3 interface


## Installation

First, install the following dependencies using your OS package manager:
- osm-gps-map
- eccodes

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


## License

Read the LICENSE file.
