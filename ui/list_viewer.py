import mili
import pygame
from ui.new_playlist import NewPlaylistUI
from ui.rename_playlist import RenamePlaylistUI
from ui.common import *


class ListViewerUI(UIComponent):
    def init(self):
        self.new_playlist = NewPlaylistUI(self.app)
        self.rename_playlist = RenamePlaylistUI(self.app)
        self.modal_state = "none"
        self.middle_selected = None

        self.anim_add_playlist = animation(-5)
        self.menu_anims = [animation(-4) for i in range(2)]

        self.scroll = mili.Scroll()
        self.scrollbar = mili.Scrollbar(self.scroll, 8, 3, 3, 0, "y")

        self.delete_image = load_icon("delete")
        self.rename_image = load_icon("edit")

    def ui(self):
        self.scrollbar.short_size = self.mult(8)
        self.mili.text_element(
            "Music Player", {"size": self.mult(35)}, None, {"align": "center"}
        )
        self.mili.line_element(
            [("-49.5", 0), ("49.5", 0)],
            {"size": 1, "color": (100,) * 3},
            (0, 0, 0, self.mult(10)),
            {"fillx": True},
        )

        with self.mili.begin(
            (0, 0, self.app.window.size[0], 0), {"filly": True}, get_data=True
        ) as scroll_cont:
            if len(self.app.playlists) > 0:
                self.scroll.update(scroll_cont)
                self.scrollbar.update(scroll_cont)

                for playlist in self.app.playlists:
                    self.ui_playlist(playlist)

                self.mili.text_element(
                    f"{len(self.app.playlists)} playlists",
                    {"size": self.mult(19), "color": (170,) * 3},
                    None,
                    {"offset": self.scroll.get_offset()},
                )

                self.ui_scrollbar()

            else:
                self.mili.text_element(
                    "No playlists",
                    {"size": self.mult(20), "color": (200,) * 3},
                    None,
                    {"align": "center"},
                )

        if self.modal_state == "none" and self.app.modal_state == "none":
            self.app.ui_overlay_btn(
                self.anim_add_playlist,
                self.action_new,
                self.app.playlistadd_image,  # ([("-20", 0), ("20", 0)], [(0, "20"), (0, "-20")]),
                "top",
            )

        if self.modal_state == "new_playlist":
            self.new_playlist.ui()
        elif self.modal_state == "rename_playlist":
            self.rename_playlist.ui()

    def ui_scrollbar(self):
        if self.scrollbar.needed:
            with self.mili.begin(self.scrollbar.bar_rect, self.scrollbar.bar_style):
                self.mili.rect({"color": (SBAR_CV,) * 3})
                if handle := self.mili.element(
                    self.scrollbar.handle_rect, self.scrollbar.handle_style
                ):
                    self.mili.rect(
                        {"color": (cond(self.app, handle, *SHANDLE_CV),) * 3}
                    )
                    self.scrollbar.update_handle(handle)

    def ui_playlist(self, playlist: Playlist):
        with self.mili.begin(
            (0, 0, 0, self.mult(80)),
            {
                "fillx": "100" if not self.scrollbar.needed else "98",
                "offset": self.scroll.get_offset(),
                "padx": self.mult(10),
                "axis": "x",
                "align": "first" if self.app.ui_mult < 1.1 else "center",
            },
        ) as cont:
            self.ui_playlist_bg(playlist, cont)

            imagesize = self.mult(70)
            cover = playlist.cover
            if cover is None:
                cover = self.app.playlist_cover
            if cover is not None:
                self.mili.image_element(
                    cover,
                    {"cache": mili.ImageCache.get_next_cache(), "smoothscale": True},
                    (0, 0, imagesize, imagesize),
                    {"align": "center", "blocking": False},
                )
            self.mili.text_element(
                playlist.name,
                {"size": self.mult(25)},
                None,
                {"align": "center", "blocking": False},
            )
            self.ui_playlist_helper(playlist)

            if cont.left_just_released and self.app.can_interact():
                self.app.playlist_viewer.enter(playlist)
            elif (
                cont.just_released_button == pygame.BUTTON_RIGHT
                and self.app.can_interact()
            ):
                self.app.open_menu(
                    playlist,
                    (self.rename_image, self.action_rename, self.menu_anims[0]),
                    (self.delete_image, self.action_delete, self.menu_anims[1]),
                )
            elif cont.just_pressed_button == pygame.BUTTON_MIDDLE:
                self.middle_selected = playlist

    def ui_playlist_helper(self, playlist):
        if self.middle_selected is playlist:
            self.mili.text_element(
                "Use the mouse wheel to move the playlist",
                {
                    "size": self.mult(13),
                    "color": (150,) * 3,
                    "align": "left",
                    "font_align": pygame.FONT_LEFT,
                },
                None,
                {
                    "align": "center",
                    "blocking": False,
                },
            )

    def ui_playlist_bg(self, playlist, cont):
        if self.app.bg_effect:
            self.mili.image(
                SURF,
                {
                    "fill": True,
                    "fill_color": (
                        *(
                            LIST_CV[1]
                            if self.app.menu_data == playlist
                            else cond(self.app, cont, *LIST_CV),
                        )
                        * 3,
                        ALPHA,
                    ),
                    "border_radius": 0,
                    "cache": mili.ImageCache.get_next_cache(),
                },
            )
        else:
            self.mili.rect(
                {
                    "color": (
                        LIST_CV[1]
                        if self.app.menu_data == playlist
                        else cond(self.app, cont, *LIST_CV),
                    )
                    * 3,
                    "border_radius": 0,
                }
            )

    def action_new(self):
        self.modal_state = "new_playlist"

    def action_rename(self):
        self.modal_state = "rename_playlist"
        self.rename_playlist.entryline.text = self.app.menu_data.name
        self.rename_playlist.entryline.cursor = len(self.app.menu_data.name)
        self.app.close_menu()

    def action_delete(self):
        btn = pygame.display.message_box(
            "Confirm deletion",
            "Are you sure you want to delete the playlist? The songs won't be deleted from disk. This action cannot be undone.",
            "warn",
            None,
            ("Proceed", "Cancel"),
        )
        if btn == 1:
            self.app.close_menu()
            return
        try:
            self.app.playlists.remove(self.app.menu_data)
        except Exception:
            pass
        self.app.close_menu()

    def event(self, event):
        if event.type == pygame.MOUSEBUTTONUP and event.button == pygame.BUTTON_MIDDLE:
            self.middle_selected = None
        if (
            event.type == pygame.MOUSEWHEEL
            and self.modal_state == "none"
            and self.app.modal_state == "none"
        ):
            if self.middle_selected is not None:
                idx = self.app.playlists.index(self.middle_selected)
                inc = -int(event.y)
                new_idx = idx + inc
                if new_idx < 0:
                    new_idx = 0
                if new_idx >= len(self.app.playlists):
                    new_idx = len(self.app.playlists) - 1
                self.app.playlists.remove(self.middle_selected)
                self.app.playlists.insert(new_idx, self.middle_selected)
            else:
                self.scroll.scroll(0, -(event.y * 40) * self.app.ui_mult)
                self.scrollbar.scroll_moved()
        if self.modal_state == "new_playlist":
            self.new_playlist.event(event)
        elif self.modal_state == "rename_playlist":
            self.rename_playlist.event(event)
