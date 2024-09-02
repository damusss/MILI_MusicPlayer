import mili
import pygame
from ui.common import *
from ui.data import MusicData, Playlist


class MoveMusicUI(UIComponent):
    def init(self):
        self.anim_close = animation(-5)
        self.cache = mili.ImageCache()
        self.scroll = mili.Scroll()
        self.music: MusicData = None

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
                    "filly": "65",
                    "align": "center",
                    "offset": (0, -self.app.tbarh),
                },
            ):
                self.mili.rect({"color": (MODAL_CV,) * 3, "border_radius": "5"})

                self.mili.text_element(
                    "Move Music", {"size": self.mult(26)}, None, mili.CENTER
                )
                self.mili.text_element(
                    "Select the playlist you want to move the music to"
                    if len(self.app.playlists) > 1
                    else "Not enough playlists to move",
                    {
                        "color": (150,) * 3,
                        "size": self.mult(18),
                    },
                    None,
                    {"align": "center"},
                )
                self.ui_playlists()

            self.app.ui_overlay_btn(
                self.anim_close,
                self.close,
                self.app.close_image,
            )

    def ui_playlists(self):
        with self.mili.begin(
            None, {"fillx": True, "filly": True}, get_data=True
        ) as cont:
            self.scroll.update(cont)
            for playlist in self.app.playlists:
                if playlist is self.app.playlist_viewer.playlist:
                    continue

                with self.mili.begin(
                    (0, 0, 0, self.mult(60)),
                    {
                        "fillx": True,
                        "anchor": "first",
                        "axis": "x",
                        "offset": self.scroll.get_offset(),
                    },
                ) as it:
                    self.mili.rect({"color": (cond(self.app, it, *LISTM_CV),) * 3})
                    cover = self.app.playlist_cover
                    if playlist.cover is not None:
                        cover = playlist.cover
                    if cover is not None:
                        self.mili.image_element(
                            cover,
                            {"cache": mili.ImageCache.get_next_cache()},
                            (0, 0, self.mult(50), self.mult(50)),
                            {"align": "center", "blocking": False},
                        )
                    self.mili.text_element(
                        f"{playlist.name}",
                        {"align": "left", "size": self.mult(22)},
                        None,
                        {"align": "center", "blocking": False},
                    )
                    if it.left_just_released and self.app.can_interact():
                        self.move(playlist)

    def move(self, playlist: Playlist):
        if self.music == self.app.music:
            self.app.end_music()

        mp3path = f"data/mp3_from_mp4/{self.app.playlist_viewer.playlist.name}_{self.music.realstem}.mp3"
        newmp3path = f"data/mp3_from_mp4/{playlist.name}_{self.music.realstem}.mp3"
        if os.path.exists(mp3path):
            if not os.path.exists(newmp3path):
                os.rename(mp3path, newmp3path)

        coverpath = f"data/music_covers/{self.app.playlist_viewer.playlist.name}_{self.music.realstem}.png"
        if os.path.exists(coverpath):
            newcoverpath = (
                f"data/music_covers/{playlist.name}_{self.music.realstem}.png"
            )
            if not os.path.exists(newcoverpath):
                os.rename(coverpath, newcoverpath)

        self.app.playlist_viewer.playlist.remove(self.music.audiopath)
        playlist.load_music(self.music.realpath, self.app.loading_image)

        self.close()

    def close(self):
        self.app.playlist_viewer.modal_state = "none"

    def event(self, event):
        if self.app.listening_key:
            return False
        if event.type == pygame.MOUSEWHEEL:
            self.scroll.scroll(0, -(event.y * 40) * self.app.ui_mult)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return True
        return False
