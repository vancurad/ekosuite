# Use bash shell
SHELL := /bin/bash

# Define variables
VENV_DIR = .venv
PYTHON = $(VENV_DIR)/bin/python3
PYTEST = $(VENV_DIR)/bin/pytest
PIP = $(VENV_DIR)/bin/pip3

# Targets
.PHONY: help install clean run

help: ## Show available commands
	@echo "Available commands:"
	@echo "  make build  - Create virtual environment and install dependencies"
	@echo "  make run      - Run the Python application"
	@echo "  make macapp   - Build the macOS application using PyInstaller"
	@echo "  make clean    - Remove virtual environment and temporary files"
	@echo "  make test     - Run tests using pytest"

build:
	@echo "Installing dependencies..."
	python3 -m venv .venv
	source "$(VENV_DIR)/bin/activate"

	export QT_QPA_PLATFORM=offscreen
	$(PIP) install -r requirements.txt

macapp:
	@echo "Building macOS application..."
	$(PYTHON) "$(VENV_DIR)/bin/PyInstaller" ekosuite.spec

test:
	$(PYTEST) tests/

run:
	$(PYTHON) ekosuite.py

clean:
	rm -rf $(VENV_DIR)
	rm -rf build
	rm -rf dist
	find . -type d -name '__pycache__' -exec rm -rf {} +
	rm -rf **/*.pyc