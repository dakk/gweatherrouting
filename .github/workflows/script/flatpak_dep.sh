#!/bin/bash

set -e

VERSION=$1
DIR="${PWD}"

mkdir -p "$DIR"/flatpak/wheels

flatpak run \
    --command=sh --devel \
    --filesystem="$DIR"/flatpak:rw \
    --share=network \
    org.gnome.Sdk//"$VERSION" \
	-c 'pip3 download -r requirements.txt -d wheels'