#!/bin/bash

set -e

sudo apt install -y flatpak flatpak-builder
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install -y flathub org.gnome.Platform//48 flathub org.gnome.Sdk//48

mkdir -p wheels
rm wheels/*

flatpak run \
	--command=sh --devel \
	--filesystem=flatpak:rw \
	--share=network \
	org.gnome.Sdk//48 \
	-c 'pip3 download -r requirements.txt -d wheels'

flatpak-builder --user --install --force-clean build-dir manifest.yaml
