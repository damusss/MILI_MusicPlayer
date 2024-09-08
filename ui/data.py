import numpy
import pygame
import pathlib
import threading
from ui.common import *
import moviepy.editor as moviepy


def load_cover_async(path, obj):
    obj.cover = pygame.image.load(path).convert()


def get_cover_async(music, videofile, cover_path):
    try:
        frame: numpy.ndarray = videofile.get_frame(videofile.duration / 2)
        surface = pygame.image.frombytes(frame.tobytes(), videofile.size, "RGB")
        pygame.image.save(surface, cover_path)
        music.cover = surface
    except Exception:
        music.cover = None


def convert_music_async(music, audiofile, new_path):
    try:
        audiofile.write_audiofile(str(new_path), verbose=True)
        music.pending = False
    except Exception as e:
        music.load_exc = e


class NotCached: ...


class ResizeHandle:
    def __init__(self, app: "MusicPlayerApp", name, corner, axis, move_window, cursor):
        self.app = app
        self.name = name
        self.corner = corner
        self.axis = axis
        self.axis_lock = "x" if self.axis == "y" else "y" if self.axis == "x" else None
        self.move_window = move_window
        self.cursor = cursor

    def make_rect(self):
        if self.corner:
            rect = pygame.Rect(0, 0, RESIZE_SIZE * 2, RESIZE_SIZE * 2)
        else:
            rect = pygame.Rect(
                0,
                0,
                self.app.window.size[0] if self.axis == "x" else RESIZE_SIZE,
                self.app.window.size[1] if self.axis == "y" else RESIZE_SIZE,
            )
        if self.name == "topright":
            rect = rect.move_to(topright=(self.app.window.size[0], 0))
        elif self.name == "bottomleft" or self.name == "bottom":
            rect = rect.move_to(bottomleft=(0, self.app.window.size[1]))
        elif self.name == "bottomright" or self.name == "right":
            rect = rect.move_to(bottomright=self.app.window.size)
        self.rect = rect

    def update(self, mpos):
        rel = self.app.window.position + mpos - self.app.resize_gmpos
        posrel = pygame.Vector2()
        if self.axis_lock == "y":
            rel.x = 0
        elif self.axis_lock == "x":
            rel.y = 0
        if self.move_window == "x":
            rel.x *= -1
            posrel.x = rel.x
        elif self.move_window == "y":
            rel.y *= -1
            posrel.y = rel.y
        elif self.move_window == "xy":
            rel.x *= -1
            rel.y *= -1
            posrel = rel
        newsize = self.app.resize_winsize + rel
        if any([v <= 0 for v in newsize]):
            return
        ratio = newsize[0] / newsize[1]
        if ratio < 0.45:
            newsize = (newsize[1] * 0.46, newsize[1])
        self.app.window.size = newsize
        if posrel.length() != 0:
            self.app.window.position = self.app.resize_winpos - posrel
        self.app.make_bg_image()


class MusicData:
    audiopath: pathlib.Path
    realpath: pathlib.Path
    cover: pygame.Surface
    duration: int
    playlist: "Playlist"
    pending: bool
    load_exc = None

    @classmethod
    def load(cls, realpath, playlist: "Playlist", loading_image=None):
        self = MusicData()
        self.realpath = realpath
        self.playlist = playlist
        self.cover = None
        self.duration = NotCached
        self.pending = False
        self.load_exc = None

        cover_path = f"data/music_covers/{playlist.name}_{self.realstem}.png"
        if not os.path.exists(realpath):
            pygame.display.message_box(
                "Could not load music",
                f"Could not load music '{realpath}' as the file doesn't exist anymore. Music will be skipped",
                "error",
                None,
                ("Understood",),
            )
            return

        if self.isvideo:
            new_path = pathlib.Path(
                f"data/mp3_from_mp4/{playlist.name}_{self.realstem}.mp3"
            ).resolve()

            if os.path.exists(new_path) and os.path.exists(cover_path):
                self.load_cover_async(cover_path, loading_image)
                self.audiopath = new_path
                return self

            videofile = moviepy.VideoFileClip(str(realpath))
            self.videofile = videofile
            if not os.path.exists(cover_path):
                try:
                    self.pending = True
                    if loading_image is not None:
                        self.cover = loading_image
                    thread = threading.Thread(
                        target=get_cover_async, args=(self, videofile, cover_path)
                    )
                    thread.start()
                except Exception:
                    self.cover = None
            else:
                self.load_cover_async(cover_path, loading_image)

            if os.path.exists(new_path):
                self.audiopath = new_path
                return self

            audiofile = videofile.audio
            if audiofile is None:
                pygame.display.message_box(
                    "Could not load music",
                    f"Could not convert '{realpath}' to audio format: the video has no associated audio. Music will be skipped",
                    "error",
                    None,
                    ("Understood",),
                )
                return
            self.audiopath = new_path
            self.pending = True
            thread = threading.Thread(
                target=convert_music_async, args=(self, audiofile, new_path)
            )
            thread.start()
            return self

        else:
            if os.path.exists(cover_path):
                self.load_cover_async(cover_path, loading_image)
            self.audiopath = realpath
            return self

    def check(self):
        if not self.pending:
            if hasattr(self, "videofile"):
                self.videofile.close()
                del self.videofile
        if self.load_exc is None:
            return False
        pygame.display.message_box(
            "Could not load music",
            f"Could not convert '{self.realpath}' to audio format due to external exception: '{self.load_exc}'. Music will be removed",
            "error",
            None,
            ("Understood",),
        )
        self.playlist.remove(self.audiopath)
        return True

    def load_cover_async(self, path, loading_image=None):
        if loading_image is not None:
            self.cover = loading_image
        thread = threading.Thread(target=load_cover_async, args=(path, self))
        thread.start()

    def cache_duration(self):
        try:
            soundfile = moviepy.AudioFileClip(str(self.audiopath))
            self.duration = soundfile.duration
            soundfile.close()
        except Exception:
            self.duration = None

    def cover_or(self, default):
        if self.cover is None:
            return default
        return self.cover

    @property
    def realstem(self):
        return self.realpath.stem

    @property
    def realname(self):
        return self.realpath.name

    @property
    def realextension(self):
        return self.realpath.suffix

    @property
    def isvideo(self):
        return self.realpath.suffix.lower() == ".mp4"

    @property
    def pos_supported(self):
        return self.realpath.suffix.lower()[1:] in POS_SUPPORTED


class HistoryData:
    def __init__(self, music: MusicData, position, duration):
        self.music = music
        self.position = position
        if duration is NotCached:
            duration = "not cached"
        self.duration = duration
        if self.duration not in [None, "not cached"]:
            if int(self.position) >= int(self.duration - 0.01):
                self.position = 0

    def get_save_data(self):
        duration = self.duration
        if duration is NotCached:
            duration = "not cached"
        return {
            "audiopath": str(self.music.audiopath),
            "position": self.position,
            "playlist": self.music.playlist.name,
            "duration": duration,
        }

    @classmethod
    def load_from_data(self, data, app):
        playlist = None
        for pobj in app.playlists:
            if pobj.name == data["playlist"]:
                playlist = pobj
                break
        if playlist is None:
            return
        musicobj = playlist.musictable.get(pathlib.Path(data["audiopath"]), None)
        if musicobj is None:
            return
        if data["duration"] is not None and data["duration"] != "not cached":
            musicobj.duration = data["duration"]
        return HistoryData(musicobj, data["position"], data["duration"])


class Playlist:
    def __init__(self, name, filepaths=None, loading_image=None):
        self.name = name
        self.cover = None

        if os.path.exists(f"data/covers/{self.name}.png"):
            if loading_image is not None:
                self.cover = loading_image
            thread = threading.Thread(
                target=load_cover_async,
                args=(f"data/covers/{self.name}.png", self),
            )
            thread.start()

        self.musiclist: list[MusicData] = []
        self.musictable: dict[pathlib.Path, MusicData] = {}
        for path in filepaths:
            self.load_music(path, loading_image)

    @property
    def realpaths(self):
        return [music.realpath for music in self.musiclist]

    def load_music(self, path, loading_image=None, idx=-1):
        if path in self.musictable or path in self.realpaths:
            return
        music_data = MusicData.load(path, self, loading_image)
        if music_data is None:
            return
        if idx != -1:
            self.musiclist.insert(idx, music_data)
        else:
            self.musiclist.append(music_data)
        self.musictable[music_data.audiopath] = music_data

    def remove(self, path):
        music = self.musictable.pop(path)
        self.musiclist.remove(music)
