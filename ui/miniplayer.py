import mili
import pygame
import typing
import ctypes
from ui.common import *

if typing.TYPE_CHECKING:
    from MusicPlayer import MusicPlayerApp

MINIP_PREFERRED_SIZES = 200, 200


class MiniplayerUI:
    def __init__(self, app: "MusicPlayerApp"):
        self.app = app
        self.window = None
        self.focused = False
        self.mili = mili.MILI(None)
        self.press_pos = pygame.Vector2()
        self.rel_pos = pygame.Vector2()
        self.ui_mult = 1
        self.canresize = False
        self.cover_cache = mili.ImageCache()
        self.bg_cache = mili.ImageCache()
        self.anims = [animation(-5) for i in range(3)]
        self.controls_rect = pygame.Rect()
        self.bg_surf = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.hovered = False
        self.pressed = False
        self.click_event = False

        self.mili.default_styles(
            text={
                "sysfont": False,
                "name": "data/ytfont.ttf",
                "growx": True,
                "growy": True,
            },
            line={"color": (255,) * 3},
            circle={"antialias": True},
            image={"smoothscale": True},
        )

        self.resize_image = load_icon("resize")
        self.borderless_image = load_icon("borderless")
        self.back_image = pygame.transform.flip(load_icon("opennew"), True, False)

    def mult(self, v):
        return max(1, int(v * self.ui_mult * 0.7))

    def open(self):
        self.window = pygame.Window(
            "MP Miniplayer",
            MINIP_PREFERRED_SIZES,
            resizable=True,
            borderless=True,
        )
        self.window.always_on_top = True
        self.window.minimum_size = (100, 100)
        self.window.get_surface()
        self.window.set_icon(self.app.music_cover_image)
        try:
            self.window.flash(pygame.FLASH_BRIEFLY)
        except Exception:
            pass
        self.canresize = False
        self.focused = True

    def set_borderon(self):
        self.window = pygame.Window(
            self.window.title, self.window.size, self.window.position, resizable=True
        )
        self.window.always_on_top = True
        self.window.minimum_size = (100, 100)
        self.canresize = True
        self.window.get_surface()
        self.window.set_icon(self.app.music_cover_image)

    def set_borderoff(self):
        self.window = pygame.Window(
            self.window.title,
            self.window.size,
            self.window.position,
            resizable=True,
            borderless=True,
        )
        self.window.always_on_top = True
        self.window.minimum_size = (100, 100)
        self.canresize = False
        self.window.get_surface()
        self.window.set_icon(self.app.music_cover_image)

    def toggle_border(self):
        if self.canresize:
            self.set_borderoff()
        else:
            self.set_borderon()

    def close(self):
        self.window.destroy()
        self.window = None
        self.focused = False

    def move_window(self):
        if not self.can_interact():
            return

        just = pygame.mouse.get_just_pressed()[0]
        if just:
            self.rel_pos = pygame.Vector2(pygame.mouse.get_pos())
            self.press_pos = pygame.Vector2(self.rel_pos + self.window.position)

        if pygame.mouse.get_pressed()[0] and not just:
            new = pygame.Vector2(self.window.position) + pygame.mouse.get_pos()
            self.window.position = (
                self.press_pos + (new - self.press_pos) - self.rel_pos
            )

    def can_interact(self):
        if self.app.sdl2 is not None:
            return self.window is not None and (
                (not self.app.focused and self.hovered) or self.focused
            )
        return self.focused and self.window is not None

    def back_to_app(self):
        self.close()
        self.app.window.focus()
        self.app.window.restore()
        try:
            self.app.window.flash(pygame.FLASH_BREIFLY)
        except Exception:
            pass

    def ui(self):
        self.get_hovered()

        wm = self.window.size[0] / MINIP_PREFERRED_SIZES[0]
        hm = self.window.size[1] / MINIP_PREFERRED_SIZES[1]
        self.ui_mult = min(2, max(0.8, (wm * 0.1 + hm * 1) / 1.1))

        self.mili.rect({"color": (3,) * 3})
        self.mili.rect(
            {"color": (20,) * 3, "outline": 1, "border_radius": 0, "draw_above": True}
        )

        self.ui_cover()
        if self.app.sdl2 is None or self.hovered:
            self.ui_controls()
        self.ui_line()

        if self.app.sdl2 is None or self.hovered:
            self.ui_top_btn(self.back_image, "left", self.back_to_app)
            if self.window is None:
                return
            self.ui_top_btn(
                self.resize_image if not self.canresize else self.borderless_image,
                "rightleft",
                self.toggle_border,
            )
            self.ui_top_btn(self.app.close_image, "right", self.close)

    def get_hovered(self):
        if self.app.sdl2 is None:
            self.hovered = False
            return
        x = ctypes.c_int(0)
        y = ctypes.c_int(0)
        res = self.app.sdl2.mouse.SDL_GetGlobalMouseState(
            ctypes.byref(x), ctypes.byref(y)
        )
        self.hovered = pygame.Rect(self.window.position, self.window.size).collidepoint(
            x.value, y.value
        )
        self.click_event = False
        if res == 1 and self.hovered and not self.pressed:
            self.pressed = True
        if res != 1:
            if self.pressed:
                self.click_event = True
            self.pressed = False

    def ui_line(self):
        totalw = self.window.size[0] - self.mult(8)
        pos = (
            self.app.music_play_offset
            + (pygame.time.get_ticks() - self.app.music_play_time) / 1000
        )
        percentage = (pos) / self.app.music_duration

        sizeperc = totalw * percentage
        data = self.mili.line_element(
            [(-totalw / 2, 0), (totalw / 2, 0)],
            {"color": (50,) * 3, "size": self.mult(2)},
            pygame.Rect(0, 0, totalw, 2).move_to(
                midbottom=(self.window.size[0] / 2, self.window.size[1] - self.mult(3))
            ),
            {"align": "center", "ignore_grid": True},
            get_data=True,
        )
        self.mili.line_element(
            [(-totalw / 2, 0), (-totalw / 2 + sizeperc, 0)],
            {"color": (255, 0, 0), "size": self.mult(2)},
            data.absolute_rect,
            {"ignore_grid": True, "parent_id": 0, "z": 99999},
        )

    def ui_cover(self):
        cover = self.app.music_cover_image
        if self.app.music_cover is not None:
            cover = self.app.music_cover
        if self.app.music_controls.music_videoclip_cover:
            cover = self.app.music_controls.music_videoclip_cover
        if cover is None:
            return

        self.mili.image_element(
            cover, {"cache": self.cover_cache}, None, {"fillx": True, "filly": True}
        )

    def ui_controls(self):
        with self.mili.begin(
            pygame.Rect((0, 0), self.controls_rect.size).move_to(
                midbottom=(self.window.size[0] / 2, self.window.size[1] - self.mult(15))
            ),
            {
                "resizex": True,
                "resizey": True,
                "align": "center",
                "clip_draw": False,
                "axis": "x",
                "ignore_grid": True,
            },
            get_data=True,
        ) as data:
            self.controls_rect = data.rect
            self.mili.image(
                self.bg_surf,
                {
                    "cache": self.bg_cache,
                    "border_radius": "50",
                    "fill": True,
                    "fill_color": MP_BG_FILL,
                },
            )
            if self.app.music_index > 0:
                self.ui_control_btn(
                    self.app.music_controls.skip_previous_image,
                    50,
                    self.action_previous,
                    0,
                )
            self.ui_control_btn(
                self.app.music_controls.play_image
                if self.app.music_paused
                else self.app.music_controls.pause_image,
                60,
                self.action_play,
                1,
            )
            if self.app.music_index < len(self.app.music_playlist.filepaths) - 1:
                self.ui_control_btn(
                    self.app.music_controls.skip_next_image, 50, self.action_next, 2
                )

    def ui_control_btn(self, image, size, action, animi):
        anim = self.anims[animi]
        size = self.mult(size)
        if it := self.mili.element((0, 0, size, size), {"align": "center"}):
            if it.hovered and self.can_interact():
                self.mili.image(
                    self.bg_surf,
                    {
                        "cache": mili.ImageCache.get_next_cache(),
                        "fill": True,
                        "border_radius": "50",
                        "fill_color": cond(self, it, *MP_OVERLAY_CV),
                    },
                )
            self.mili.image(
                image,
                {"cache": mili.ImageCache.get_next_cache()}
                | mili.style.same(self.mult(1) + anim.value / 3, "padx", "pady"),
            )
            if (
                (it.left_just_released and self.can_focus_click())
                or (self.click_event and it.absolute_hover)
            ) and self.can_interact():
                action()
            if it.just_hovered and self.can_interact():
                anim.goto_b()
            if it.just_unhovered and self.can_interact():
                anim.goto_a()

    def can_focus_click(self):
        return self.app.sdl2 is None and self.focused

    def action_play(self):
        self.app.music_controls.action_play()

    def action_next(self):
        self.app.music_controls.action_skip_next()

    def action_previous(self):
        self.app.music_controls.action_skip_previous()

    def ui_top_btn(self, img, side, action):
        size = self.mult(35)
        offset = self.mult(4)
        if it := self.mili.element(
            pygame.Rect(0, 0, size, size).move_to(topleft=(offset, offset))
            if side == "left"
            else pygame.Rect(0, 0, size, size).move_to(
                topright=(
                    self.window.size[0]
                    - (offset if side == "right" else size + offset * 2),
                    offset,
                )
            ),
            {"ignore_grid": True, "parent_id": 0},
        ):
            self.mili.image(
                self.bg_surf,
                {
                    "cache": self.bg_cache,
                    "border_radius": 0,
                    "fill": True,
                    "fill_color": cond(self, it, *MP_OVERLAY_CV),
                },
            )
            self.mili.image(img, {"cache": mili.ImageCache.get_next_cache()})
            if (
                (it.left_just_released and self.can_focus_click())
                or (self.click_event and it.absolute_hover)
            ) and self.can_interact():
                action()

    def run(self):
        if self.window is None:
            return

        self.move_window()
        surf = self.window.get_surface()
        self.mili.set_canva(surf)
        surf.fill("black")

        self.mili.start(
            {
                "anchor": "center",
                "padx": self.mult(3),
                "pady": self.mult(3),
            },
            is_global=False,
        )
        self.ui()

        if self.window is None:
            return

        self.mili.update_draw()
        self.window.flip()
