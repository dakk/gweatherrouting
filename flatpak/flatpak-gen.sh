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

flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install -y flathub org.gnome.Platform//48 flathub org.gnome.Sdk//48

if [ ! -d "wheels" ]; then
	mkdir wheels
fi

flatpak run \
	--command=sh --devel \
	--filesystem="$DIR":rw \
	--share=network \
	org.gnome.Sdk//48 \
	-c 'pip3 download -r requirements.txt -d wheels'

flatpak-builder --user --install --force-clean build-dir manifest.yaml
