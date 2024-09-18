import mili
import pygame
from ui.common import *
from ui.data import HistoryData


class HistoryUI(UIComponent):
    def init(self):
        self.anim_back = animation(-5)
        self.anim_clear = animation(-2)
        self.cache = mili.ImageCache()
        self.scroll = mili.Scroll()
        self.scrollbar = mili.Scrollbar(self.scroll, 7, 0, 0, 0, "y")
        self.sbar_size = self.scrollbar.short_size

    def ui(self):
        self.mili.id_checkpoint(3000 + 600)
        handle_arrow_scroll(self.app, self.scroll, self.scrollbar)

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
                    "filly": "75",
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

                self.ui_modal_content()

            self.ui_overlay_btn(
                self.anim_back,
                self.back,
                self.app.back_image,
            )

    def ui_modal_content(self):
        with self.mili.begin(
            None,
            mili.RESIZE | mili.PADLESS | mili.CENTER | mili.X | {"clip_draw": False},
        ):
            self.mili.text_element(
                "History", {"size": self.mult(26)}, None, mili.CENTER
            )
            self.ui_image_btn(
                self.app.delete_image, self.action_clear, self.anim_clear, 30
            )
        with self.mili.begin(
            None, {"fillx": True, "filly": True} | mili.PADLESS, get_data=True
        ) as cont:
            self.scroll.update(cont)
            self.scrollbar.short_size = self.mult(self.sbar_size)
            self.scrollbar.update(cont)
            for history in reversed(self.app.history_data):
                self.ui_history(history)
            if len(self.app.history_data) <= 0:
                self.mili.text_element(
                    "No music in history",
                    {"size": self.mult(20), "color": (200,) * 3},
                    None,
                    {"align": "center"},
                )
            self.ui_scrollbar()
        self.mili.element((0, 0, 0, self.mult(4)))

    def ui_scrollbar(self):
        if self.scrollbar.needed:
            with self.mili.begin(self.scrollbar.bar_rect, self.scrollbar.bar_style):
                self.mili.rect({"color": (BSBAR_CV,) * 3})
                if handle := self.mili.element(
                    self.scrollbar.handle_rect, self.scrollbar.handle_style
                ):
                    self.mili.rect(
                        {"color": (cond(self.app, handle, *SHANDLE_CV) * 1.2,) * 3}
                    )
                    self.scrollbar.update_handle(handle)
                    if (
                        handle.hovered or handle.unhover_pressed
                    ) and self.app.can_interact():
                        self.app.cursor_hover = True

    def ui_history(self, history: HistoryData):
        if history.duration == "not cached" and history.music.pos_supported:
            history.music.cache_duration()
            history.duration = history.music.duration
        with self.mili.begin(
            (0, 0, 0, 0),
            {
                "fillx": "97" if self.scrollbar.needed else "99",
                "resizey": True,
                "anchor": "first",
                "offset": (
                    self.scrollbar.needed * -self.mult(self.sbar_size / 2),
                    self.scroll.get_offset()[1],
                ),
                "pady": 2,
                "spacing": 0,
                "align": "center",
            },
            get_data=True,
        ) as it:
            self.mili.rect({"color": (cond(self.app, it, *MENUB_CV),) * 3})
            self.ui_history_title(history)
            self.ui_history_time(history, it.rect)

            if self.app.can_interact():
                if it.left_just_released:
                    self.restore_history(history)
                if it.hovered or it.unhover_pressed:
                    self.app.cursor_hover = True

    def ui_history_time(self, history: HistoryData, cont_rect):
        if history.music.pos_supported:
            data = self.mili.line_element(
                [("-49.5", 0), ("49.5", 0)],
                {"color": (120,) * 3, "size": self.mult(2)},
                (0, 0, 0, self.mult(2)),
                {"fillx": True, "blocking": False},
                get_data=True,
            )
            w = (data.rect.w) * (history.position / history.duration)
            self.mili.line_element(
                [("-49.5", 0), ("49.5", 0)],
                {"color": "red", "size": self.mult(2)},
                (data.rect.topleft, (w, data.rect.h)),
                {"ignore_grid": True, "blocking": False},
            )
            txt, txtstyle = (
                f"{int(history.position/60):.0f}:{history.position %
                                                  60:.0f}/{int(history.duration/60):.0f}:{history.duration % 60:.0f}",
                {"size": self.mult(15), "color": (120,) * 3},
            )
            size = self.mili.text_size(txt, txtstyle)
            self.mili.text_element(
                txt,
                txtstyle,
                pygame.Rect((0, 0), size).move_to(
                    bottomright=(cont_rect.w - self.mult(2), cont_rect.h - self.mult(4))
                ),
                {"ignore_grid": True},
            )

    def ui_history_title(self, history: HistoryData):
        cover = history.music.cover
        if cover is None:
            cover = self.app.music_cover_image
        with self.mili.begin(
            None,
            {"resizey": True, "fillx": True, "blocking": False} | mili.PADLESS | mili.X,
        ):
            if cover is not None:
                self.mili.image_element(
                    cover,
                    {"cache": mili.ImageCache.get_next_cache()},
                    (0, 0, self.mult(50), self.mult(50)),
                    {"align": "center", "blocking": False},
                )
            self.mili.text_element(
                parse_music_stem(self.app, history.music.realstem),
                {
                    "size": self.mult(16),
                    "growx": False,
                    "growy": False,
                    "wraplen": "100",
                    "font_align": pygame.FONT_LEFT,
                    "align": "topleft",
                },
                (0, 0, 0, self.mult(60)),
                {"align": "first", "blocking": False, "fillx": True},
            )

    def restore_history(self, history: HistoryData):
        self.app.playlist_viewer.enter(history.music.playlist)
        self.app.play_music(
            history.music,
            history.music.playlist.get_group_sorted_musics().index(history.music),
        )
        self.app.set_music_pos(history.position)
        self.app.playlist_viewer.set_scroll_to_music()
        self.app.modal_state = "none"

    def action_clear(self):
        self.app.history_data = []

    def back(self):
        self.app.modal_state = "settings"

    def event(self, event):
        if self.app.listening_key:
            return False
        if event.type == pygame.MOUSEWHEEL:
            handle_wheel_scroll(event, self.app, self.scroll, self.scrollbar)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.back()
            return True
        return False
