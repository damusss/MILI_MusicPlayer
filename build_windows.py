"""
Executable creation steps:
1. delete the old executable
2. create the new executable using pyinstaler without a console and with a custom icon
3. copy the executable from the dist folder to the main folder
4. delete the spec file
5. delete the dist folder and its contents
6. delete the build folder and its contents
"""

import os
import shutil

if os.path.exists("MusicPlayer.exe"):
    os.remove("MusicPlayer.exe")

os.system(
    "pyinstaller --onefile --icon=data/icons/playlist.png --windowed MusicPlayer.py"
)

shutil.copyfile("dist/MusicPlayer.exe", "MusicPlayer.exe")
os.remove("MusicPlayer.spec")
shutil.rmtree("dist")
shutil.rmtree("build")
