#!/bin/bash
# Mac Build Script for PrintShop

# 1. Install dependencies
pip3 install pyinstaller pyngrok flask flask-cors

# 2. Build the Mac App bundle
pyinstaller --name "PrintShop" --add-data "templates:templates" --add-data "static:static" --noconsole app.py

echo "Build complete! You can find PrintShop.app in the 'dist' folder."
