#!/bin/bash

python3 -m venv DEV-ENV
source DEV-ENV/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

protoc -I/Users/lewis/csse4011/project/CSSE4011/embedded/mycode/apps/BaseNodeDev/GUI/DEV-ENV/lib/python3.12/site-packages/nanopb/generator/proto --python_out=. --proto_path=. minecraftmessage.proto

echo "To activate the virtual environment, run: source DEV-ENV/bin/activate"
