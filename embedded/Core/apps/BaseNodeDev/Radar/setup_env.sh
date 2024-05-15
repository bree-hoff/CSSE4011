#!/bin/bash

python3 -m venv RADAR-ENV
source RADAR-ENV/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "To activate the virtual environment, run: source RADAR-ENV/bin/activate"
