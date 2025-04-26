sudo apt-get install -y libaec-dev
wget -O eccodes-2.41.0-Source.tar.gz "https://confluence.ecmwf.int/download/attachments/45757960/eccodes-2.41.0-Source.tar.gz?api=v2"
tar -xzf eccodes-2.41.0-Source.tar.gz
cd eccodes-2.41.0-Source
mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=/usr/local -DENABLE_EXAMPLES=OFF -DENABLE_TESTS=OFF ..
make
ctest
sudo make install

sudo add-apt-repository ppa:ubuntugis/ubuntugis-unstable
sudo add-apt-repository ppa:ubuntugis/ubuntugis-unstable
sudo apt-get update
sudo apt-get install libosmgpsmap-1.0-1
sudo apt-get install gdal-bin libgdal-dev
sudo apt-get install libgtk-4-dev libgtk-4-1 libgirepository1.0-dev
# sudo apt-get install libeccodes-dev

