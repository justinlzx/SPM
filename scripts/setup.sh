#!/bin/bash

# Create and activate virtual environment
echo -e "\nCreating and activating virtual environment\n"
python3 -m venv project_venv
source project_venv/bin/activate

# Install pip dependencies
echo -e "\nInstalling pip dependencies\n"
pip install pre-commit black flake8

# Install frontend dependencies
echo -e "\nInstalling frontend dependencies\n"
cd frontend
npm install

echo -e "\nSetup complete. Run 'source project_venv/bin/activate' to activate the virtual environment\n"