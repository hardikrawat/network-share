@echo off
echo Windows Build Script for PrintShop
echo -----------------------------------

echo 1. Installing dependencies...
pip install pyinstaller pyngrok flask flask-cors

echo 2. Building the Windows executable...
pyinstaller --name "PrintShop" --icon="../static/res/favicon.ico" --add-data "../templates;templates" --add-data "../static;static" --noconsole ../app.py

echo Build complete! You can find PrintShop.exe in the 'dist' folder.
pause
