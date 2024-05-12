#!/bin/bash

python3 -m venv DEV-ENV

source DEV-ENV/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

#Path to the python environment
protoc --python_out=. --plugin=protoc-gen-nanopb=/Users/lewis/csse4011/project/CSSE4011/embedded/mycode/apps/BaseNodeDev/GUI/DEV-ENV/lib/python3.12/site-packages/nanopb/generator/protoc-gen-nanopb message.proto

echo "To activate the virtual environment, run: source DEV-ENV/bin/activate"

