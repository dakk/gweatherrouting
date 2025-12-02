#!/bin/bash

set -e

DIR="${PWD}"

os=$(awk -F= '/^ID=/ { gsub(/"/, "", $2); print $2 }' /etc/os-release)

case "$os" in
    [Aa][Rr][Cc][Hh]*|[Mm][Aa][Nn][Jj][Aa][Rr][Oo]*)
        sudo pacman -Syu --noconfirm --needed flatpak flatpak-builder
        ;;
    [Dd][Ee][Bb][Ii][Aa][Nn]*|[Mm][Ii][Nn][Tt]*|[Uu][Bb][Uu][Nn][Tt][Uu]*)
        sudo apt update
        sudo apt install -y flatpak flatpak-builder
        ;;
    [Ff][Ee][Dd][Oo][Rr][Aa]*|[Rr][Hh][Ee][Dd][Hh][Aa][Tt]*|[Cc][Ee][Nn][Tt][Oo][Ss]*|[Aa][Ll][Mm][Aa]*|[Rr][Oo][Cc][Kk][Yy]*)
        sudo dnf check-update
        sudo dnf install -y flatpak flatpak-builder
        ;;
    *)
        echo "Unsupported OS: $os"
        exit 1
        ;;
esac

export XDG_DATA_DIRS="$XDG_DATA_DIRS:/var/lib/flatpak/exports/share:$HOME/.local/share/flatpak/exports/share"

flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo

flatpak-builder --install-deps-from=flathub --force-clean build-dir io.github.dakk.gweatherrouting.yml

flatpak-builder --user --install --force-clean build-dir io.github.dakk.gweatherrouting.yml
