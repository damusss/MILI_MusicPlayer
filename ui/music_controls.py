import mili
import pygame
import random
from ui.common import *
from ui.miniplayer import MiniplayerUI


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
        self.timebar_controlled = False
        self.timebar_pos = None
        self.handle_percentage = None
        self.big_cover = False
        self.bigcover_time = 0

        self.play_image = load_icon("play")
        self.pause_image = load_icon("pause")
        self.skip_next_image = load_icon("skip_next")
        self.skip_previous_image = load_icon("skip_previous")

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
                bottomleft=(0, self.app.window.size[1] - self.app.tbarh)
            ),
            {"axis": "x", "pady": 0},
            get_data=True,
        ) as self.main_cont:
            self.mili.rect({"color": (MUSICC_CV,) * 3})
            bigcover = self.ui_container()

        self.ui_track_control()

        if bigcover:
            if not self.big_cover:
                self.big_cover = True
                self.bigcover_time = pygame.time.get_ticks()
        else:
            self.big_cover = False

        if (
            bigcover
            and pygame.time.get_ticks() - self.bigcover_time >= BIG_COVER_COOLDOWN
        ):
            self.ui_big_cover()

        self.minip.run()

    def ui_container(self):
        bigcover = False
        imgsize = 0
        cover = self.app.music.cover
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
            if it.left_just_released and self.app.can_interact():
                if self.app.view_state != "playlist":
                    self.app.playlist_viewer.enter(self.app.music.playlist)
                self.app.playlist_viewer.scroll.set_scroll(
                    0, self.app.music_index * (self.app.mult(80) + 3)
                )
                self.app.playlist_viewer.scrollbar.scroll_moved()
            if it.absolute_hover and self.app.can_interact():
                bigcover = True
        else:
            self.mili.element((0, 0, 0, 0))
        self.ui_controls_cont()
        return bigcover

    def ui_track_control(self):
        if self.app.music.pos_supported or self.app.music.duration is None:
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
                    bottomleft=(
                        0,
                        self.app.window.size[1] - self.mult(32) - self.app.tbarh,
                    )
                ),
                {"ignore_grid": True, "parent_id": 0, "z": 9999},
            )

    def ui_time(self):
        pos = self.app.get_music_pos()
        txt, txtstyle = (
            f"{int(pos/60):.0f}:{pos%60:.0f}/{int(self.app.music.duration/60):.0f}:{self.app.music.duration%60:.0f}",
            {"color": (120,) * 3, "size": self.mult(20)},
        )
        size = self.mili.text_size(txt, txtstyle)
        self.mili.text_element(
            txt,
            txtstyle,
            pygame.Rect(0, 0, size.x, size.y).move_to(
                bottomright=(
                    self.app.window.size[0] - self.mult(8),
                    self.app.window.size[1] - self.mult(20),
                )
            ),
            {"ignore_grid": True, "z": 9999, "parent_id": 0},
        )

    def ui_small_slider(self):
        totalw = self.app.window.size[0] - self.mult(15)
        pos = self.app.get_music_pos()
        percentage = (pos) / self.app.music.duration

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
                    self.app.window.size[1] - self.mult(6),
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
                    self.app.window.size[1] - self.mult(6),
                )
            ),
            {"ignore_grid": True, "parent_id": 0, "z": 99999},
        )

    def ui_slider(self):
        self.slider.handle_size = (self.mult(48), self.mult(48))
        totalw = self.app.window.size[0] - self.mult(15)
        pos = self.app.get_music_pos()
        percentage = (pos) / self.app.music.duration
        if self.timebar_pos is not None:
            percentage = self.timebar_pos

        if percentage > 1.01 and self.timebar_pos is None:
            self.music_auto_finish()
            return

        if self.handle_percentage is not None:
            percentage = self.handle_percentage

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

            handle = self.ui_slider_handle(percentage)
            mpressed = pygame.mouse.get_pressed()[0]
            if not self.timebar_controlled:
                if (
                    not handle.absolute_hover
                    and self.app.can_interact()
                    and sbar.absolute_hover
                    and mpressed
                ):
                    self.timebar_controlled = True
                    self.handle_anim.goto_b()
            else:
                if not mpressed:
                    self.timebar_controlled = False
                    if self.timebar_pos is not None:
                        pygame.mixer.music.set_pos(
                            self.timebar_pos * self.app.music.duration
                        )
                        self.app.music_play_time = pygame.time.get_ticks()
                        self.app.music_play_offset = (
                            self.timebar_pos * self.app.music.duration
                        )
                    self.timebar_pos = None

            if self.timebar_controlled:
                mposx = pygame.mouse.get_pos()[0]
                relmpos = mposx - sbar.absolute_rect.x
                newpos = pygame.math.clamp(relmpos / sbar.absolute_rect.w, 0, 1)
                self.timebar_pos = newpos
                self.slider.valuex = newpos

    def ui_slider_handle(self, percentage):
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
            if not self.timebar_controlled:
                if handle.left_just_released and self.app.can_interact():
                    pygame.mixer.music.set_pos(
                        self.slider.valuex * self.app.music.duration
                    )
                    self.app.music_play_time = pygame.time.get_ticks()
                    self.app.music_play_offset = (
                        self.slider.valuex * self.app.music.duration
                    )
                if not handle.left_pressed:
                    self.slider.valuex = percentage
                    self.handle_percentage = None
                else:
                    self.handle_percentage = self.slider.valuex
                if handle.just_hovered and self.app.can_interact():
                    self.handle_anim.goto_b()
                if handle.just_unhovered:
                    self.handle_anim.goto_a()
        return handle

    def ui_controls_cont(self):
        with self.mili.begin(
            (0, 0, 0, self.cont_height),
            {"fillx": True, "pady": 0, "spacing": 0},
            get_data=True,
        ) as cont:
            txt, txtstyle = (
                f"{self.app.music.realstem}",
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

    def ui_big_cover(self):
        cover = self.app.music.cover
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
                    (self.app.window.size[1] - self.app.tbarh) / 2,
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
            if self.app.music_index < len(self.app.music.playlist.musiclist) - 1:
                self.ui_control_btn(self.skip_next_image, self.action_skip_next, 40, 2)
            self.ui_control_btn(
                self.app.loopon_image
                if self.app.music_loops
                else self.app.loopoff_image,
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
            if pos >= self.app.music.duration:
                self.music_videoclip_cover = SURF
                return
            frame = self.app.music_videoclip.get_frame(pos)
            self.music_videoclip_cover = pygame.image.frombytes(
                frame.tobytes(), self.app.music_videoclip.size, "RGB"
            )
            self.last_videoclip_cover = self.music_videoclip_cover

    def get_bg_effect(self):
        self.app.bg_effect = False
        if not self.app.focused:
            return
        image = self.app.music.cover
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

    def action_loop(self):
        self.app.music_loops = not self.app.music_loops

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
        self.app.discord_presence.update()

    def action_skip_next(self, stop_if_end=False, consider_loop=False):
        if len(self.app.music.playlist.musiclist) <= 0:
            if stop_if_end:
                self.app.end_music()
            return
        new_idx = self.app.music_index + 1
        if new_idx >= len(self.app.music.playlist.musiclist):
            if consider_loop and self.app.loops:
                new_idx = 0
            else:
                if stop_if_end:
                    self.app.end_music()
                return
        self.app.play_music(self.app.music.playlist.musiclist[new_idx], new_idx)
        self.app.playlist_viewer.scroll.scroll(0, self.app.mult(80) + 3)
        self.app.playlist_viewer.scrollbar.scroll_moved()

    def action_skip_previous(self):
        if len(self.app.music.playlist.musiclist) <= 0:
            return
        new_idx = self.app.music_index - 1
        if new_idx < 0:
            return
        self.app.play_music(self.app.music.playlist.musiclist[new_idx], new_idx)

    def music_auto_finish(self):
        if self.app.music_loops:
            self.app.play_music(self.app.music, self.app.music_index)
            return
        if self.app.shuffle:
            music_available = self.app.music.playlist.musiclist.copy()
            music_available.remove(self.app.music)
            new_music = random.choice(music_available)
            self.app.play_music(
                new_music,
                self.app.music.playlist.musiclist.index(new_music),
            )
            self.app.playlist_viewer.scroll.set_scroll(
                0, self.app.music_index * (self.app.mult(80) + 3)
            )
            self.app.playlist_viewer.scrollbar.scroll_moved()
            return
        self.action_skip_next(True, True)

    def event(self, event):
        if event.type == MUSIC_ENDEVENT:
            if self.app.music is None:
                return
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
