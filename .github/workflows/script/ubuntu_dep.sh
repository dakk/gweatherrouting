sudo add-apt-repository -y ppa:ubuntugis/ubuntugis-unstable
sudo apt update
sudo apt-get install -y libosmgpsmap-1.0-1 libosmgpsmap-1.0-dev
sudo apt-get install -y gdal-bin libgdal-dev
sudo apt-get install -y libgtk-4-dev libgtk-4-1 libgirepository1.0-dev
# sudo apt-get install libeccodes-dev

sudo apt-get install -y libaec-dev cmake
wget -O eccodes-2.41.0-Source.tar.gz "https://confluence.ecmwf.int/download/attachments/45757960/eccodes-2.41.0-Source.tar.gz?api=v2"
tar -xzf eccodes-2.41.0-Source.tar.gz
cd eccodes-2.41.0-Source
mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=/usr/local -DENABLE_EXAMPLES=OFF -DENABLE_TESTS=OFF -DENABLE_FORTRAN=OFF ..
make -j`nproc`
sudo make install


