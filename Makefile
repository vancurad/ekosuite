# Use bash shell
SHELL := /bin/bash

# Define variables
VENV_DIR = .venv
PYTHON = $(VENV_DIR)/bin/python3
PIP = $(VENV_DIR)/bin/pip3

# Targets
.PHONY: help install clean run

help: ## Show available commands
	@echo "Available commands:"
	@echo "  make install  - Create virtual environment and install dependencies"
	@echo "  make run      - Run the Python application"
	@echo "  make clean    - Remove virtual environment and temporary files"
	@echo "  make test     - Run tests using pytest"

install:
	@echo "Installing dependencies..."
	python3 -m venv .venv
	source "$(VENV_DIR)/bin/activate"

	export QT_QPA_PLATFORM=offscreen
	$(PIP) install -r requirements.txt

test:
	pytest tests/

run:
	$(PYTHON) ekosuite.py

clean:
	rm -r $(VENV_DIR)