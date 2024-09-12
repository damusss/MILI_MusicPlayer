import os
import mili
import json
import pygame
import typing

if typing.TYPE_CHECKING:
    from MusicPlayer import MusicPlayerApp

PREFERRED_SIZES = (415, 700)
MINIP_PREFERRED_SIZES = 200, 200
UI_SIZES = (480, 720)
SURF = pygame.Surface((10, 10), pygame.SRCALPHA)
FORMATS = ["mp4", "wav", "mp3", "ogg", "flac", "opus", "wv", "mod", "aiff"]
POS_SUPPORTED = ["mp4", "mp3", "ogg", "flac", "mod"]
MUSIC_ENDEVENT = pygame.event.custom_type()
HISTORY_LEN = 100
RESIZE_SIZE = 3
WIN_MIN_SIZE = (200, 300)
DISCORD_COOLDOWN = 20000
BIG_COVER_COOLDOWN = 300
SAVE_COOLDOWN = 60000 * 2
RATIO_MIN = 0.5
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
MENUB_CV = 20, 30, 18
MP_OVERLAY_CV = (50, 50, 50, 150), (80, 80, 80, 150), (30, 30, 30, 150)
MP_BG_FILL = (50, 50, 50, 120)
ALPHA = 170
BORDER_CV = 100
TOPB_CV = 15, 25, 8


def cond(app: "MusicPlayerApp", it: mili.Interaction, normal, hover, press):
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
    scroll.scroll(0, amount * 600 * dt)
    if scrollbar is not None:
        scrollbar.scroll_moved()


def handle_wheel_scroll(
    event: pygame.Event,
    app: "MusicPlayerApp",
    scroll: mili.Scroll,
    scrollbar: mili.Scrollbar = None,
):
    scroll.scroll(0, -(event.y * 50) * app.ui_mult)
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

    def ui_image_btn(
        self, image, action, anim: mili.animation.ABAnimation, size=62, br="50"
    ):
        if it := self.mili.element(
            (0, 0, self.mult(size), self.mult(size)),
            {"align": "center", "clip_draw": False},
        ):
            (self.mili.rect if br != "50" else self.mili.circle)(
                {
                    "color": (cond(self.app, it, MODAL_CV, MODALB_CV[1], MODALB_CV[2]),)
                    * 3,
                    "border_radius": br,
                }
                | mili.style.same(
                    (anim.value if br != "50" else anim.value / 1.8), "padx", "pady"
                )
            )
            self.mili.image(
                image,
                mili.style.same(self.mult(3) + anim.value, "padx", "pady")
                | {"smoothscale": True},
            )
            if self.app.can_interact():
                if it.hovered or it.unhover_pressed:
                    self.app.cursor_hover = True
                if it.left_just_released:
                    action()
                if it.just_hovered:
                    anim.goto_b()
            if it.just_unhovered:
                anim.goto_a()

    def ui_overlay_btn(
        self, anim: mili.animation.ABAnimation, on_action, image, side="bottom"
    ):
        size = self.mult(55)
        offset = self.mult(8)
        xoffset = offset * 0.8
        if (
            self.app.view_state == "list" and self.app.list_viewer.scrollbar.needed
        ) or (
            self.app.view_state == "playlist"
            and self.app.playlist_viewer.scrollbar.needed
        ):
            xoffset = offset * 1.5
        if it := self.mili.element(
            pygame.Rect(0, 0, size, size).move_to(
                bottomright=(
                    self.app.window.size[0] - xoffset,
                    self.app.window.size[1]
                    - self.app.tbarh
                    - offset
                    - self.app.music_controls.cont_height
                    - {
                        "bottom": 0,
                        "top": size + self.mult(5),
                        "supertop": size * 2 + offset,
                        "megatop": size * 3 + offset * 1.5,
                    }[side],
                )
            ),
            {"ignore_grid": True, "clip_draw": False},
        ):
            self.mili.circle(
                {"color": (cond(self.app, it, *OVERLAY_CV),) * 3, "border_radius": "50"}
                | mili.style.same(int(anim.value / 1.8), "padx", "pady")
            )
            self.mili.image(
                image,
                {"cache": mili.ImageCache.get_next_cache()}
                | mili.style.same(self.mult(8 + anim.value / 1.8), "padx", "pady"),
            )
            if self.app.can_interact():
                if it.hovered or it.unhover_pressed:
                    self.app.cursor_hover = True
                if it.just_hovered:
                    anim.goto_b()
                if it.left_just_released:
                    on_action()
                    anim.goto_a()
            if it.just_unhovered:
                anim.goto_a()

    def ui_overlay_top_btn(
        self,
        anim: mili.animation.ABAnimation,
        on_action,
        image,
        side,
        sidei=0,
        red=False,
    ):
        if self.app.custom_title:
            size = self.app.tbarh
        else:
            y = self.mili.text_size("Music Player", {"size": self.mult(35)}).y
            size = self.mult(36)
            offset = self.mult(10)
        if it := self.mili.element(
            pygame.Rect(0, 0, size, size).move_to(
                topleft=(
                    0,
                    0,
                )
                if self.app.custom_title
                else (offset, y / 2 - size / 2 + 5)
            )
            if side == "left"
            else pygame.Rect(0, 0, size, size).move_to(
                topright=(self.app.window.size[0] - (size * sidei), 0)
                if self.app.custom_title
                else (
                    self.app.window.size[0]
                    - (offset if side == "right" else offset * 2 + size),
                    y / 2 - size / 2 + 5,
                )
            ),
            {
                "ignore_grid": True,
                "clip_draw": False,
                "z": 9999,
            },
        ):
            if red:
                color = (TOPB_CV[0],) * 3
                if self.app.can_abs_interact():
                    if it.hovered:
                        color = (200, 0, 0)
                    if it.left_pressed:
                        color = (80, 0, 0)
            else:
                color = (cond(self.app, it, *TOPB_CV),) * 3
            self.mili.rect(
                {"color": color, "border_radius": 0}
                | mili.style.same(int(anim.value), "padx", "pady")
            )
            self.mili.image(
                image,
                {"cache": mili.ImageCache.get_next_cache(), "smoothscale": True}
                | mili.style.same(self.mult(3 + anim.value), "padx", "pady"),
            )
            if self.app.can_interact():
                if it.hovered or it.unhover_pressed:
                    self.app.cursor_hover = True
                if it.just_hovered:
                    anim.goto_b()
                if it.left_just_released:
                    on_action()
                    anim.goto_a()
            if it.just_unhovered:
                anim.goto_a()


class Keybinds:
    class Binding:
        class Bind:
            def __init__(self, key, ctrl=False):
                self.key = key
                self.ctrl = ctrl

        def __init__(self, *binds, ctrl=False):
            newbinds = []
            for bind in binds:
                if isinstance(bind, int):
                    newbinds.append(Keybinds.Binding.Bind(bind, ctrl))
                else:
                    newbinds.append(bind)
            self.binds: list[Keybinds.Binding.Bind] = newbinds

        def get_keycodes(self):
            return [bind.key for bind in self.binds]

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

    instance: "Keybinds" = None

    def __init__(self, app):
        self.app: "MusicPlayerApp" = app
        self.reset()
        Keybinds.instance = self

    @classmethod
    def check(cls, name, event, *extra_keys):
        return not cls.instance.app.listening_key and cls.instance.keybinds[name].check(
            event, extra_keys, cls.instance.app.input_stolen
        )

    def reset(self):
        Binding = Keybinds.Binding
        self.keybinds = {
            "confirm": Binding(pygame.K_RETURN),
            "toggle_settings": Binding(pygame.K_s),
            "volume_up": Binding(pygame.K_UP, pygame.K_KP8),
            "volume_down": Binding(pygame.K_DOWN, pygame.K_KP2),
            "previous_track": Binding(pygame.K_LEFT, pygame.K_KP4),
            "next_track": Binding(pygame.K_RIGHT, pygame.K_KP6),
            "back_5_s": Binding(pygame.K_LEFT, pygame.K_KP4, ctrl=True),
            "skip_5_s": Binding(pygame.K_RIGHT, pygame.K_KP6, ctrl=True),
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

    def load_from_data(self, data: dict):
        for name, bdata in data.items():
            if name not in self.keybinds:
                continue
            binding = self.keybinds[name]
            binding.binds = [Keybinds.Binding.Bind(d["key"], d["ctrl"]) for d in bdata]

    def get_save_data(self):
        return {
            name: [{"key": bind.key, "ctrl": bind.ctrl} for bind in binding.binds]
            for name, binding in self.keybinds.items()
        }
