# GWeatherRouting

![CI Status](https://github.com/dakk/gweatherrouting/actions/workflows/ci.yaml/badge.svg)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
<!-- [![PyPI version](https://badge.fury.io/py/gweatherrouting.svg)](https://badge.fury.io/py/gweatherrouting) -->

GWeatherRouting is an open-source sailing routing and navigation software written using Python and Gtk4.

![Routing in progress](https://github.com/dakk/gweatherrouting/raw/master/docs/source/_static/images/quckstart/10.gif)

<!-- ![Routing in progress](https://github.com/dakk/gweatherrouting/raw/master/docs/source/_static/images/s3.png) -->
<!-- ![Routing done](https://github.com/dakk/gweatherrouting/raw/master/docs/source/_static/images/s5.png) -->

![Chart detail](https://github.com/dakk/gweatherrouting/raw/master/docs/source/_static/images/s6.png)

![Log analysis](https://github.com/dakk/gweatherrouting/raw/master/docs/source/_static/images/loganalysis.png)

## Features

- Multi-point sailing weather routing
- Boat / polar integrated database
- Grib1 and Grib2 support, with downloader for openskiron
- GPX support for importing and exporting POIs and tracks
- Session manager for storing POIs, tracks and routings
- Chart rendering: 
    - GeoJSON (coastlines included)
    - GSHHS basemap (download helper included)
    - KAP, GeoTiff charts and other raster formats supported by GDAL
    - OpenStreetMap seamark rendering
- Gtk4 interface
- NMEA instruments interface
- Raster Nautical charts (KAP)
- NMEA / GPX log analysys


## Planned features

- Customizable routing calculator
- Ortodromic track render
- AIS rendering
- Boat realtime dashboard


## Installation

1. Make sure to have Python >= 3.9 installed and the `pip` package manager.
2. Install the following dependencies using your OS package manager (e.g: archlinux=pacman, debian=apt, macos=homebrew). Be aware that some packages have different names with different package managers.
   - gobject-introspection
   - gdal
   - gtk+3
   - libffi
   - librsvg
   - osm-gps-map
   - py3cairo
   - pygobject3
   - pkg-config
   - eccodes
   - libgirepository1.0-dev

> [!NOTE]  
> If you are using a `virtualenv` you may need to make symbolic links from the UI libraries to your `venv` folder (this is not needed using system interpreter outside venv).

3. Checkout the repository and run: ```pip install .```
4. Start the software running: ```gweatherrouting```

## License

Read the LICENSE file.
