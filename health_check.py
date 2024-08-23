import os
import sys
import json
import pathlib


class Playlist:
    def __init__(self, name, filepaths):
        self.name = name
        self.filepaths = [pathlib.Path(p) for p in filepaths]
        self.mp3_paths = []
        self.cover_path = f"{self.name}.png"
        self.cover_paths = []

        for path in self.filepaths:
            if path.suffix == ".mp4":
                mp3_path = f"{self.name}_{path.stem}.mp3"
                self.mp3_paths.append(mp3_path)
            cover_path = f"{self.name}_{path.stem}.png"
            self.cover_paths.append(cover_path)


def check_iterate(playlists: list[Playlist], path, mode):
    for playlist in playlists:
        if mode == "cover":
            if playlist.cover_path == path:
                return True
        elif mode == "mp3":
            if path in playlist.mp3_paths:
                return True
        elif mode == "covers":
            if path in playlist.cover_paths:
                return True
    return False


def main():
    do_remove = len(sys.argv) > 1 and sys.argv[1] == "--remove"

    data = []
    if os.path.exists("data/playlists.json"):
        with open("data/playlists.json", "r") as file:
            data = json.load(file)

    playlists = [Playlist(pdata["name"], pdata["paths"]) for pdata in data]

    anyf1 = False
    if os.path.exists("data/covers"):
        for file in os.listdir("data/covers"):
            if not check_iterate(playlists, file, "cover"):
                path = f"data/covers/{file}"
                if do_remove:
                    print(f"Removing unused playlist cover: '{path}'")
                    os.remove(path)
                else:
                    print(f"Found unused playlist cover: '{path}'")
                anyf1 = True

    anyf2 = False
    if os.path.exists("data/music_covers"):
        for file in os.listdir("data/music_covers"):
            if not check_iterate(playlists, file, "covers"):
                path = f"data/music_covers/{file}"
                if do_remove:
                    print(f"Removing unused music cover: '{path}'")
                    os.remove(path)
                else:
                    print(f"Found unused music cover: '{path}'")
                anyf2 = True

    anyf3 = False
    if os.path.exists("data/mp3_from_mp4"):
        for file in os.listdir("data/mp3_from_mp4"):
            if not check_iterate(playlists, file, "mp3"):
                path = f"data/mp3_from_mp4/{file}"
                if do_remove:
                    print(f"Removing unused MP3 file: '{path}'")
                    os.remove(path)
                else:
                    print(f"Found unused MP3 file: '{path}'")
                anyf3 = True

    if not anyf1 and not anyf2 and not anyf3:
        print("Health Check: 100%")
    else:
        if not anyf1:
            print("No unused playlist covers found")
        if not anyf2:
            print("No unused music covers found")
        if not anyf3:
            print("No unused MP3 files found")

    if anyf1 or anyf2 or anyf3:
        if do_remove:
            return
        print()
        print(
            "Run health_check.py with the --remove cli argument to automatically delete the unused files"
        )


if __name__ == "__main__":
    main()
