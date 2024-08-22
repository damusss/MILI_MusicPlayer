import pygame
import mili
import os
import pathlib
import json
import numpy
import moviepy.editor as moviepy
import typing
import functools
import threading

if typing.TYPE_CHECKING:
    from MusicPlayer import MusicPlayerApp

PREFERRED_SIZES = (415, 700)
UI_SIZES = (450, 700)
SURF = pygame.Surface((10, 10), pygame.SRCALPHA)
FORMATS = ["mp4", "wav", "mp3", "ogg", "flac", "opus", "wv", "mod", "aiff"]
POS_SUPPORTED = ["mp4", "mp3", "ogg", "flac", "mod"]
ANIMSPEED = 50
ANIMEASE = mili.animation.EaseIn()
MUSIC_ENDEVENT = pygame.event.custom_type()

BG_CV = 3
MUSIC_CV = 3, 10, 5
LIST_CV = MUSIC_CV  # 10, 20, 5
OVERLAY_CV = 30, 50, 20
SBAR_CV = 7
SHANDLE_CV = 15, 20, 10
MODAL_CV = 15
MODALB_CV = 25, 45, 20
MUSICC_CV = 10
CONTROLS_CV = 10, 30, 18
MENU_CV = 6, 20
LISTM_CV = 20, 25, 18
MP_OVERLAY_CV = (50, 50, 50, 150), (80, 80, 80, 150), (30, 30, 30, 150)
MP_BG_FILL = (50, 50, 50, 120)
ALPHA = 120


def cond(app, it, normal, hover, press):
    if not app.can_interact():
        return normal
    if it.left_pressed:
        return press
    elif it.hovered:
        return hover
    return normal


def load_json(path, content_if_not_exist):
    if os.path.exists(path):
        with open(path, "r") as file:
            return json.load(file)
    else:
        with open(path, "w") as file:
            json.dump(content_if_not_exist, file)
            return content_if_not_exist


def write_json(path, content):
    with open(path, "w") as file:
        json.dump(content, file)


def make_data_folders(*names):
    for name in names:
        if not os.path.exists(f"data/{name}"):
            os.mkdir(f"data/{name}")


def load_icon(name):
    return pygame.image.load(f"data/icons/{name}.png").convert_alpha()


def animation(value):
    return mili.animation.ABAnimation(
        0, value, "number", ANIMSPEED, ANIMSPEED, ANIMEASE
    )


def load_cover_async(path, key, storage):
    storage[key] = pygame.image.load(path).convert()


def load_main_cover_async(path, playlist):
    playlist.cover = pygame.image.load(path).convert()


class Playlist:
    def __init__(self, name, filepaths: list[pathlib.Path] = None, loading=None):
        self.name = name
        self.filepaths = filepaths if filepaths else []
        self.music_covers = {}
        self.filepaths_table = {}
        self.cover = None
        self.musics_durations = {}

        if os.path.exists(f"data/covers/{self.name}.png"):
            if loading is not None:
                self.cover = loading
            thread = threading.Thread(
                target=load_main_cover_async,
                args=(f"data/covers/{self.name}.png", self),
            )
            thread.start()

        new_paths: list[pathlib.Path] = []
        for path in self.filepaths:
            self.load_music(path, new_paths, loading)
        self.filepaths = new_paths

    def load_music(self, path, new_paths, loading=None):
        if path in new_paths or path in self.filepaths_table.values():
            return
        cover_path = f"data/music_covers/{self.name}_{path.stem}.png"
        if not os.path.exists(path):
            pygame.display.message_box(
                "Could not load music",
                f"Could not load music '{path}' as the file doesn't exist anymore. Music will be skipped",
                "error",
                None,
                ("Understood",),
            )
            return

        if path.suffix == ".mp4":
            new_path = pathlib.Path(
                f"data/mp3_from_mp4/{self.name}_{path.stem}.mp3"
            ).resolve()

            if os.path.exists(new_path) and os.path.exists(cover_path):
                new_paths.append(new_path)
                self.load_cover_async(new_path, cover_path, loading)
                self.filepaths_table[new_path] = path
                return

            with moviepy.VideoFileClip(str(path)) as videofile:
                if not os.path.exists(cover_path):
                    try:
                        frame: numpy.ndarray = videofile.get_frame(
                            videofile.duration / 2
                        )
                        surface = pygame.image.frombytes(
                            frame.tobytes(), videofile.size, "RGB"
                        )
                        pygame.image.save(surface, cover_path)
                        self.music_covers[new_path] = surface
                    except Exception:
                        surface = None
                        pygame.image.save(surface, cover_path)
                        self.music_covers[new_path] = surface
                else:
                    self.load_cover_async(new_path, cover_path, loading)

                if os.path.exists(new_path):
                    new_paths.append(new_path)
                    self.filepaths_table[new_path] = path
                    return

                audiofile = videofile.audio
                if audiofile is None:
                    pygame.display.message_box(
                        "Could not load music",
                        f"Could not convert '{path}' to audio format: the video has no associated audio. Music will be skipped",
                        "error",
                        None,
                        ("Understood",),
                    )
                    return
                try:
                    audiofile.write_audiofile(str(new_path), verbose=True)
                except Exception as e:
                    pygame.display.message_box(
                        "Could not load music",
                        f"Could not convert '{path}' to audio format due to external exception: '{e}'. Music will be skipped",
                        "error",
                        None,
                        ("Understood",),
                    )
                    return
                new_paths.append(new_path)
                self.filepaths_table[new_path] = path

        else:
            if os.path.exists(cover_path):
                self.load_cover_async(path, cover_path, loading)
            new_paths.append(path)
            self.filepaths_table[path] = path

    def load_cover_async(self, key, path, loading=None):
        if loading is not None:
            self.music_covers[key] = loading
        thread = threading.Thread(
            target=load_cover_async, args=(path, key, self.music_covers)
        )
        thread.start()

    def cache_duration(self, path):
        try:
            soundfile = moviepy.AudioFileClip(str(path))
            duration = soundfile.duration
            self.musics_durations[path] = duration
            soundfile.close()
        except Exception:
            self.musics_durations[path] = None

    def remove(self, path):
        self.filepaths.remove(path)
        if path in self.filepaths_table:
            self.filepaths_table.pop(path)
        if path in self.music_covers:
            self.music_covers.pop(path)
        if path in self.musics_durations:
            self.musics_durations.pop(path)


class UIComponent:
    def __init__(self, app: "MusicPlayerApp"):
        self.app = app
        self.mili: mili.MILI = app.mili
        self.init()

    def init(self): ...

    def ui(self): ...

    def mult(self, size):
        return max(0, int(size * self.app.ui_mult))


class UIEntryline:
    def __init__(self, placeholder="Enter text...", target_files=True):
        self.text = ""
        self.cursor = 0
        self.placeholder = placeholder
        self.cursor_on = True
        self.cursor_time = pygame.time.get_ticks()
        self.action_start_time = pygame.time.get_ticks()
        self.action_data = None
        self.action_time = pygame.time.get_ticks()
        self.target_files = target_files

    def add(self, char):
        left, right = self.text[: self.cursor], self.text[self.cursor :]
        self.text = left + char + right
        self.cursor += 1

    def remove(self):
        if self.cursor > 0:
            left, right = self.text[: self.cursor], self.text[self.cursor :]
            self.text = left[:-1] + right
            self.cursor -= 1

    def canc(self):
        if self.cursor <= len(self.text):
            left, right = self.text[: self.cursor], self.text[self.cursor :]
            self.text = left[: self.cursor] + right[1:]

    def move(self, dir):
        self.cursor += dir
        if self.cursor < 0:
            self.cursor = 0
        if self.cursor > len(self.text):
            self.cursor = len(self.text)

    def start_action(self, func, *args):
        self.action_start_time = pygame.time.get_ticks()
        self.action_data = (func, args)

    def event(self, event):
        if event.type == pygame.TEXTINPUT:
            if self.target_files and event.text in [
                "<",
                ">",
                ":",
                '"',
                "/",
                "\\",
                "|",
                "?",
                "*",
                ".",
            ]:
                return
            self.set_cursor_on()
            self.add(event.text)
            self.start_action(self.add, event.text)
        if event.type == pygame.KEYDOWN:
            self.set_cursor_on()
            if event.key == pygame.K_LEFT:
                self.move(-1)
                self.start_action(self.move, -1)
            elif event.key == pygame.K_RIGHT:
                self.move(1)
                self.start_action(self.move, 1)
            elif event.key == pygame.K_BACKSPACE:
                self.remove()
                self.start_action(self.remove)
            elif event.key == pygame.K_DELETE:
                self.canc()
                self.start_action(self.canc)
        if event.type == pygame.KEYUP:
            self.action_data = None

    def update(self):
        if pygame.time.get_ticks() - self.cursor_time >= 350:
            self.cursor_on = not self.cursor_on
            self.cursor_time = pygame.time.get_ticks()

        if self.action_data is None:
            return
        if pygame.time.get_ticks() - self.action_start_time < (
            800 if self.action_data[0] is self.add else 500
        ):
            self.set_cursor_on()
            return

        if pygame.time.get_ticks() - self.action_time >= (
            80 if self.action_data[0] is self.add else 30
        ):
            self.action_time = pygame.time.get_ticks()
            self.action_data[0](*self.action_data[1])
            self.set_cursor_on()

    def set_cursor_on(self):
        self.cursor_on = True
        self.cursor_time = pygame.time.get_ticks()

    def draw_cursor(self, csize, offset, canva, element_data, rect):
        if not self.cursor_on:
            return
        curs = rect.h / 1.5
        xpos = rect.x + csize - offset + 5
        if offset != 0:
            xpos += 5
        pygame.draw.line(
            canva,
            (255,) * 3,
            (xpos, rect.y + rect.h / 2 - curs / 2),
            (xpos, rect.y + rect.h / 2 + curs / 2),
        )

    def ui(self, mili_: mili.MILI, rect, style, mult, bgcol=20, outlinecol=40):
        with mili_.begin(rect, style | {"axis": "x"}, get_data=True) as data:
            rect = data.rect
            mili_.rect({"color": (bgcol,) * 3, "border_radius": 0})
            mili_.rect(
                {
                    "color": (outlinecol,) * 3,
                    "outline": 1,
                    "border_radius": 0,
                    "draw_above": True,
                }
            )

            txtocursor = self.text[: self.cursor]
            size = mili_.text_size(txtocursor, {"size": mult(20)})
            offsetx = size.x - (rect.w - 15)
            if offsetx < 0:
                offsetx = 0

            if mili_.element(
                (0, 0, 0, 0),
                {
                    "align": "center",
                    "offset": (-offsetx, 0),
                    "post_draw_func": functools.partial(
                        self.draw_cursor, size.x, offsetx
                    ),
                },
                get_data=True,
            ):
                text = self.text
                if len(self.text) == 1:
                    text = f"{text} "
                mili_.text(
                    text if self.text else self.placeholder,
                    {"color": (255 if self.text else 120,) * 3, "size": mult(20)},
                )
