install:
	pip install .

run:
	gweatherrouting

build-standalone:
	nuitka3 gweatherrouting/main.py --follow-imports --follow-stdlib 

test:
	tox

lint:
	tox -e linters

typecheck:
	tox -e typecheck
