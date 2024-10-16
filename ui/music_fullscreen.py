import mili
import pygame
import mili._core
from ui.common import *


class MusicFullscreenUI(UIComponent):
    def init(self):
        self.anims = [animation(-5) for i in range(2)]
        self.cache = mili.ImageCache()
        self.music_cache = mili.ImageCache()
        self.fullscreenclose_image = load_icon("fullscreenclose")

    def ui(self):
        self.mili.id_checkpoint(3000 + 100)
        if self.app.music is None:
            self.close()
            return
        with self.mili.begin(
            ((0, 0), self.app.window.size),
            {"ignore_grid": True} | mili.PADLESS,
        ):
            self.mili.image(
                SURF, {"fill": True, "fill_color": (0, 0, 0, 255), "cache": self.cache}
            )

            cover = self.app.music_cover_image
            if self.app.music.cover is not None:
                cover = self.app.music.cover
            if (
                self.app.music_controls.music_videoclip_cover is not None
                and self.app.focused
            ):
                cover = self.app.music_controls.music_videoclip_cover
            if cover is None:
                self.close()
            else:
                self.mili.image_element(
                    cover,
                    {"cache": self.music_cache} | mili.PADLESS,
                    (
                        0,
                        0,
                        0,
                        self.app.window.size[1]
                        - self.app.music_controls.cont_height
                        - self.app.tbarh,
                    ),
                    {"fillx": True},
                )

            self.ui_overlay_btn(
                self.anims[0],
                self.close,
                self.fullscreenclose_image,
                tooltip="Disable fullscreen"
                if self.app.music_controls.super_fullscreen
                else "Minimize",
            )

    def close(self):
        if self.app.music_controls.super_fullscreen:
            self.app.music_controls.super_fullscreen = False
            return
        self.app.modal_state = "none"

    def event(self, event):
        if self.app.listening_key:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return True
        return False
