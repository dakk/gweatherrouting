#!/bin/bash

set -e

VERSION=$1
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WHEELS_DIR="$REPO_DIR/flatpak/wheels"

mkdir -p "$WHEELS_DIR"

flatpak run \
  --command=sh --devel \
  --filesystem="$REPO_DIR/flatpak":rw \
  --share=network \
  org.gnome.Sdk//"$VERSION" \
  -c 'pip3 download -r flatpak/requirements.txt -d flatpak/wheels'