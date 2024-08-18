import mili
import pygame
from ui.common import *


class MusicControlsUI(UIComponent):
    def init(self):
        self.img_cache = mili.ImageCache()
        self.main_cont = None
        self.offset = 0
        self.offset_restart_time = pygame.time.get_ticks()
        self.cont_height = 0
        self.small_cont = True
        self.anims = [animation(-3) for i in range(3)]
        self.handle_anim = animation(-10)
        self.slider = mili.Slider(False, True, 30, False)

        self.play_image = load_icon("play")
        self.pause_image = load_icon("pause")
        self.skip_next_image = load_icon("skip_next")
        self.skip_previous_image = load_icon("skip_previous")

    def ui(self):
        self.cont_height = 0
        if self.app.music is None:
            return

        if self.app.music_paused:
            self.app.music_play_time += self.app.delta_time * 1000

        self.small_cont = (
            self.main_cont is None
            or not self.main_cont.absolute_rect.collidepoint(pygame.mouse.get_pos())
        )
        contheight = self.mult(100 if self.small_cont else 116)

        self.cont_height = contheight
        with self.mili.begin(
            pygame.Rect(0, 0, self.app.window.size[0], contheight).move_to(
                bottomleft=(0, self.app.window.size[1])
            ),
            {"axis": "x", "pady": 0},
            get_data=True,
        ) as self.main_cont:
            self.mili.rect({"color": (MUSICC_CV,) * 3})
            imgsize = 0
            if self.app.music_cover is not None:
                imgsize = self.mult(90)
                self.mili.image_element(
                    self.app.music_cover,
                    {
                        "cache": self.img_cache,
                        "pady": self.mult(5),
                        "smoothscale": True,
                    },
                    (0, 0, imgsize, imgsize),
                    {"align": "first", "blocking": False},
                )
            else:
                self.mili.element((0, 0, 0, 0))
            self.ui_controls_cont()

        if (
            self.app.music_ref.suffix[1:].lower() in POS_SUPPORTED
            or self.app.music_duration is None
        ):
            if self.small_cont:
                self.ui_small_slider()
            else:
                self.ui_slider()
                self.ui_time()
        elif not self.small_cont:
            self.mili.text_element(
                "Audio format does not support track positioning",
                {"color": (150,) * 3, "size": self.mult(18)},
                pygame.Rect(0, 0, self.app.window.size[0], 0).move_to(
                    bottomleft=(0, self.app.window.size[1] - self.mult(32))
                ),
                {"ignore_grid": True, "parent_id": 0, "z": 9999},
            )

    def ui_time(self):
        pos = (
            self.app.music_play_offset
            + (pygame.time.get_ticks() - self.app.music_play_time) / 1000
        )
        txt, txtstyle = (
            f"{int(pos/60):.0f}:{pos%60:.0f}/{int(self.app.music_duration/60):.0f}:{self.app.music_duration%60:.0f}",
            {"color": (120,) * 3, "size": self.mult(20)},
        )
        size = self.mili.text_size(txt, txtstyle)
        self.mili.text_element(
            txt,
            txtstyle,
            pygame.Rect(0, 0, size.x, size.y).move_to(
                bottomright=(
                    self.app.window.size[0] - self.mult(8),
                    self.app.window.size[1] - self.mult(22),
                )
            ),
            {"ignore_grid": True, "z": 9999, "parent_id": 0},
        )

    def ui_small_slider(self):
        totalw = self.app.window.size[0] - self.mult(15)
        pos = (
            self.app.music_play_offset
            + (pygame.time.get_ticks() - self.app.music_play_time) / 1000
        )
        percentage = (pos) / self.app.music_duration

        if percentage > 1.01:
            self.action_skip_next(True, True)
            return

        sizeperc = totalw * percentage
        self.mili.line_element(
            [(-totalw / 2, 0), (totalw / 2, 0)],
            {"color": (50,) * 3, "size": 3},
            pygame.Rect(0, 0, totalw, 2).move_to(
                midbottom=(
                    self.app.window.size[0] / 2,
                    self.app.window.size[1] - self.mult(5),
                )
            ),
            {"ignore_grid": True, "parent_id": 0, "z": 99999},
        )
        self.mili.line_element(
            [(-totalw / 2, 0), (-totalw / 2 + sizeperc, 0)],
            {"color": (255, 0, 0), "size": 3},
            pygame.Rect(0, 0, totalw, 2).move_to(
                midbottom=(
                    self.app.window.size[0] / 2,
                    self.app.window.size[1] - self.mult(5),
                )
            ),
            {"ignore_grid": True, "parent_id": 0, "z": 99999},
        )

    def ui_slider(self):
        self.slider.handle_size = (self.mult(48), self.mult(48))
        totalw = self.app.window.size[0] - self.mult(15)
        pos = (
            self.app.music_play_offset
            + (pygame.time.get_ticks() - self.app.music_play_time) / 1000
        )
        percentage = (pos) / self.app.music_duration

        if percentage > 1.01:
            self.action_skip_next(True, True)
            return

        sizeperc = totalw * min(1, percentage)
        with self.mili.begin(
            pygame.Rect(0, 0, totalw, self.mult(5)).move_to(
                midbottom=(
                    self.app.window.size[0] / 2,
                    self.app.window.size[1] - self.mult(10),
                )
            ),
            self.slider.area_style | {"ignore_grid": True, "parent_id": 0, "z": 9999},
            get_data=True,
        ) as sbar:
            self.slider.update_area(sbar)
            self.mili.rect({"color": (30,) * 3})

            self.mili.rect_element(
                {"color": (255, 0, 0)},
                (0, 0, sizeperc, self.mult(5)),
                {"ignore_grid": True},
            )

            if handle := self.mili.element(
                self.slider.handle_rect.move(0, self.slider.handle_size[1] / 17),
                self.slider.handle_style | {"z": 99999},
            ):
                self.slider.update_handle(handle)
                self.mili.rect(
                    {
                        "color": (255,) * 3,
                        "border_radius": "50",
                        "padx": str(75 + self.handle_anim.value),
                        "pady": str(75 + self.handle_anim.value),
                    }
                )

                if handle.left_just_released:
                    pygame.mixer.music.set_pos(
                        self.slider.valuex * self.app.music_duration
                    )
                    self.app.music_play_time = pygame.time.get_ticks()
                    self.app.music_play_offset = (
                        self.slider.valuex * self.app.music_duration
                    )
                    percentage = (pos) / self.app.music_duration
                if not handle.left_pressed:
                    self.slider.valuex = percentage
                if handle.just_hovered:
                    self.handle_anim.goto_b()
                if handle.just_unhovered:
                    self.handle_anim.goto_a()

    def ui_controls_cont(self):
        with self.mili.begin(
            (0, 0, 0, self.cont_height),
            {"fillx": True, "pady": 0, "spacing": 0},
            get_data=True,
        ) as cont:
            txt, txtstyle = (
                f"{self.app.music_ref.name}",
                {"size": self.mult(22), "align": "left"},
            )
            size = self.mili.text_size(txt, txtstyle).x
            diff = size - cont.rect.w
            if diff > 0:
                if pygame.time.get_ticks() - self.offset_restart_time >= 2000:
                    self.offset += self.app.delta_time * 35
                if self.offset > diff * 1.45:
                    self.offset = 0
                    self.offset_restart_time = pygame.time.get_ticks()
            else:
                self.offset = 0
            self.mili.text_element(
                txt,
                txtstyle,
                None,
                {"align": "first", "offset": (-self.offset, 0)},
            )
            self.ui_controls()

    def ui_controls(self):
        with self.mili.begin(
            None,
            {
                "resizex": True,
                "resizey": True,
                "align": "center",
                "axis": "x",
                "clip_draw": False,
                "offset": (0, -self.mult(5)),
            },
        ):
            if self.app.music_index > 0:
                self.ui_control_btn(
                    self.skip_previous_image, self.action_skip_previous, 40, 0
                )
            self.ui_control_btn(
                self.play_image if self.app.music_paused else self.pause_image,
                self.action_play,
                50,
                1,
            )
            if self.app.music_index < len(self.app.music_playlist.filepaths) - 1:
                self.ui_control_btn(self.skip_next_image, self.action_skip_next, 40, 2)

    def ui_control_btn(self, image, action, size, animi):
        anim = self.anims[animi]
        if it := self.mili.element(
            (0, 0, self.mult(size), self.mult(size)),
            {"align": "center", "clip_draw": False},
        ):
            if it.hovered:
                self.mili.rect(
                    {"color": (cond(it, *CONTROLS_CV),) * 3, "border_radius": "50"}
                    | mili.style.same(anim.value, "padx", "pady")
                )
            self.mili.image(
                image, mili.style.same(self.mult(1) + anim.value, "padx", "pady")
            )
            if it.left_just_released:
                action()
            if it.just_hovered:
                anim.goto_b()
            if it.just_unhovered:
                anim.goto_a()

    def action_play(self):
        if self.app.music_paused:
            pygame.mixer.music.unpause()
            self.app.music_paused = False
        else:
            pygame.mixer.music.pause()
            self.app.music_paused = True

    def action_skip_next(self, stop_if_end=False, consider_loop=False):
        if len(self.app.music_playlist.filepaths) <= 0:
            if stop_if_end:
                self.app.end_music()
            return
        new_idx = self.app.music_index + 1
        if new_idx >= len(self.app.music_playlist.filepaths):
            if consider_loop and self.app.loops:
                new_idx = 0
            else:
                if stop_if_end:
                    self.app.end_music()
                return
        self.app.play_from_playlist(
            self.app.music_playlist, self.app.music_playlist.filepaths[new_idx], new_idx
        )

    def action_skip_previous(self):
        if len(self.app.music_playlist.filepaths) <= 0:
            return
        new_idx = self.app.music_index - 1
        if new_idx < 0:
            return
        self.app.play_from_playlist(
            self.app.music_playlist, self.app.music_playlist.filepaths[new_idx], new_idx
        )

    def event(self, event):
        if event.type == MUSIC_ENDEVENT:
            self.action_skip_next(True, True)
