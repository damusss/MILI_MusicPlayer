import os
import mili
import json
import pygame
import typing


if typing.TYPE_CHECKING:
    from MusicPlayer import MusicPlayerApp

PREFERRED_SIZES = (415, 700)
MINIP_PREFERRED_SIZES = 200, 200
UI_SIZES = (450, 700)
SURF = pygame.Surface((10, 10), pygame.SRCALPHA)
FORMATS = ["mp4", "wav", "mp3", "ogg", "flac", "opus", "wv", "mod", "aiff"]
POS_SUPPORTED = ["mp4", "mp3", "ogg", "flac", "mod"]
MUSIC_ENDEVENT = pygame.event.custom_type()
HISTORY_LEN = 100
RESIZE_SIZE = 3
WIN_MIN_SIZE = (200, 300)
DISCORD_COOLDOWN = 20000
BIG_COVER_COOLDOWN = 300

BG_CV = 3
MUSIC_CV = 3, 10, 5
LIST_CV = MUSIC_CV
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
BORDER_CV = 100
TOPB_CV = 15, 25, 8


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


def load_icon(name):
    return pygame.image.load(f"data/icons/{name}.png").convert_alpha()


def animation(value):
    return mili.animation.ABAnimation(
        0, value, "number", 50, 50, mili.animation.EaseIn()
    )


class UIComponent:
    def __init__(self, app: "MusicPlayerApp"):
        self.app = app
        self.mili: mili.MILI = app.mili
        self.init()

    def init(self): ...

    def ui(self): ...

    def mult(self, size):
        return max(0, int(size * self.app.ui_mult))


class Binding:
    def __init__(self, *keys, ctrl=False):
        self.keys = list(keys)
        self.ctrl = ctrl

    def check(self, event: pygame.Event, extra_keys):
        if not self.ctrl:
            return event.type == pygame.KEYDOWN and any(
                [event.key == k for k in self.keys + list(extra_keys)]
            )
        return (
            event.type == pygame.KEYDOWN
            and any([event.key == k for k in self.keys + list(extra_keys)])
            and event.mod & pygame.KMOD_CTRL
        )


class Keybinds:
    instance: "Keybinds" = None

    def __init__(self, app):
        self.app = app
        self.reset()
        Keybinds.instance = self

    @classmethod
    def check(cls, name, event, *extra_keys):
        bind = cls.instance.keybinds[name]
        return (
            bind.check(event, extra_keys)
            and (not cls.instance.app.input_stolen or bind.ctrl)
            and not cls.instance.app.listening_key
        )

    def reset(self):
        self.keybinds = {
            "confirm": Binding(pygame.K_RETURN),
            "toggle_settings": Binding(pygame.K_s),
            "volume_up": Binding(pygame.K_UP),
            "volume_down": Binding(pygame.K_DOWN),
            "previous_track": Binding(pygame.K_LEFT),
            "next_track": Binding(pygame.K_RIGHT),
            "pause_music": Binding(pygame.K_SPACE),
            "quit": Binding(pygame.K_q, ctrl=True),
            "new/add": Binding(pygame.K_a, ctrl=True),
            "save": Binding(pygame.K_s, ctrl=True),
            "open_history": Binding(pygame.K_h, ctrl=True),
            "toggle_search": Binding(pygame.K_f, ctrl=True),
            "erase_input": Binding(pygame.K_BACKSPACE, ctrl=True),
            "change_cover": Binding(pygame.K_c, ctrl=True),
            "end_music": Binding(pygame.K_e, ctrl=True),
            "rewind_music": Binding(pygame.K_r, ctrl=True),
            "toggle_miniplayer": Binding(pygame.K_d, ctrl=True),
        }
        self.default_keybinds = self.keybinds.copy()

    def load_from_data(self, data):
        for name, bdata in data.items():
            if name not in self.keybinds:
                print("gogogo")
                continue
            binding = self.keybinds[name]
            binding.keys = bdata["keys"]
            binding.ctrl = bdata["ctrl"]

    def get_save_data(self):
        return {
            name: {"keys": bind.keys, "ctrl": bind.ctrl}
            for name, bind in self.keybinds.items()
        }
