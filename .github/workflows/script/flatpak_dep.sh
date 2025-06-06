#!/bin/bash

set -e

VERSION=$1
DIR="${PWD}"

#mkdir -p flatpak/wheels /tmp/flatpak/wheels
#cp flatpak/requirements.txt /tmp/flatpak/
#ls /tmp/flatpak

mkdir -p flatpak/wheels

flatpak run \
    --command=sh --devel \
    --filesystem="$PWD"/flatpak:rw \
    --share=network \
    org.gnome.Sdk//"$VERSION" \
	-c 'pip3 download -r requirements.txt -d wheels'

cp -r /tmp/flatpak/wheels/* flatpak/wheels