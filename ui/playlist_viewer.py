import mili
import pygame
from ui.common import *
from ui.data import Playlist, MusicData
from ui.add_music import AddMusicUI
from ui.entryline import UIEntryline
from ui.move_music import MoveMusicUI
from ui.change_cover import ChangeCoverUI
from ui.rename_music import RenameMusicUI


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
        self.big_cover = False
        self.big_cover_time = 0

        self.add_music = AddMusicUI(self.app)
        self.change_cover = ChangeCoverUI(self.app)
        self.rename_music = RenameMusicUI(self.app)
        self.move_music = MoveMusicUI(self.app)

        self.scroll = mili.Scroll()
        self.scrollbar = mili.Scrollbar(self.scroll, 8, 3, 3, 0, "y")
        self.sbar_size = self.scrollbar.short_size
        self.cover_cache = mili.ImageCache()
        self.bigcover_cache = mili.ImageCache()
        self.black_cache = mili.ImageCache()

        self.change_cover_image = load_icon("cover")
        self.forward_image = load_icon("forward")
        self.search_image = load_icon("search")
        self.searchoff_image = load_icon("searchoff")
        self.backspace_image = load_icon("backspace")

    def sort_searched_songs(self):
        scores = {}
        rawsearch = self.search_entryline.text.strip()
        search = rawsearch.lower()
        for i, apath in enumerate(
            [music.audiopath for music in self.playlist.musiclist]
        ):
            path = self.playlist.musictable[apath].realpath
            score = 0
            rawname = str(path.stem)
            name = rawname.lower()
            if rawsearch in rawname:
                score += 100
            if search in name:
                score += 80
            words = rawsearch.split(" ")
            for rawword in words:
                if rawword in rawname:
                    score += 20
                if rawword.lower() in name:
                    score += 10
                if rawword.lower() in name.replace(" ", ""):
                    score += 5
            scores[apath] = (score, i)
        return [
            (v[1][1], v[0])
            for v in sorted(list(scores.items()), key=lambda x: x[1][0], reverse=True)
        ]

    def enter(self, playlist):
        self.playlist = playlist
        self.app.change_state("playlist")

    def ui_top_buttons(self):
        self.ui_overlay_top_btn(self.anim_back, self.back, self.app.back_image, "left")

    def ui(self):
        if self.modal_state == "none" and self.app.modal_state == "none":
            handle_arrow_scroll(self.app.delta_time, self.scroll, self.scrollbar)

        if self.search_active:
            self.search_entryline.update(self.app)
        self.scrollbar.short_size = self.mult(8)
        if self.playlist is None:
            self.back()

        big_cover = self.ui_title()
        if big_cover and not self.big_cover:
            self.big_cover = True
            self.big_cover_time = pygame.time.get_ticks()
        if not big_cover:
            self.big_cover = False
        self.ui_container()

        if self.modal_state == "none" and self.app.modal_state == "none":
            self.ui_overlay_btn(
                self.anim_add_music,
                self.action_add_music,
                self.app.playlistadd_image,
                "top",
            )
            self.ui_overlay_btn(
                self.anim_cover, self.action_cover, self.change_cover_image, "supertop"
            )
            self.ui_overlay_btn(
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

        if (
            big_cover
            and pygame.time.get_ticks() - self.big_cover_time >= BIG_COVER_COOLDOWN
        ):
            self.ui_big_cover()

    def ui_container(self):
        with self.mili.begin(
            (0, 0, self.app.window.size[0], 0), {"filly": True}, get_data=True
        ) as scroll_cont:
            any_pending = any(music.pending for music in self.playlist.musiclist)
            if self.search_active:
                paths = self.sort_searched_songs()
            else:
                paths = list(
                    enumerate([music.audiopath for music in self.playlist.musiclist])
                )
            if len(paths) > 0:
                self.scroll.update(scroll_cont)
                self.scrollbar.short_size = self.mult(self.sbar_size)
                self.scrollbar.update(scroll_cont)

                self.ui_scrollbar()

                drawn_musics = 0
                for posi, (musici, path) in enumerate(paths):
                    drawn_musics += 1
                    music = self.playlist.musictable[path]
                    if music.check():
                        continue
                    if music.pending:
                        self.mili.text_element(
                            f"'{parse_music_stem(self.app, music.realstem)}' is being converted...",
                            {
                                "size": self.mult(16),
                                "color": (170,) * 3,
                                "growx": False,
                                "slow_grow": True,
                                "wraplen": self.app.window.size[0] * 0.95,
                            },
                            None,
                            {"offset": self.scroll.get_offset(), "fillx": True},
                        )
                        continue
                    if self.ui_music(music, musici, posi) and not any_pending:
                        break

                if drawn_musics < len(paths) and not any_pending:
                    to_draw = len(paths) - drawn_musics
                    self.mili.element((0, 0, 10, (self.mult(80) + 3) * to_draw))

                self.mili.text_element(
                    f"{len(self.playlist.musiclist)} track{
                        "s" if len(self.playlist.musiclist) > 1 else ""}",
                    {"size": self.mult(19), "color": (170,) * 3},
                    None,
                    {"offset": self.scroll.get_offset()},
                )

            else:
                self.mili.text_element(
                    "No music matches your search"
                    if self.search_active
                    else "No music",
                    {"size": self.mult(20), "color": (200,) * 3},
                    None,
                    {"align": "center"},
                )

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
                    if (
                        handle.hovered or handle.unhover_pressed
                    ) and self.app.can_interact():
                        self.app.cursor_hover = True

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
                        self.app.cursor_hover = True
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
                if self.app.can_interact():
                    if it.left_just_released:
                        self.search_entryline.text = ""
                        self.search_entryline.cursor = 0
                    if it.hovered or it.unhover_pressed:
                        self.app.cursor_hover = True

    def ui_big_cover(self):
        self.mili.image_element(
            SURF,
            {"fill": True, "fill_color": (0, 0, 0, 200), "cache": self.black_cache},
            ((0, 0), self.app.window.size),
            {"ignore_grid": True, "parent_id": 0, "z": 99999, "blocking": False},
        )
        size = mili.percentage(90, min(self.app.window.size))
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

    def ui_music(self, music: MusicData, idx, posi):
        predicted_pos = posi * (self.mult(80) + 3) + self.scroll.get_offset()[1]
        if predicted_pos > self.app.window.size[1]:
            return True
        with self.mili.begin(
            (0, 0, 0, self.mult(80)),
            {
                "fillx": "100" if not self.scrollbar.needed else "98",
                "offset": (
                    self.scrollbar.needed * -self.mult(self.sbar_size / 2),
                    self.scroll.get_offset()[1],
                ),
                "padx": self.mult(8),
                "axis": "x",
                "align": "center",
                "anchor": "first",
            },
        ) as cont:
            self.ui_music_bg(music.audiopath, cont)
            imagesize = 0
            cover = music.cover_or(self.app.music_cover_image)
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
                parse_music_stem(self.app, music.realstem),
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
            if self.app.can_interact():
                if cont.hovered or cont.unhover_pressed:
                    self.app.cursor_hover = True
                if cont.left_just_released:
                    self.action_start_playing(music, idx)
                elif cont.just_released_button == pygame.BUTTON_RIGHT:
                    self.app.open_menu(
                        music,
                        (self.app.rename_image, self.action_rename, self.menu_anims[0]),
                        (self.forward_image, self.action_forward, self.menu_anims[1]),
                        (self.app.delete_image, self.action_delete, self.menu_anims[2]),
                    )
                elif cont.just_pressed_button == pygame.BUTTON_MIDDLE:
                    self.middle_selected = music
        return False

    def ui_music_bg(self, path, cont):
        if self.app.bg_effect:
            self.mili.image(
                SURF,
                {
                    "fill": True,
                    "fill_color": (
                        *(
                            (
                                MUSIC_CV[1]
                                if self.app.music == path
                                else cond(self.app, cont, *MUSIC_CV),
                            )
                            * 3
                        ),
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
                        MUSIC_CV[1]
                        if self.app.music == path
                        else cond(self.app, cont, *MUSIC_CV),
                    )
                    * 3,
                    "border_radius": 0,
                }
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

    def action_rename(self):
        self.modal_state = "rename"
        self.rename_music.music = self.app.menu_data
        self.rename_music.entryline.text = self.rename_music.music.realstem
        self.rename_music.entryline.cursor = len(self.rename_music.entryline.text)
        self.app.close_menu()

    def action_forward(self):
        self.modal_state = "move"
        self.move_music.music = self.app.menu_data
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
            path = self.app.menu_data.audiopath
            self.playlist.remove(path)
        except Exception:
            pass
        self.app.close_menu()

    def action_start_playing(self, music, idx):
        self.app.play_music(music, idx)

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
                idx = self.playlist.musiclist.index(self.middle_selected)
                mult = 1
                if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                    mult = 5
                inc = -int(event.y) * mult
                new_idx = idx + inc
                if new_idx < 0:
                    new_idx = 0
                if new_idx >= len(self.playlist.musiclist):
                    new_idx = len(self.playlist.musiclist) - 1
                self.playlist.musiclist.remove(self.middle_selected)
                self.playlist.musiclist.insert(new_idx, self.middle_selected)
                if self.middle_selected is self.app.music:
                    self.app.music_index = new_idx
            else:
                handle_wheel_scroll(event, self.app, self.scroll, self.scrollbar)

        self.shortcuts_event(event, modal_exit)

    def shortcuts_event(self, event, modal_exit):
        if self.app.listening_key or not self.app.can_interact():
            return
        if event.type == pygame.KEYDOWN:
            if not modal_exit and event.key == pygame.K_ESCAPE:
                if self.search_active:
                    self.stop_searching()
                else:
                    self.back()
            elif Keybinds.check("toggle_search", event):
                if self.search_active:
                    self.stop_searching()
                else:
                    self.action_search()
            elif Keybinds.check("change_cover", event):
                if self.modal_state == "cover":
                    self.change_cover.close()
                else:
                    self.action_cover()
