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

# 0. Detect libraries to manually inject
LIBOSM_PATHS=$(ldconfig -p | grep "libosmgpsmap-1.0" | awk '{print $NF}' | tr '\n' ' ')
echo "Using osmmap libraries at: $LIBOSM_PATHS"


echo -e "\nStarting AppImage creation process..."

# 1. Generate Binary from Python File
cd ../gweatherrouting
echo "Generating binary with PyInstaller..."
pyinstaller --onefile --hidden-import=gi --collect-submodules=gi --add-data "data/:gweatherrouting/data" --add-data "gtk/:gweatherrouting/gtk" --name "$APP_NAME" __main__.py
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

for LIBOSM_PATH in $LIBOSM_PATHS; do
    #NO_STRIP=true DEPLOY_GTK_VERSION=3 ./linuxdeploy-x86_64.AppImage --appdir $APP_DIR --plugin gtk --library "$LIBOSM_PATH" 
    NO_STRIP=true DEPLOY_GTK_VERSION=3 ./squashfs-root/AppRun --appdir $APP_DIR --plugin gtk --library "$LIBOSM_PATH"
done
rm -rf squashfs-root

# 5. Modify the AppRun file to add LD_LIBRARY_PATH after the gtk plugin line
echo "Configuring AppRun file..."
rm "$APP_DIR/AppRun"
cp "appimage/AppRun" "$APP_DIR/AppRun"
chmod +x "$APP_DIR/AppRun"

# 6. Create the AppImage
echo "Creating the final AppImage..."
wget https://github.com/AppImage/AppImageKit/releases/latest/download/appimagetool-x86_64.AppImage
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