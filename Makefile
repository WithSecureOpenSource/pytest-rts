VENV_DIR := .venv
PYTHON := ${VENV_DIR}/bin/python

venv: $(VENV_DIR)/bin/activate
$(VENV_DIR)/bin/activate: setup.py
	test -d $(VENV_DIR) || python3 -m venv $(VENV_DIR)

install: venv
	$(PYTHON) setup.py develop

clean:
	rm -rf $(VENV_DIR)
	rm -rf pytest_rts.egg-info
