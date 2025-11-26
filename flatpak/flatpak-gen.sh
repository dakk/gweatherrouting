#!/bin/bash

set -e

# Check for the presence of flatpak and flatpak-builder
shopt -s nocasematch

DIR="${PWD}"
os=$(awk -F= '/^ID=/ { gsub(/"/, "", $2); print $2 }' /etc/os-release)

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

if command_exists flatpak && command_exists flatpak-builder; then
    echo "flatpak and flatpak-builder already installed, skipping installation."
    install_needed=false
else
    install_needed=true
fi


# If not present, install it
if [ "$install_needed" = true ]; then
    case "$os" in
        arch*|manjaro*)
            sudo pacman -Syu --noconfirm --needed flatpak flatpak-builder
            ;;
        debian*|mint*|ubuntu*)
            sudo apt update
            sudo apt install -y flatpak flatpak-builder
            ;;
        fedora*|redhat*|centos*|alma*|rocky*)
            sudo dnf check-update
            sudo dnf install -y flatpak flatpak-builder
            ;;
        gentoo*)
            sudo emerge --sync
            sudo emerge --ask --noreplace flatpak flatpak-builder
            ;;
        *)
            echo "Unsupported OS: $os; please install flatpak flatpak-builder and start the script again"
            exit 1
            ;;
    esac
fi

shopt -u nocasematch

# Createh the build
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --user -y flathub org.gnome.Platform//46 flathub org.gnome.Sdk//46

if [ ! -d "wheels" ]; then
    mkdir wheels
fi

flatpak run \
    --user \
    --command=sh --devel \
    --filesystem="$DIR":rw \
    --share=network \
    org.gnome.Sdk//46 \
    -c 'pip3 download -r requirements.txt -d wheels'

flatpak-builder --user --install --force-clean build-dir org.gweatherrouting.app.yml
