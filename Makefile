VENV_DIR := .venv
PYTHON := ${VENV_DIR}/bin/python

venv: $(VENV_DIR)/bin/activate
$(VENV_DIR)/bin/activate: setup.py
	test -d $(VENV_DIR) || virtualenv --python=python3.8 $(VENV_DIR)
	$(PYTHON) -m pip install -e .[dev]

lint: venv
	$(PYTHON) -m black *.py tests_selector --exclude helper_project

install: venv
	$(PYTHON) setup.py develop

clean:
	rm -rf $(VENV_DIR)
	rm -rf tests_selector.egg-info

test: install
	$(PYTHON) -m pytest --cov=tests_selector \
                            --cov-report=html \
                            --cov-report=term
