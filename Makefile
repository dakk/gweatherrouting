install:
	pip install .

run:
	gweatherrouting

build-standalone:
	nuitka3 gweatherrouting/main.py --follow-imports --follow-stdlib 


build-appimage:
	pip install pyinstaller
	cd appimage && bash appimagegen.sh -y
