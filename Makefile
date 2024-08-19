install:
	pip install .

run:
	gweatherrouting

build-standalone:
	nuitka3 gweatherrouting/main.py --follow-imports --follow-stdlib 
