.PHONY: docs

install:
	pip install .

run:
	gweatherrouting

build-standalone:
	nuitka3 gweatherrouting/__main__.py --follow-imports --follow-stdlib 

build-appimage:
	pip install pyinstaller
	cd appimage && bash appimagegen.sh -y

docs:
	make -C docs html