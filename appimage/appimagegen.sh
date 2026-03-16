#!/bin/bash

set -e  # Exit on error

# Define variables
APP_NAME="GWeatherRouting"
APP_DIR="AppDir"
DEPLOY_GTK_VERSION=3

# Display disclaimers
echo -e "\n========== DISCLAIMER ==========\n"
echo "This script has been tested on Ubuntu. If you are using another Linux distribution,"
echo "you may encounter errors in the generated AppImage due to linuxdeploy-gtk not"
echo "properly tracking all dependencies."
echo -e "\nBefore running this script, ensure you are in a Python environment"
echo "(e.g., virtual environment) where the application works properly and"
echo "pyinstaller is installed (you can install it using 'pip install pyinstaller')."
echo -e "\n===============================\n"

# Ask for confirmation to proceed
if [[ "$1" != "-y" ]]; then
    read -p "Do you want to continue? (y/n): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "Script execution cancelled."
        exit 0
    fi
fi

echo -e "\nStarting AppImage creation process..."

# 1. Find system typelib directory (needed for PyInstaller bundling)
TYPELIB_DIR=""
for dir in /usr/lib/x86_64-linux-gnu/girepository-1.0 /usr/lib64/girepository-1.0 /usr/lib/girepository-1.0; do
    if [[ -d "$dir" ]]; then
        TYPELIB_DIR="$dir"
        break
    fi
done

if [[ -z "$TYPELIB_DIR" ]]; then
    echo "ERROR: Could not find system typelib directory, exiting."
    exit 1
fi

echo "Found typelib directory: $TYPELIB_DIR"

# Collect typelib --add-data flags for PyInstaller
TYPELIB_FLAGS=""
REQUIRED_TYPELIBS="Gtk-3.0 Gdk-3.0 GdkPixbuf-2.0 Pango-1.0 PangoCairo-1.0 GObject-2.0 GLib-2.0 Gio-2.0 cairo-1.0 Atk-1.0 GdkX11-3.0 xlib-2.0 HarfBuzz-0.0 freetype2-2.0 GModule-2.0"
for typelib in $REQUIRED_TYPELIBS; do
    if [[ -f "$TYPELIB_DIR/${typelib}.typelib" ]]; then
        TYPELIB_FLAGS="$TYPELIB_FLAGS --add-data $TYPELIB_DIR/${typelib}.typelib:gi_typelibs"
    else
        echo "WARNING: ${typelib}.typelib not found in $TYPELIB_DIR"
    fi
done

# 2. Generate Binary from Python File
cd ../gweatherrouting
echo "Generating binary with PyInstaller..."
pyinstaller --onefile --hidden-import=gi --collect-submodules=gi \
    --add-data "data/:gweatherrouting/data" --add-data "gtk/:gweatherrouting/gtk" \
    --runtime-hook="../appimage/pyinstaller_gi_hook.py" \
    $TYPELIB_FLAGS \
    --name "$APP_NAME" __main__.py
cd ..

# 2. Create AppImage Directory Structure
echo "Creating AppImage directory structure..."
mkdir -p "$APP_DIR/usr/bin" "$APP_DIR/usr/share/applications" "$APP_DIR/usr/share/icons/hicolor/256x256/apps"

cp -r /usr/share/gdal "$APP_DIR/usr/share/"
cp "gweatherrouting/dist/$APP_NAME" "$APP_DIR/usr/bin/"
cp "appimage/icon.png" "$APP_DIR/usr/share/icons/hicolor/256x256/apps/"
cp "appimage/$APP_NAME.desktop" "$APP_DIR/usr/share/applications/"

# 3. Install linuxdeploy and GTK Plugin
echo "Downloading linuxdeploy tools..."
wget -c "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage"
wget -c "https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-gtk/master/linuxdeploy-plugin-gtk.sh"
chmod +x linuxdeploy-x86_64.AppImage linuxdeploy-plugin-gtk.sh

# 4. Add Required Libraries to AppImage Directory
echo "Adding required libraries to AppImage directory..."
./linuxdeploy-x86_64.AppImage --appimage-extract
NO_STRIP=true DEPLOY_GTK_VERSION=3 ./squashfs-root/AppRun --appdir $APP_DIR --plugin gtk
rm -rf squashfs-root

# Ensure destination exists
mkdir -p "$APP_DIR/usr/lib"

# Find libgirepository libraries and copy them to your AppDir
LIBGIREPO_PATHS=$(ldconfig -p | grep libgirepository | awk '{print $4}' | sort -u)

if [[ -z "$LIBGIREPO_PATHS" ]]; then
    echo "libgirepository libraries not found on the system, exiting."
    exit 1
fi

for libpath in $LIBGIREPO_PATHS; do
    echo "Copying $libpath to $APP_DIR/usr/lib/"
    cp "$libpath" "$APP_DIR/usr/lib/"
done

# Copy GObject Introspection typelib files to AppDir as fallback
echo "Copying typelib files to AppDir..."
mkdir -p "$APP_DIR/usr/lib/girepository-1.0"
for typelib in $REQUIRED_TYPELIBS; do
    if [[ -f "$TYPELIB_DIR/${typelib}.typelib" ]]; then
        echo "Copying ${typelib}.typelib"
        cp "$TYPELIB_DIR/${typelib}.typelib" "$APP_DIR/usr/lib/girepository-1.0/"
    fi
done

# 5. Modify the AppRun file to add LD_LIBRARY_PATH after the gtk plugin line
echo "Configuring AppRun file..."
rm "$APP_DIR/AppRun"
cp "appimage/AppRun" "$APP_DIR/AppRun"
chmod +x "$APP_DIR/AppRun"

# 6. Create the AppImage
echo "Creating the final AppImage..."
wget https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
./appimagetool-x86_64.AppImage --appimage-extract-and-run "$APP_DIR"

echo -e "\nAppImage creation completed successfully!"

# 7. Clean up

echo "Cleaning up..."
rm linuxdeploy-plugin-gtk.sh
rm linuxdeploy-x86_64.AppImage
rm appimagetool-x86_64.AppImage
rm -rf squashfs-root
rm -r gweatherrouting/dist
rm -r gweatherrouting/build
rm -r gweatherrouting/GWeatherRouting.spec
rm -r AppDir
echo "Cleanup completed."