VENV_DIR := .venv
PYTHON := ${VENV_DIR}/bin/python

venv: $(VENV_DIR)/bin/activate
$(VENV_DIR)/bin/activate: requirements.txt setup.py
	test -d $(VENV_DIR) || virtualenv --python=python3 $(VENV_DIR)
	$(PYTHON) -m pip install -e .[dev]

lint: venv
	$(PYTHON) -m black *.py tests_selector --exclude helper_project

install: venv
	$(PYTHON) setup.py develop

clean:
	rm -rf $(VENV_DIR)
	rm -rf tests_selector.egg-info
