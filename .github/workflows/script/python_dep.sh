pip install git+https://github.com/vext-python/vext@32ad4d1c5f45797e244df1d2816f76b60f28e20e

# NOTE: this is necessary for building gdal using deprecated bdist enforced by pep 517
python -m pip install "pip<25.3"

pip install numpy>1.0.0 wheel setuptools>=67
pip install --no-cache --force-reinstall gdal[numpy]=="$(gdal-config --version).*"

echo "Checking GDAL installation..."
python3 -c 'from osgeo import gdal_array'
