# GWeatherRouting

![CI Status](https://github.com/dakk/gweatherrouting/actions/workflows/ci.yaml/badge.svg)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg?logo=gnu&logoColor=white)](https://www.gnu.org/licenses/gpl-3.0)
[![GitHub Release](https://img.shields.io/github/v/release/dakk/gweatherrouting?logo=github&color=orange)](https://github.com/dakk/gweatherrouting/releases/latest)
[![Flathub](https://img.shields.io/flathub/v/org.gweatherrouting.gweatherrouting?logo=flathub&logoColor=white&color=royalblue)](https://flathub.org/apps/org.gweatherrouting.gweatherrouting)

GWeatherRouting is an open-source sailing routing and navigation software written using Python and Gtk4.

![Routing in progress](https://github.com/dakk/gweatherrouting/raw/master/docs/source/_static/images/quickstart/10.gif)

<!-- ![Routing in progress](https://github.com/dakk/gweatherrouting/raw/master/docs/source/_static/images/s3.png) -->
<!-- ![Routing done](https://github.com/dakk/gweatherrouting/raw/master/docs/source/_static/images/s5.png) -->

![Chart detail](https://github.com/dakk/gweatherrouting/raw/master/docs/source/_static/images/s6.png)

![Log analysis](https://github.com/dakk/gweatherrouting/raw/master/docs/source/_static/images/loganalysis.png)

## Features

- Multi-point sailing weather routing
- Boat / polar integrated database
- Grib1 and Grib2 support, with downloader for OpenSkiron and NOAA
- GPX support for importing and exporting POIs and tracks
- Session manager for storing POIs, tracks and routings
- Chart rendering: 
    - GeoJSON (coastlines included)
    - GSHHS basemap (download helper included)
    - KAP, GeoTiff charts and other raster formats supported by GDAL
    - OpenSeaMap seamarks rendering
- Gtk4 interface
- NMEA instruments support
- NMEA / GPX log analysys
- AIS rendering
- Boat dashboard and other realtime navigation support
- Customizable routing calculator



## Installation

You can install gweatherrouting via flatpak, appimage, windows portable zip, or from source.

### Download

[![Flathub](https://img.shields.io/badge/Flathub-blue?logo=flathub&logoColor=white)](https://flathub.org/apps/org.gweatherrouting.gweatherrouting)
[![AppImage](https://img.shields.io/badge/AppImage-blue?logo=linux&logoColor=white)](https://github.com/dakk/gweatherrouting/releases/latest)
[![Windows](https://img.shields.io/badge/Windows-blue?logo=windows&logoColor=white)](https://github.com/dakk/gweatherrouting/releases/download/v0.2.7/GWeatherRouting-win64.zip)

### From source

1. Make sure to have Python >= 3.9 installed and the `pip` package manager.
2. Install the following dependencies using your OS package manager (e.g: archlinux=pacman, debian=apt, macos=homebrew). Be aware that some packages have different names with different package managers.
   - gobject-introspection
   - gdal
   - gtk+3
   - libffi
   - librsvg
   - py3cairo
   - pygobject3
   - pkg-config
   - libgirepository1.0-dev

> [!NOTE]  
> If you are using a `virtualenv` you may need to make symbolic links from the UI libraries to your `venv` folder (this is not needed using system interpreter outside venv).

3. Checkout the repository and run: ```pip install .```
4. Start the software running: ```gweatherrouting```

## License

Read the LICENSE file.
