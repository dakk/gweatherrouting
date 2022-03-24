# GWeatherRouting

[![Build Status](https://travis-ci.com/dakk/gweatherrouting.svg?branch=master)](https://travis-ci.com/dakk/gweatherrouting.svg?branch=master)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
<!-- [![PyPI version](https://badge.fury.io/py/gweatherrouting.svg)](https://badge.fury.io/py/gweatherrouting) -->


GWeatherRouting is an opensource sailing route calculator written in python and:
- Gtk3 for the desktop version (Linux/Mac/Windows)
- Kivy for the mobile version (iOS/Android)

![Routing in progress](https://github.com/dakk/gweatherrouting/raw/master/media/routing_process.gif)

![Routing in progress](https://github.com/dakk/gweatherrouting/raw/master/media/routing_process2.png)

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
- Gtk3 interface
- NMEA interface
- Raster Nautical charts (KAP)
- NMEA / GPX log analysys


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


## Building for android

Install buildozer:

```
git clone https://github.com/kivy/buildozer.git
cd buildozer
sudo python setup.py install
```


Create an apk:

```
rm -rf .buildozer/android/platform/build-armeabi-v7a/build/python-installs/gweatherrouting/gweatherrouting* && buildozer android debug deploy run && buildozer android logcat | grep python
```


## Planned features

- Customizable routing calculator
- Ortodromic track render
- AIS rendering
- Boat realtime dashboard
- Mobile version


## License

Read the LICENSE file.
