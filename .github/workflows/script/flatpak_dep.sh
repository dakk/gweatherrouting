#!/bin/bash

set -e

VERSION=$1

mkdir -p /tmp/flatpak/wheels
cp flatpak/requirements.txt /tmp/flatpak/
ls /tmp/flatpak

flatpak run \
    --command=sh --devel \
    --filesystem=/tmp/flatpak:rw \
    --share=network \
    org.gnome.Sdk//"$VERSION" \
	-c 'pip3 download -r requirements.txt -d wheels'

cp -r /tmp/flatpak/wheels/* flatpak/wheels