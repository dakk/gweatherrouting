# gWeatherRouting - AppImage Generation Guide

This document provides a step-by-step guide to generating an AppImage from the `gWeatherRouting` repository.
`AppImageGen.sh` automatically executes a procedure similar to the one outlined below.
## Prerequisites

- Python and `pip`
- `appimagetool` (for AppImage creation)

## 1. Clone the Repository

```bash
git clone https://github.com/scyrock/gweatherrouting.git
cd gweatherrouting/gweatherrouting/
```

## 2. Generate Binary from Python File

Install `pyinstaller`:

```bash
pip install pyinstaller
```

Run `pyinstaller` with necessary options:

```bash
pyinstaller --onefile --hidden-import=gi --collect-submodules=gi \
--add-data "data/:gweatherrouting/data" --add-data "gtk/:gweatherrouting/gtk" \
--name gWeatherRouting --additional-hooks-dir=. __main__.py
cd ../..
```

### Notes:
- Ensure `hook-gi.repository.Gtk.py` references the correct library paths on your system, as incorrect paths may cause issues.
- The `--add-data "gtk/:gweatherrouting/gtk"` option is not optimal. Ideally, only `.glade` files should be copied instead of the entire directory.

## 3. Create AppImage Directory Structure

```bash
mkdir -p AppDir/usr/{bin,share/applications,share/icons/hicolor/256x256/apps}
cp gweatherrouting/gweatherrouting/dist/gWeatherRouting AppDir/usr/bin/
cp gweatherrouting/icon.png AppDir/usr/share/icons/hicolor/256x256/apps/
cp gweatherrouting/gWeatherRouting.desktop AppDir/usr/share/applications/
```

## 4. Install `linuxdeploy` and GTK Plugin

```bash
wget -c "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage"
wget -c "https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-gtk/master/linuxdeploy-plugin-gtk.sh"
chmod +x linuxdeploy-x86_64.AppImage linuxdeploy-plugin-gtk.sh
```

## 5. Add Required Libraries to AppImage Directory

```bash
NO_STRIP=true DEPLOY_GTK_VERSION=3 ./linuxdeploy-x86_64.AppImage --appdir AppDir --plugin gtk
```

## 6. Generate the AppImage

```bash
cp gweatherrouting/gWeatherRouting.desktop AppDir/
appimagetool AppDir/
```
