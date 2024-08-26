import mili
import pygame
import mili._core
from ui.common import *


class SettingsUI(UIComponent):
    def init(self):
        self.anim_close = animation(-5)
        self.anim_handle = animation(-3)
        self.anims = [animation(-3) for i in range(5)]
        self.cache = mili.ImageCache()
        self.slider = mili.Slider(False, True, (10, 10))

        self.vol0_image = load_icon("vol0")
        self.vol1_image = load_icon("vol1")
        self.vollow_image = load_icon("vollow")
        self.shuffleon_image = load_icon("shuffleon")
        self.shuffleoff_image = load_icon("shuffleoff")
        self.fps30_image = load_icon("fps30")
        self.fps60_image = load_icon("fps60")
        self.history_image = load_icon("history")

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
                    "fillx": "80",
                    "resizey": True,
                    "align": "center",
                    "spacing": self.mult(13),
                    "offset": (0, -self.app.tbarh),
                },
            ):
                self.mili.rect({"color": (MODAL_CV,) * 3, "border_radius": "5"})

                self.ui_modal_content()

            self.app.ui_overlay_btn(
                self.anim_close,
                self.close,
                self.app.close_image,
            )

    def ui_modal_content(self):
        self.mili.text_element("Settings", {"size": self.mult(26)}, None, mili.CENTER)
        with self.mili.begin(
            (0, 0, mili.percentage(70, self.app.window.size[0]), 0),
            mili.X
            | mili.PADLESS
            | {"resizey": True, "clip_draw": False, "spacing": self.mult(10)},
        ):
            vol_image = self.vol0_image
            if self.app.volume >= 0.5:
                vol_image = self.vol1_image
            elif self.app.volume > 0.05:
                vol_image = self.vollow_image
            self.app.ui_image_btn(vol_image, self.action_mute, self.anims[0], 45)
            self.ui_slider()
        self.ui_buttons()

    def ui_buttons(self):
        with self.mili.begin(
            None,
            {
                "resizex": True,
                "resizey": True,
                "axis": "x",
                "clip_draw": False,
                "align": "center",
            },
        ):
            self.app.ui_image_btn(
                self.history_image, self.action_history, self.anims[1]
            )
            self.app.ui_image_btn(
                self.app.loopon_image if self.app.loops else self.app.loopoff_image,
                self.action_loop,
                self.anims[2],
                br="50" if not self.app.loops else "5",
            )
            self.app.ui_image_btn(
                self.shuffleon_image if self.app.shuffle else self.shuffleoff_image,
                self.action_shuffle,
                self.anims[3],
                br="50" if not self.app.shuffle else "5",
            )
            self.app.ui_image_btn(
                self.fps60_image if self.app.user_framerate == 60 else self.fps30_image,
                self.action_fps,
                self.anims[4],
                br="5",
            )

    def action_history(self):
        self.app.modal_state = "history"

    def action_fps(self):
        if self.app.user_framerate == 60:
            self.app.user_framerate = 30
        else:
            self.app.user_framerate = 60

    def action_shuffle(self):
        self.app.shuffle = not self.app.shuffle

    def ui_slider(self):
        self.slider.handle_size = self.mult(40), self.mult(40)

        with self.mili.begin(
            (0, 0, 0, self.mult(10)),
            {"align": "center", "fillx": True} | self.slider.area_style,
            get_data=True,
        ) as bar:
            self.slider.update_area(bar)
            self.mili.rect({"color": (30,) * 3})

            if self.app.volume > 0:
                self.mili.rect_element(
                    {"color": (120,) * 3},
                    (0, 0, bar.rect.w * self.app.volume, bar.rect.h),
                    {"ignore_grid": True},
                )

            if handle := self.mili.element(
                self.slider.handle_rect.move(0, self.slider.handle_rect.h / 8),
                self.slider.handle_style,
            ):
                self.slider.update_handle(handle)
                self.mili.circle(
                    {"color": (255,) * 3}
                    | mili.style.same(
                        self.mult(12 + self.anim_handle.value), "padx", "pady"
                    )
                )
                if handle.just_hovered and self.app.can_interact():
                    self.anim_handle.goto_b()
                if handle.just_unhovered and not handle.left_pressed:
                    self.anim_handle.goto_a()
                if (
                    handle.left_just_released
                    and self.app.can_interact()
                    and not handle.hovered
                ):
                    self.anim_handle.goto_a()
                if handle.left_pressed:
                    self.change_volume()
                else:
                    self.slider.valuex = self.app.volume

    def change_volume(self):
        self.app.volume = self.slider.valuex
        pygame.mixer.music.set_volume(self.app.volume)

    def action_mute(self):
        if self.app.volume > 0:
            self.app.vol_before_mute = self.app.volume
            self.app.volume = 0
        else:
            self.app.volume = self.app.vol_before_mute
        pygame.mixer.music.set_volume(self.app.volume)

    def action_loop(self):
        self.app.loops = not self.app.loops

    def close(self):
        self.app.modal_state = "none"

    def event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return True
        return False
