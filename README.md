# GWeatherRouting

[![Build Status](https://travis-ci.com/dakk/gweatherrouting.svg?branch=master)](https://travis-ci.com/dakk/gweatherrouting.svg?branch=master)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
<!-- [![PyPI version](https://badge.fury.io/py/gweatherrouting.svg)](https://badge.fury.io/py/gweatherrouting) -->

GWeatherRouting is an opensource sailing route calculator written in python and:
- Gtk3 for the desktop version (Linux/Mac/Windows)
- Kivy for the mobile version (iOS/Android) [Read here](README.mobile.md)

![Routing in progress](https://github.com/dakk/gweatherrouting/raw/master/media/s3.png)

![Routing done](https://github.com/dakk/gweatherrouting/raw/master/media/s5.png)

![Chart detail](https://github.com/dakk/gweatherrouting/raw/master/media/s6.png)

![Log analysis](https://github.com/dakk/gweatherrouting/raw/master/media/loganalysis.png)

## Features

- Multi-point sailing weather routing
- Boat / polar integrated database
- Grib1 and Grib2 support, with downloader for openskiron
- GPX support for importing and exporting POIs and tracks
- Session manager for storing POIs, tracks and routings
- Chart rendering: 
    - GeoJSON (coastlines included)
    - GSHHS basemap (download helper included)
    - KAP, GeoTiff charts and other raster formats
    - OpenStreetMap seamark rendering
- Gtk3 interface
- NMEA interface
- Raster Nautical charts (KAP)
- NMEA / GPX log analysys


## Planned features

- Customizable routing calculator
- Ortodromic track render
- AIS rendering
- Boat realtime dashboard
- Mobile version


## Installation

First, install the following dependencies using your OS package manager:
- osm-gps-map (version 1.2.0)
- eccodes
- python3
- python3-pip

Then checkout the repository and run:
```sudo python3 setup.py install```

Start the software running:
```gweatherrouting```


## License

Read the LICENSE file.
