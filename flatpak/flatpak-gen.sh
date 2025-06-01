#!/bin/bash

set -e

DIR="${PWD}"

sudo apt install -y flatpak flatpak-builder
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install -y flathub org.gnome.Platform//48 flathub org.gnome.Sdk//48

if [ ! -d "wheels" ]; then
	mkdir wheels
fi
if [ ! - "requirements.txt" ]; then
	
fi
rm wheels

flatpak run \
	--command=sh --devel \
	--filesystem="$DIR":rw \
	--share=network \
	org.gnome.Sdk//48 \
	-c 'pip3 download -r requirements.txt -d wheels'

flatpak-builder --user --install --force-clean build-dir manifest.yaml
