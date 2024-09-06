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
SAVE_COOLDOWN = 60000 * 3

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
KEYB_CV = 20, 32, 18
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


def handle_arrow_scroll(dt, scroll: mili.Scroll, scrollbar: mili.Scrollbar = None):
    keys = pygame.key.get_pressed()
    amount = 0
    upbind = Keybinds.instance.keybinds["scroll_up"]
    downbind = Keybinds.instance.keybinds["scroll_down"]
    if any([keys[key] for key in upbind.get_keycodes()]):
        amount -= 1
    if any([keys[key] for key in downbind.get_keycodes()]):
        amount += 1
    scroll.scroll(0, amount * 300 * dt)
    if scrollbar is not None:
        scrollbar.scroll_moved()


def parse_music_stem(app: "MusicPlayerApp", stem: str):
    if app.strip_youtube_id:
        if len(stem) >= 14:
            if stem.endswith("]") and stem[-13] == "[" and stem[-14] == " ":
                return stem[:-14]
        return stem
    return stem


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
    class Bind:
        def __init__(self, key, ctrl=False):
            self.key = key
            self.ctrl = ctrl

    def get_keycodes(self):
        return [bind.key for bind in self.binds]

    def __init__(self, *binds, ctrl=False):
        newbinds = []
        for bind in binds:
            if isinstance(bind, int):
                newbinds.append(Binding.Bind(bind, ctrl))
            else:
                newbinds.append(bind)
        self.binds: list[Binding.Bind] = newbinds

    def check(self, event: pygame.Event, extra_keys, input_stolen):
        if event.type == pygame.KEYDOWN:
            for key in extra_keys:
                if event.key == key and not input_stolen:
                    return True
            for bind in self.binds:
                if bind.ctrl:
                    if event.key == bind.key and event.mod & pygame.KMOD_CTRL:
                        return True
                else:
                    if (
                        event.key == bind.key
                        and not input_stolen
                        and not event.mod & pygame.KMOD_CTRL
                    ):
                        return True

        return False


class Keybinds:
    instance: "Keybinds" = None

    def __init__(self, app):
        self.app = app
        self.reset()
        Keybinds.instance = self

    @classmethod
    def check(cls, name, event, *extra_keys):
        return not cls.instance.app.listening_key and cls.instance.keybinds[name].check(
            event, extra_keys, cls.instance.app.input_stolen
        )

    def reset(self):
        self.keybinds = {
            "confirm": Binding(pygame.K_RETURN),
            "toggle_settings": Binding(pygame.K_s),
            "volume_up": Binding(pygame.K_UP, pygame.K_KP8),
            "volume_down": Binding(pygame.K_DOWN, pygame.K_KP2),
            "previous_track": Binding(pygame.K_LEFT, pygame.K_KP4),
            "next_track": Binding(pygame.K_RIGHT, pygame.K_KP6),
            "pause_music": Binding(pygame.K_SPACE, pygame.K_KP_ENTER),
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
            "scroll_up": Binding(pygame.K_PAGEUP, pygame.K_KP9),
            "scroll_down": Binding(pygame.K_PAGEDOWN, pygame.K_KP3),
        }
        self.default_keybinds = self.keybinds.copy()

    def load_from_data(self, data):
        for name, bdata in data.items():
            if name not in self.keybinds:
                continue
            binding = self.keybinds[name]
            binding.binds = [Binding.Bind(d["key"], d["ctrl"]) for d in bdata]

    def get_save_data(self):
        return {
            name: [{"key": bind.key, "ctrl": bind.ctrl} for bind in binding.binds]
            for name, binding in self.keybinds.items()
        }
