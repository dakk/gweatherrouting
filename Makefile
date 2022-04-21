install:
	pip install .

run:
	gweatherrouting

run-kivy:
	python3 setup.kivy.py install
	gweatherrouting-kivy

build-standalone:
	nuitka3 gweatherrouting/main.py --follow-imports --follow-stdlib 
