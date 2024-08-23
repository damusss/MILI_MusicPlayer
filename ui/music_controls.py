import mili
import pygame
import random
from ui.miniplayer import MiniplayerUI
from ui.common import *


class MusicControlsUI(UIComponent):
    def init(self):
        self.minip = MiniplayerUI(self.app)
        self.img_cache = mili.ImageCache()
        self.main_cont = None
        self.offset = 0
        self.offset_restart_time = pygame.time.get_ticks()
        self.cont_height = 0
        self.small_cont = True
        self.anims = [animation(-3) for i in range(5)]
        self.handle_anim = animation(-10)
        self.slider = mili.Slider(False, True, 30, False)
        self.bigcover_cache = mili.ImageCache()
        self.black_cache = mili.ImageCache()
        self.music_videoclip_cover = None
        self.last_videoclip_cover = None

        self.play_image = load_icon("play")
        self.pause_image = load_icon("pause")
        self.skip_next_image = load_icon("skip_next")
        self.skip_previous_image = load_icon("skip_previous")
        self.loopon_image = load_icon("loopon")
        self.loopoff_image = load_icon("loopoff")
        self.minip_image = load_icon("opennew")
        self.maxip_image = pygame.transform.flip(self.minip_image, True, True)

    def ui(self):
        self.cont_height = 0
        if self.app.music is None:
            return
        self.get_videoclip_cover()
        self.get_bg_effect()

        if self.app.music_paused:
            self.app.music_play_time += self.app.delta_time * 1000

        self.small_cont = (
            self.main_cont is None
            or not self.main_cont.absolute_rect.collidepoint(pygame.mouse.get_pos())
        )
        contheight = self.mult(100 if self.small_cont else 116)
        bigcover = False

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
            cover = self.app.music_cover
            if self.music_videoclip_cover is not None and self.app.focused:
                cover = self.music_videoclip_cover
            if cover is not None:
                imgsize = self.mult(90)
                it = self.mili.image_element(
                    cover,
                    {
                        "cache": self.img_cache,
                        "pady": self.mult(5),
                        "smoothscale": True,
                    },
                    (0, 0, imgsize, imgsize),
                    {"align": "first", "blocking": True},
                )
                if it.absolute_hover and self.app.can_interact():
                    bigcover = True
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

        if bigcover:
            self.ui_big_cover()

        self.minip.run()

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
            self.music_auto_finish()
            return

        sizeperc = totalw * percentage
        self.mili.line_element(
            [(-totalw / 2, 0), (totalw / 2, 0)],
            {"color": (50,) * 3, "size": self.mult(3)},
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
            {"color": (255, 0, 0), "size": self.mult(3)},
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
            self.music_auto_finish()
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

                if handle.left_just_released and self.app.can_interact():
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
                if handle.just_hovered and self.app.can_interact():
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
            if not self.app.focused:
                self.offset = 0
            else:
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

    def get_videoclip_cover(self):
        self.music_videoclip_cover = None
        if not self.app.focused and self.minip.window is None:
            return
        if self.app.music_paused:
            self.music_videoclip_cover = self.last_videoclip_cover
            return
        if self.app.music_videoclip is not None:
            pos = (
                self.app.music_play_offset
                + (pygame.time.get_ticks() - self.app.music_play_time) / 1000
            )
            frame = self.app.music_videoclip.get_frame(pos)
            self.music_videoclip_cover = pygame.image.frombytes(
                frame.tobytes(), self.app.music_videoclip.size, "RGB"
            )
            self.last_videoclip_cover = self.music_videoclip_cover

    def get_bg_effect(self):
        self.app.bg_effect = False
        if not self.app.focused:
            return
        image = self.app.music_cover
        if self.music_videoclip_cover is not None:
            image = self.music_videoclip_cover
        if image is None:
            return
        if self.app.music_paused:
            self.app.bg_effect = True
            return
        color = pygame.Color(pygame.transform.average_color(image))
        color.a = 40
        self.app.bg_effect = True
        self.app.bg_effect_image.fill(color)

    def ui_big_cover(self):
        cover = self.app.music_cover
        if self.music_videoclip_cover is not None:
            cover = self.music_videoclip_cover
        if cover is None or cover is self.app.music_cover_image:
            return
        self.mili.image_element(
            SURF,
            {"fill": True, "fill_color": (0, 0, 0, 200), "cache": self.black_cache},
            ((0, 0), self.app.window.size),
            {"ignore_grid": True, "parent_id": 0, "z": 99999, "blocking": False},
        )
        size = mili.percentage(85, min(self.app.window.size))
        self.mili.image_element(
            cover,
            {"cache": self.bigcover_cache, "smoothscale": True},
            pygame.Rect(0, 0, size, size).move_to(
                center=(
                    self.app.window.size[0] / 2,
                    self.app.window.size[1] / 2,
                )
            ),
            {
                "ignore_grid": True,
                "blocking": False,
                "z": 999999,
                "parent_id": self.mili.stack_id,
            },
        )

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
            self.ui_control_btn(
                self.loopon_image if self.app.music_loops else self.loopoff_image,
                self.action_loop,
                40,
                3,
                True,
            )
            self.ui_control_btn(
                self.minip_image if self.minip.window is None else self.maxip_image,
                self.action_miniplayer,
                40,
                4,
                True,
            )

    def action_loop(self):
        self.app.music_loops = not self.app.music_loops

    def ui_control_btn(self, image, action, size, animi, special=False):
        anim = self.anims[animi]
        if it := self.mili.element(
            (0, 0, self.mult(size), self.mult(size)),
            {"align": "center", "clip_draw": False},
        ):
            if it.hovered and self.app.can_interact():
                (self.mili.rect if special else self.mili.circle)(
                    {
                        "color": (cond(self.app, it, *CONTROLS_CV),) * 3,
                        "border_radius": "20",
                    }
                    | mili.style.same(anim.value, "padx", "pady")
                )
            self.mili.image(
                image,
                {"cache": mili.ImageCache.get_next_cache()}
                | mili.style.same(self.mult(1) + anim.value, "padx", "pady"),
            )
            if it.left_just_released and self.app.can_interact():
                action()
            if it.just_hovered and self.app.can_interact():
                anim.goto_b()
            if it.just_unhovered:
                anim.goto_a()

    def action_miniplayer(self):
        if self.minip.window is None:
            self.minip.open()
        else:
            self.minip.close()

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
        self.app.playlist_viewer.scroll.scroll(0, self.app.mult(80) + 3)

    def action_skip_previous(self):
        if len(self.app.music_playlist.filepaths) <= 0:
            return
        new_idx = self.app.music_index - 1
        if new_idx < 0:
            return
        self.app.play_from_playlist(
            self.app.music_playlist, self.app.music_playlist.filepaths[new_idx], new_idx
        )

    def music_auto_finish(self):
        if self.app.shuffle:
            music_available = self.app.music_playlist.filepaths.copy()
            music_available.remove(self.app.music)
            new_music = random.choice(music_available)
            self.app.play_from_playlist(
                self.app.music_playlist,
                new_music,
                self.app.music_playlist.filepaths.index(new_music),
            )
            self.app.playlist_viewer.scroll.set_scroll(
                0, self.app.music_index * (self.app.mult(80) + 6)
            )
            return
        if self.app.music_loops:
            self.app.play_from_playlist(
                self.app.music_playlist, self.app.music, self.app.music_index
            )
            return
        self.action_skip_next(True, True)

    def event(self, event):
        if event.type == MUSIC_ENDEVENT:
            self.music_auto_finish()
        if event.type == pygame.WINDOWFOCUSGAINED:
            if event.window == self.minip.window:
                self.minip.focused = True
            else:
                self.minip.focused = False
        if event.type == pygame.WINDOWFOCUSLOST and event.window == self.minip.window:
            self.minip.focused = False
        if event.type == pygame.WINDOWCLOSE and event.window == self.minip.window:
            self.minip.close()
        if event.type == pygame.KEYDOWN:
            self.key_controls(event)

    def key_controls(self, event):
        if self.app.music is not None:
            if event.key in [
                pygame.K_KP_ENTER,
                pygame.K_RETURN,
                pygame.K_PAUSE,
                1073742085,
            ]:
                self.action_play()
            if event.key == pygame.K_SPACE and (
                self.app.view_state != "playlist"
                or not self.app.playlist_viewer.search_active
            ):
                self.action_play()
            if (
                event.mod & pygame.KMOD_META
                and event.mod & pygame.KMOD_SHIFT
                and event.mod & pygame.KMOD_CTRL
            ):
                self.action_play()
            if event.scancode == pygame.KSCAN_PAUSE:
                self.action_play()
            if event.key in [
                1073742082,
                pygame.K_RIGHT,
                pygame.K_KP_6,
            ]:
                self.action_skip_next(True, True)
            if event.key in [1073742083, pygame.K_LEFT, pygame.K_KP_4]:
                self.action_skip_previous()
        if event.key in [pygame.K_UP, pygame.K_KP_8]:
            self.app.volume += 0.05
            if self.app.volume > 1:
                self.app.volume = 1
            pygame.mixer.music.set_volume(self.app.volume)
        if event.key in [pygame.K_DOWN, pygame.K_KP_2]:
            self.app.volume -= 0.05
            if self.app.volume < 0:
                self.app.volume = 0
            pygame.mixer.music.set_volume(self.app.volume)
