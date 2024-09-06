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
