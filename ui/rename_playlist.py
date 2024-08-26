import os
import mili
import pygame
import pathlib
from ui.common import *
from ui.entryline import UIEntryline


class RenamePlaylistUI(UIComponent):
    def init(self):
        self.anim_close = animation(-5)
        self.anim_create = animation(-3)
        self.entryline = UIEntryline("Enter name...")
        self.cache = mili.ImageCache()

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
                    "resizey": True,
                    "align": "center",
                    "offset": (0, -self.app.tbarh),
                },
            ):
                self.mili.rect({"color": (MODAL_CV,) * 3, "border_radius": "5"})

                self.ui_modal_content()

            self.app.ui_overlay_btn(
                self.anim_close,
                self.close,
                self.app.close_image,
            )

    def ui_modal_content(self):
        self.mili.text_element(
            "Rename Playlist", {"size": self.mult(26)}, None, mili.CENTER
        )
        self.entryline.update()
        self.entryline.ui(
            self.mili,
            pygame.Rect(
                0,
                0,
                mili.percentage(80, self.app.window.size[0] / 1.35),
                self.mult(35),
            ),
            {"align": "center"},
            self.mult,
        )
        self.app.ui_image_btn(
            self.app.confirm_image, self.action_confirm, self.anim_create
        )
        self.mili.text_element(
            "Renaming might take some time if MP4 files were present",
            {
                "size": self.mult(16),
                "color": (150,) * 3,
                "growx": False,
                "wraplen": mili.percentage(70, self.app.window.size[0]),
                "slow_grow": True,
            },
            None,
            {"fillx": True},
        )

    def action_confirm(self):
        if not self.entryline.text.strip() or self.entryline.text[-1] == ".":
            pygame.display.message_box(
                "Invalid name",
                "Enter a valid name to rename the playlist. A name must be a valid folder name (cannot end with '.', must be non empty)",
                "error",
                None,
                ("Understood",),
            )
            return
        name = self.entryline.text.strip()
        if name == self.app.menu_data.name:
            pygame.display.message_box(
                "Invalid name",
                "Cannot change name to the same name.",
                "error",
                None,
                ("Understood",),
            )
            return
        for playlist in self.app.playlists:
            if name == playlist.name:
                pygame.display.message_box(
                    "Invalid name",
                    "A playlist already exists with the same name.",
                    "error",
                    None,
                    ("Understood",),
                )
                return
        self.final_rename(name)
        self.close()

    def final_rename(self, name):
        old_name = self.app.menu_data.name
        for file in os.listdir("data/mp3_from_mp4"):
            if file.startswith(old_name):
                old_path = pathlib.Path(f"data/mp3_from_mp4/{file}").resolve()
                new_path = pathlib.Path(
                    f"data/mp3_from_mp4/{name}{file.removeprefix(old_name)}"
                )
                if not os.path.exists(new_path):
                    os.rename(old_path, new_path)
        for file in os.listdir("data/music_covers"):
            if file.startswith(old_name):
                old_path = pathlib.Path(f"data/music_covers/{file}").resolve()
                new_path = pathlib.Path(
                    f"data/music_covers/{name}{file.removeprefix(old_name)}"
                )
                if not os.path.exists(new_path):
                    os.rename(old_path, new_path)
        if os.path.exists(f"data/covers/{old_name}.png"):
            if not os.path.exists(f"data/covers/{name}.png"):
                os.rename(f"data/covers/{old_name}.png", f"data/covers/{name}.png")
        self.app.menu_data.__init__(
            name, list(self.app.menu_data.realpaths), self.app.loading_image
        )

    def close(self):
        self.entryline.text = ""
        self.app.list_viewer.modal_state = "none"

    def event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
        self.entryline.event(event)
