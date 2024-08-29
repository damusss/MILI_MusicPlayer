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
ANIMSPEED = 50
ANIMEASE = mili.animation.EaseIn()
MUSIC_ENDEVENT = pygame.event.custom_type()
HISTORY_LEN = 100
RESIZESIZE = 3
WIN_MIN_SIZE = (200, 300)
DISCORD_COOLDOWN = 20000

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
BORDER_CV = 120
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


class UIComponent:
    def __init__(self, app: "MusicPlayerApp"):
        self.app = app
        self.mili: mili.MILI = app.mili
        self.init()

    def init(self): ...

    def ui(self): ...

    def mult(self, size):
        return max(0, int(size * self.app.ui_mult))
