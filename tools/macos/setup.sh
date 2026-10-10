#!/usr/bin/env bash
set -euo pipefail

if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew is required. Install it from https://brew.sh/ and run this script again." >&2
    exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

brew install gdal gobject-introspection gtk+3 python@3.11

BREW_PREFIX="$(brew --prefix)"
export PATH="$(brew --prefix python@3.11)/bin:$BREW_PREFIX/bin:$PATH"
export PKG_CONFIG_PATH="$BREW_PREFIX/lib/pkgconfig:$BREW_PREFIX/share/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"

if [[ ! -d .venv ]]; then
    python3.11 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip wheel setuptools

# Build Python GDAL against the GDAL library installed by Homebrew.
GDAL_VERSION="$(gdal-config --version)"
python -m pip install numpy
python -m pip install --no-build-isolation "GDAL[numpy]==${GDAL_VERSION}"
# PyGObject uses Meson and needs its isolated build dependencies.
python -m pip install "PyGObject==3.50.0"
python -m pip install --no-build-isolation --editable .

echo "Setup complete. Activate the environment with: source .venv/bin/activate"
echo "Then start the app with: gweatherrouting"
