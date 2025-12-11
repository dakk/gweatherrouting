#!/bin/bash

set -e

# Check for the presence of flatpak and flatpak-builder
shopt -s nocasematch

DIR="${PWD}"
os=$(awk -F= '/^ID=/ { gsub(/"/, "", $2); print $2 }' /etc/os-release)

case "$os" in
    arch*|manjaro*)
        sudo pacman -Syu --noconfirm --needed flatpak flatpak-builder
        ;;
    debian*|mint*|ubuntu*)
        sudo apt update
        sudo apt install -y flatpak flatpak-builder
        ;;
    fedora*|redhat*|centos*|alma*|rocky*)
        sudo dnf install -y flatpak flatpak-builder
        ;;
    gentoo*)
        sudo emerge --ask --noreplace flatpak flatpak-builder
        ;;
    *)
        echo "Unsupported OS: $os"
        exit 1
        ;;
esac

shopt -u nocasematch

flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo

flatpak-builder --install-deps-from=flathub --force-clean org.gweatherrouting.gweatherrouting.yml

flatpak-builder --user --install --force-clean org.gweatherrouting.gweatherrouting.yml

