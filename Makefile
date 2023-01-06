VENV ?= makevenv
RAWVENV = rawvenv
PYTHON ?= python3
VPYTHON = $(VENV)/bin/python3

.PHONY: clean pytest mypy test sdist wheel

$(VENV):
	$(PYTHON) -m venv $@
	$(VPYTHON) -m pip install --upgrade pip
	$(VPYTHON) -m pip install -e ".[dev]"

$(RAWVENV): clean
	$(PYTHON) -m venv $@

$(VPYTHON): $(VENV)

pytest: $(VPYTHON)
	$(VPYTHON) -m pytest

mypy: $(VPYTHON)
	$(VPYTHON) -m mypy tuindow
	$(VPYTHON) -m mypy test

test: mypy pytest

sdist: $(RAWVENV)
	  $(RAWVENV)/bin/python3 setup.py sdist
	  $(RAWVENV)/bin/python3 -m pip install pytest wheel
	  $(RAWVENV)/bin/python3 -m pip install dist/*.tar.gz
	  $(RAWVENV)/bin/python3 -m pytest

wheel: $(RAWVENV)
	  $(RAWVENV)/bin/python3 -m pip install pytest wheel
	  $(RAWVENV)/bin/python3 setup.py bdist_wheel
	  $(RAWVENV)/bin/python3 -m pip install dist/*.whl
	  $(RAWVENV)/bin/python3 -m pytest


clean:
	-rm -rf $(VENV) $(RAWVENV) dist build
