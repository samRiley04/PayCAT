cd ../
pyinstaller --onefile --windowed --add-data="./templates":"templates" --add-data="./static":"static" --hidden-import holidays.countries --clean --name="PayCAT" --icon PayCAT.icns ./app.py