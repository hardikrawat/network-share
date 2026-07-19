#!/bin/bash
# Linux Build Script for PrintShop

# 1. Install dependencies
pip3 install pyinstaller pyngrok flask flask-cors

echo "2. Building the Linux executable..."
pyinstaller --name "PrintShop" --add-data "../templates:templates" --add-data "../static:static" --noconsole ../app.py

echo "3. Creating Desktop Shortcut..."
cat << EOF > dist/PrintShop.desktop
[Desktop Entry]
Name=PrintShop
Exec=$(pwd)/dist/PrintShop/PrintShop
Icon=$(pwd)/../static/res/favicon.jpg
Terminal=false
Type=Application
Categories=Utility;
EOF
chmod +x dist/PrintShop.desktop

echo "Build complete! You can find the PrintShop executable and PrintShop.desktop shortcut in the 'dist' folder."
