VENV ?= makevenv
PYTHON ?= python3
VPYTHON = $(VENV)/bin/python3

.PHONY: clean pytest mypy test

$(VENV):
	$(PYTHON) -m venv $@
	$(VPYTHON) -m pip install --upgrade pip
	$(VPYTHON) -m pip install -e ".[dev]"

$(VPYTHON): $(VENV)

pytest: $(VPYTHON)
	$(VPYTHON) -m pytest

mypy: $(VPYTHON)
	$(VPYTHON) -m mypy tuindow
	$(VPYTHON) -m mypy test

test: mypy pytest

clean:
	-rm -rf $(VENV)
