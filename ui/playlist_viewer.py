import mili
import pygame
import pathlib
from ui.add_music import AddMusicUI
from ui.change_cover import ChangeCoverUI
from ui.rename_music import RenameMusicUI
from ui.move_music import MoveMusicUI
from ui.common import *


class PlaylistViewerUI(UIComponent):
    def init(self):
        self.playlist: Playlist = None
        self.anim_add_music = animation(-5)
        self.anim_cover = animation(-5)
        self.anim_back = animation(-3)
        self.anim_search = animation(-5)
        self.menu_anims = [animation(-4) for i in range(3)]
        self.modal_state = "none"
        self.middle_selected = None
        self.search_active = False
        self.search_entryline = UIEntryline("Enter search...", False)

        self.add_music = AddMusicUI(self.app)
        self.change_cover = ChangeCoverUI(self.app)
        self.rename_music = RenameMusicUI(self.app)
        self.move_music = MoveMusicUI(self.app)

        self.scroll = mili.Scroll()
        self.scrollbar = mili.Scrollbar(self.scroll, 8, 3, 3, 0, "y")
        self.cover_cache = mili.ImageCache()
        self.bigcover_cache = mili.ImageCache()
        self.black_cache = mili.ImageCache()

        self.back_image = load_icon("back")
        self.rename_image = load_icon("edit")
        self.change_cover_image = load_icon("cover")
        self.forward_image = load_icon("forward")
        self.delete_image = load_icon("delete")
        self.search_image = load_icon("search")
        self.searchoff_image = load_icon("searchoff")
        self.backspace_image = load_icon("backspace")

    def sort_searched_songs(self):
        scores = {}
        rawsearch = self.search_entryline.text.strip()
        search = rawsearch.lower()
        for i, path in enumerate(self.playlist.filepaths):
            score = 0
            rawname = str(self.playlist.filepaths_table[path].stem)
            name = rawname.lower()
            if rawsearch in rawname:
                score += 100
            if search in name:
                score += 80
            words = rawsearch.split(" ")
            for rawword in words:
                if rawword in rawname:
                    score += 20
                if rawword.strip() in name:
                    score += 10
            scores[path] = (score, i)
        return [
            (v[1][1], v[0])
            for v in sorted(list(scores.items()), key=lambda x: x[1][0], reverse=True)
        ]

    def enter(self, playlist):
        self.playlist = playlist
        self.app.change_state("playlist")

    def ui(self):
        if self.search_active:
            self.search_entryline.update()
        self.scrollbar.short_size = self.mult(8)
        if self.playlist is None:
            self.back()

        big_cover = self.ui_title()
        self.ui_container()

        if self.modal_state == "none" and self.app.modal_state == "none":
            self.app.ui_overlay_top_btn(
                self.anim_back, self.back, self.back_image, "left"
            )
            self.app.ui_overlay_btn(
                self.anim_add_music,
                self.action_add_music,
                self.app.playlistadd_image,  # ([("-20", 0), ("20", 0)], [(0, "20"), (0, "-20")]),
                "top",
            )
            self.app.ui_overlay_btn(
                self.anim_cover, self.action_cover, self.change_cover_image, "supertop"
            )
            self.app.ui_overlay_btn(
                self.anim_search,
                self.action_search,
                self.searchoff_image if self.search_active else self.search_image,
                "megatop",
            )
        elif self.modal_state == "add":
            self.add_music.ui()
        elif self.modal_state == "move":
            self.move_music.ui()
        elif self.modal_state == "cover":
            self.change_cover.ui()
        elif self.modal_state == "rename":
            self.rename_music.ui()

        if big_cover:
            self.ui_big_cover()

    def ui_container(self):
        with self.mili.begin(
            (0, 0, self.app.window.size[0], 0), {"filly": True}, get_data=True
        ) as scroll_cont:
            if self.search_active:
                paths = self.sort_searched_songs()
            else:
                paths = list(enumerate(self.playlist.filepaths))
            if len(paths) > 0:
                self.scroll.update(scroll_cont)
                self.scrollbar.update(scroll_cont)

                for i, path in paths:
                    self.ui_music(path, i)

                self.mili.text_element(
                    f"{len(self.playlist.filepaths)} tracks",
                    {"size": self.mult(19), "color": (170,) * 3},
                    None,
                    {"offset": self.scroll.get_offset()},
                )

                if self.scrollbar.needed:
                    with self.mili.begin(
                        self.scrollbar.bar_rect, self.scrollbar.bar_style
                    ):
                        self.mili.rect({"color": (SBAR_CV,) * 3})
                        if handle := self.mili.element(
                            self.scrollbar.handle_rect, self.scrollbar.handle_style
                        ):
                            self.mili.rect(
                                {"color": (cond(self.app, handle, *SHANDLE_CV),) * 3}
                            )
                            self.scrollbar.update_handle(handle)

            else:
                self.mili.text_element(
                    "No music matches your search"
                    if self.search_active
                    else "No music",
                    {"size": self.mult(20), "color": (200,) * 3},
                    None,
                    {"align": "center"},
                )

    def ui_title(self):
        ret = False
        with self.mili.begin(None, mili.RESIZE | mili.PADLESS | mili.CENTER):
            if self.playlist.cover is not None:
                with self.mili.begin(
                    (0, 0, 0, 0),
                    {"resizex": True, "resizey": True, "align": "center", "axis": "x"},
                ):
                    it = self.mili.image_element(
                        self.playlist.cover,
                        {"cache": self.cover_cache, "smoothscale": True},
                        (0, 0, self.mult(80), self.mult(80)),
                        {"align": "center"},
                    )
                    if (
                        it.absolute_hover
                        and self.modal_state == "none"
                        and self.app.modal_state == "none"
                        and self.app.can_interact()
                    ):
                        ret = True
                    self.ui_title_txt()
            else:
                self.ui_title_txt()
            if self.search_active:
                self.ui_search()
        self.mili.line_element(
            [("-49.5", 0), ("49.5", 0)],
            {"size": 1, "color": (100,) * 3},
            (0, 0, 0, self.mult(7)),
            {"fillx": True},
        )
        return ret

    def ui_search(self):
        with self.mili.begin(
            (0, 0, self.app.window.size[0] - self.mult(20), 0),
            {"resizey": True} | mili.PADLESS | mili.X,
        ):
            size = self.mult(30)
            self.search_entryline.ui(
                self.mili,
                (0, 0, 0, size),
                {"fillx": True},
                self.mult,
                CONTROLS_CV[0] + 5,
                CONTROLS_CV[1],
            )
            if it := self.mili.element((0, 0, size, size)):
                self.mili.rect(
                    {
                        "color": (cond(self.app, it, *OVERLAY_CV),) * 3,
                        "border_radius": 0,
                    }
                )
                self.mili.image(
                    self.backspace_image, {"cache": mili.ImageCache.get_next_cache()}
                )
                if it.left_just_released and self.app.can_interact():
                    self.search_entryline.text = ""
                    self.search_entryline.cursor = 0

    def ui_big_cover(self):
        self.mili.image_element(
            SURF,
            {"fill": True, "fill_color": (0, 0, 0, 200), "cache": self.black_cache},
            ((0, 0), self.app.window.size),
            {"ignore_grid": True, "parent_id": 0, "z": 99999, "blocking": False},
        )
        size = mili.percentage(80, min(self.app.window.size))
        self.mili.image_element(
            self.playlist.cover,
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

    def ui_title_txt(self):
        self.mili.text_element(
            f"{self.playlist.name}",
            {"size": self.mult(32)},
            None,
            {"align": "center"},
        )

    def action_search(self):
        if self.search_active:
            self.stop_searching()
        else:
            self.search_active = True

    def action_cover(self):
        self.modal_state = "cover"

    def action_add_music(self):
        self.modal_state = "add"

    def back(self):
        self.app.change_state("list")
        self.scroll.set_scroll(0, 0)
        self.scrollbar.scroll_moved()
        if self.modal_state == "move":
            self.move_music.close()
        elif self.modal_state == "cover":
            self.change_cover.close()
        elif self.modal_state == "add":
            self.add_music.close()

    def ui_music(self, path, idx):
        with self.mili.begin(
            (0, 0, 0, self.mult(80)),
            {
                "fillx": "100" if not self.scrollbar.needed else "98",
                "offset": self.scroll.get_offset(),
                "padx": self.mult(8),
                "axis": "x",
                "align": "first" if self.app.ui_mult < 1.1 else "center",
                "anchor": "first",
            },
        ) as cont:
            self.mili.rect(
                {
                    "color": (
                        MUSIC_CV[1]
                        if self.app.music == path
                        else cond(self.app, cont, *MUSIC_CV),
                    )
                    * 3,
                    "border_radius": 0,
                }
            )
            opath: pathlib.Path = self.playlist.filepaths_table[path]
            imagesize = 0
            cover = self.playlist.music_covers.get(path, self.app.music_cover_image)
            if cover is None:
                cover = self.app.music_cover_image
            if cover is not None:
                imagesize = self.mult(70)
                self.mili.image_element(
                    cover,
                    {"cache": mili.ImageCache.get_next_cache(), "smoothscale": True},
                    (0, 0, imagesize, imagesize),
                    {"align": "center", "blocking": False},
                )
            self.mili.text_element(
                opath.name,
                {
                    "size": self.mult(18),
                    "growx": False,
                    "growy": False,
                    "wraplen": self.app.window.size[0] / 1.1 - imagesize,
                    "font_align": pygame.FONT_LEFT,
                    "align": "topleft",
                },
                (0, 0, self.app.window.size[0] / 1.1 - imagesize, self.mult(80) / 1.1),
                {"align": "first", "blocking": False},
            )
            if cont.left_just_released and self.app.can_interact():
                self.start_playing(path, idx)
            if (
                cont.just_released_button == pygame.BUTTON_RIGHT
                and self.app.can_interact()
            ):
                self.app.open_menu(
                    path,
                    (self.rename_image, self.action_rename, self.menu_anims[0]),
                    (self.forward_image, self.action_forward, self.menu_anims[1]),
                    (self.delete_image, self.action_delete, self.menu_anims[2]),
                )
            elif cont.just_pressed_button == pygame.BUTTON_MIDDLE:
                self.middle_selected = path

    def action_rename(self):
        self.modal_state = "rename"
        self.rename_music.original_path = self.app.menu_data
        self.rename_music.original_ref = self.playlist.filepaths_table[
            self.app.menu_data
        ]
        self.rename_music.entryline.text = self.rename_music.original_ref.stem
        self.rename_music.entryline.cursor = len(self.rename_music.entryline.text)
        self.app.close_menu()

    def action_forward(self):
        self.modal_state = "move"
        self.app.close_menu()

    def action_delete(self):
        btn = pygame.display.message_box(
            "Confirm deletion",
            "Are you sure you want to remove the music? The song won't be deleted from disk. This action cannot be undone.",
            "warn",
            None,
            ("Proceed", "Cancel"),
        )
        if btn == 1:
            self.app.close_menu()
            return
        try:
            if self.app.menu_data == self.app.music:
                self.app.end_music()
            path = self.app.menu_data
            self.playlist.remove(path)
        except Exception:
            pass
        self.app.close_menu()

    def start_playing(self, path, idx):
        self.app.play_from_playlist(self.playlist, path, idx)

    def stop_searching(self):
        self.search_active = False
        self.search_entryline.text = ""

    def event(self, event):
        modal_exit = False
        if self.modal_state == "add":
            modal_exit = self.add_music.event(event)
        elif self.modal_state == "move":
            modal_exit = self.move_music.event(event)
        elif self.modal_state == "cover":
            modal_exit = self.change_cover.event(event)
        elif self.modal_state == "rename":
            modal_exit = self.rename_music.event(event)
        if (
            self.search_active
            and self.app.can_interact()
            and self.modal_state == "none"
        ):
            self.search_entryline.event(event)
        if event.type == pygame.MOUSEBUTTONUP and event.button == pygame.BUTTON_MIDDLE:
            self.middle_selected = None
        if (
            event.type == pygame.MOUSEWHEEL
            and self.modal_state == "none"
            and self.app.modal_state == "none"
        ):
            if self.middle_selected is not None:
                idx = self.playlist.filepaths.index(self.middle_selected)
                inc = -int(event.y)
                new_idx = idx + inc
                if new_idx < 0:
                    new_idx = 0
                if new_idx >= len(self.playlist.filepaths):
                    new_idx = len(self.playlist.filepaths) - 1
                self.playlist.filepaths.remove(self.middle_selected)
                self.playlist.filepaths.insert(new_idx, self.middle_selected)
            else:
                self.scroll.scroll(0, -(event.y * 40) * self.app.ui_mult)
                self.scrollbar.scroll_moved()
        if not modal_exit and (
            event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
        ):
            if self.search_active:
                self.stop_searching()
            else:
                self.back()
