import mili
import pygame
from ui.common import *


class EditKeybindsUI(UIComponent):
    def init(self):
        self.anim_back = animation(-5)
        self.anim_reset = animation(-2)
        self.anim_remove = animation(-2)
        self.cache = mili.ImageCache()
        self.scroll = mili.Scroll()
        self.scrollbar = mili.Scrollbar(self.scroll, 5, 3, 3, 0, "y")
        self.listening_bind: Binding = None
        self.listening_idx = 0
        self.listening_key = None
        self.listening_ctrl = False

    def ui(self):
        with self.mili.begin(
            ((0, 0), self.app.window.size), {"ignore_grid": True} | mili.CENTER
        ):
            self.mili.image(
                SURF, {"fill": True, "fill_color": (0, 0, 0, 200), "cache": self.cache}
            )

            with self.mili.begin(
                (0, 0, 0, 0),
                {
                    "fillx": "90",
                    "filly": "76",
                    "align": "center",
                    "spacing": self.mult(13),
                    "offset": (
                        0,
                        -self.mult(50) * (self.app.music is not None)
                        - self.app.tbarh / 2,
                    ),
                }
                | mili.PADLESS,
            ):
                self.mili.rect({"color": (MODAL_CV,) * 3, "border_radius": "5"})

                self.ui_modal_content()

            self.app.ui_overlay_btn(
                self.anim_back,
                self.back,
                self.app.back_image,
            )
        if self.app.listening_key:
            self.ui_listening()

    def ui_modal_content(self):
        with self.mili.begin(
            None,
            mili.RESIZE | mili.PADLESS | mili.CENTER | mili.X | {"clip_draw": False},
        ):
            self.mili.text_element(
                "Keybinds", {"size": self.mult(26)}, None, mili.CENTER
            )
            self.app.ui_image_btn(
                self.app.reset_image, self.action_reset, self.anim_reset, 30
            )
        with self.mili.begin(
            None, {"fillx": True, "filly": True} | mili.PADLESS, get_data=True
        ) as cont:
            self.scroll.update(cont)
            self.scrollbar.update(cont)
            for name, bind in Keybinds.instance.keybinds.items():
                self.ui_keybind(name, bind)
            self.ui_scrollbar()
        self.mili.element(None)

    def ui_scrollbar(self):
        if self.scrollbar.needed:
            with self.mili.begin(self.scrollbar.bar_rect, self.scrollbar.bar_style):
                self.mili.rect({"color": (SBAR_CV * 1.5,) * 3})
                if handle := self.mili.element(
                    self.scrollbar.handle_rect, self.scrollbar.handle_style
                ):
                    self.mili.rect(
                        {"color": (cond(self.app, handle, *SHANDLE_CV) * 1.2,) * 3}
                    )
                    self.scrollbar.update_handle(handle)

    def ui_keybind(self, name, bind: Binding):
        height = self.mult(30)
        with self.mili.begin(
            (0, 0, 0, height),
            mili.PADLESS
            | mili.X
            | {
                "fillx": "97.5" if self.scrollbar.needed else True,
                "anchor": "max_spacing",
                "offset": self.scroll.get_offset(),
                "align": "first",
            },
        ):
            self.mili.text_element(
                name.replace("_", " ").title(),
                {"size": self.mult(16), "growx": False, "align": "right"},
                None,
                {"fillx": "35", "align": "center"},
            )
            self.ui_binds(bind)

    def ui_binds(self, bind):
        with self.mili.begin(
            None, {"fillx": "65", "filly": True} | mili.PADLESS | mili.X
        ):
            for i in range(2):
                display_txt = "-"
                pgkey = None
                if i <= len(bind.keys) - 1:
                    pgkey = bind.keys[i]
                    display_txt = pygame.key.name(pgkey).upper()
                    if display_txt.strip() == "":
                        display_txt = "UNKNOWN"
                    if bind.ctrl:
                        display_txt = f"CTRL + {display_txt}"

                if it := self.mili.element(None, {"filly": True, "fillx": True}):
                    self.mili.rect(
                        {
                            "color": (
                                (
                                    LISTM_CV[1]
                                    if (
                                        bind is self.listening_bind
                                        and i == self.listening_idx
                                        and self.app.listening_key
                                    )
                                    else cond(self.app, it, *LISTM_CV)
                                ),
                            )
                            * 3,
                            "border_radius": 0,
                        }
                    )
                    self.mili.text(display_txt, {"size": self.mult(15)})

                    if it.left_just_released and self.app.can_interact():
                        self.start_listening(bind, i)

    def ui_listening(self):
        with self.mili.begin(
            ((0, 0), self.app.window.size),
            {"ignore_grid": True, "parent_id": 0} | mili.CENTER,
        ):
            self.mili.image(
                SURF, {"fill": True, "fill_color": (0, 0, 0, 200), "cache": self.cache}
            )

            with self.mili.begin(
                (0, 0, 0, 0),
                {
                    "fillx": "80",
                    "resizey": True,
                    "align": "center",
                    "spacing": self.mult(13),
                    "offset": (
                        0,
                        -self.mult(50) * (self.app.music is not None)
                        - self.app.tbarh / 2,
                    ),
                },
            ):
                self.mili.rect({"color": (MODAL_CV,) * 3, "border_radius": "5"})
                with self.mili.begin(
                    None,
                    mili.RESIZE
                    | mili.PADLESS
                    | mili.CENTER
                    | mili.X
                    | {"clip_draw": False},
                ):
                    self.mili.text_element(
                        "Listening Key", {"size": self.mult(26)}, None, mili.CENTER
                    )
                    if self.listening_idx == 1:
                        self.app.ui_image_btn(
                            self.app.delete_image,
                            self.action_remove_keybind,
                            self.anim_remove,
                            30,
                        )
                text = "Press any key (optional ctrl modifier)"
                color = (120,) * 3
                size = 18
                if self.listening_key is not None:
                    size = 21
                    color = (255,) * 3
                    keytxt = pygame.key.name(self.listening_key).upper()
                    if keytxt.strip() == "":
                        keytxt = "UNKNOWN"
                    if self.listening_ctrl:
                        keytxt = f"CTRL + {keytxt}"
                    text = keytxt
                    if not self.get_key_ok():
                        color = (255, 0, 0)
                        text = f"'{keytxt}' is already used"
                if self.listening_key == pygame.K_ESCAPE and not self.listening_ctrl:
                    color = (255, 0, 0)
                    text = "'ESCAPE' is a reserved key"
                self.mili.text_element(
                    text,
                    {
                        "color": color,
                        "size": self.mult(size),
                        "wraplen": mili.percentage(75, self.app.window.size[0]),
                        "growx": False,
                        "slow_grow": True,
                    },
                    None,
                    {"fillx": True},
                )

    def get_key_ok(self):
        for bind in Keybinds.instance.keybinds.values():
            if bind.ctrl == self.listening_ctrl and self.listening_key in bind.keys:
                return False
        return True

    def action_remove_keybind(self):
        self.app.listening_key = False
        self.listening_bind.keys = [self.listening_bind.keys[0]]
        self.listening_bind.ctrl = False
        self.listening_key = None

    def start_listening(self, bind, idx):
        self.app.listening_key = True
        self.listening_bind = bind
        self.listening_idx = idx

    def action_reset(self):
        Keybinds.instance.reset()

    def back(self):
        self.app.modal_state = "settings"

    def event(self, event):
        if event.type == pygame.MOUSEWHEEL and not self.app.listening_key:
            self.scroll.scroll(0, -(event.y * 40) * self.app.ui_mult)
            self.scrollbar.scroll_moved()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.app.listening_key:
                self.app.listening_key = False
            else:
                self.back()
            return True
        if (
            event.type == pygame.KEYDOWN
            and self.app.listening_key
            and event.key not in [pygame.K_LCTRL, pygame.K_RCTRL]
        ):
            self.listening_ctrl = event.mod & pygame.KMOD_CTRL
            self.listening_key = event.key
        if (
            event.type == pygame.KEYUP
            and self.app.listening_key
            and self.listening_key is not None
            and self.get_key_ok()
        ):
            self.app.listening_key = False
            if len(self.listening_bind.keys) <= self.listening_idx:
                self.listening_bind.keys.append(self.listening_key)
            else:
                self.listening_bind.keys[self.listening_idx] = self.listening_key
            self.listening_bind.ctrl = self.listening_ctrl
            self.listening_key = None
        return False
