import mili
import pygame
from ui.common import *
from ui.data import HistoryData


class HistoryUI(UIComponent):
    def init(self):
        self.anim_back = animation(-5)
        self.cache = mili.ImageCache()
        self.scroll = mili.Scroll()

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

            self.app.ui_overlay_btn(
                self.anim_back,
                self.back,
                self.app.back_image,
            )

    def ui_modal_content(self):
        self.mili.text_element("History", {"size": self.mult(26)}, None, mili.CENTER)
        with self.mili.begin(
            None, {"fillx": True, "filly": True} | mili.PADLESS, get_data=True
        ) as cont:
            self.scroll.update(cont)
            for history in reversed(self.app.history_data):
                self.ui_history(history)
        self.mili.element((0, 0, 0, self.mult(4)))

    def ui_history(self, history: HistoryData):
        if history.duration == "not cached" and history.music.pos_supported:
            history.music.cache_duration()
            history.duration = history.music.duration
        with self.mili.begin(
            (0, 0, 0, 0),
            {
                "fillx": True,
                "resizey": True,
                "anchor": "first",
                "offset": self.scroll.get_offset(),
                "pady": 2,
                "spacing": 0,
            },
        ) as it:
            self.mili.rect({"color": (cond(self.app, it, *LISTM_CV),) * 3})
            self.ui_history_title(history)
            self.ui_history_time(history)

            if it.left_just_released and self.app.can_interact():
                self.restore_history(history)

    def restore_history(self, history: HistoryData):
        self.app.playlist_viewer.enter(history.music.playlist)
        self.app.play_music(
            history.music, history.music.playlist.musiclist.index(history.music)
        )
        self.app.music_play_offset = history.position
        pygame.mixer.music.set_pos(history.position)
        self.app.playlist_viewer.scroll.set_scroll(
            0, self.app.music_index * (self.app.mult(80) + 3)
        )
        self.app.playlist_viewer.scrollbar.scroll_moved()
        self.app.modal_state = "none"

    def ui_history_time(self, history):
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
                history.music.realstem,
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

    def back(self):
        self.app.modal_state = "settings"

    def event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.scroll.scroll(0, -(event.y * 40) * self.app.ui_mult)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.back()
            return True
        return False
