VENV_DIR := .venv
PYTHON := ${VENV_DIR}/bin/python

venv: $(VENV_DIR)/bin/activate
$(VENV_DIR)/bin/activate: setup.py
	test -d $(VENV_DIR) || python3 -m venv $(VENV_DIR)

install: venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .[dev]

clean:
	rm -rf $(VENV_DIR)
	rm -rf pytest_rts.egg-info

publish: install
	. $(VENV_DIR)/bin/activate; $(VENV_DIR)/bin/semantic-release publish -D version_variable=pytest_rts/__init__.py:__version__
