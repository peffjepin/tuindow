VENV ?= makevenv
PYTHON = $(VENV)/bin/python3

.PHONY: clean test type_check test_all

$(VENV):
	python3 -m venv $@
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

$(PYTHON): $(VENV)

test: $(PYTHON)
	$(PYTHON) -m pytest

type_check: $(PYTHON)
	$(PYTHON) -m mypy tuindow

test_all: type_check test

clean:
	-rm -rf $(VENV)
