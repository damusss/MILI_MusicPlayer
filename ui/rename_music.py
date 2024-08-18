import mili
import pygame
import os
import pathlib
from ui.common import *


class RenameMusicUI(UIComponent):
    def init(self):
        self.anim_close = animation(-5)
        self.anim_create = animation(-3)
        self.entryline = UIEntryline("Enter name (no filetype)...")
        self.cache = mili.ImageCache()
        self.confirm_image = load_icon("confirm")
        self.original_path: pathlib.Path = None
        self.original_ref: pathlib.Path = None

    def ui(self):
        with self.mili.begin(
            ((0, 0), self.app.window.size), {"ignore_grid": True} | mili.CENTER
        ):
            self.mili.image(
                SURF, {"fill": True, "fill_color": (0, 0, 0, 200), "cache": self.cache}
            )

            with self.mili.begin(
                (0, 0, 0, 0), {"fillx": "80", "resizey": True, "align": "center"}
            ):
                self.mili.rect({"color": (MODAL_CV,) * 3, "border_radius": "5"})

                self.ui_modal_content()

            self.app.ui_overlay_btn(
                self.anim_close,
                self.close,
                self.app.close_image,  # ([("-20", "-20"), ("20", "20")], [("-20", "20"), ("20", "-20")]),
            )

    def ui_modal_content(self):
        self.mili.text_element(
            "Rename Music", {"size": self.mult(26)}, None, mili.CENTER
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
        self.app.ui_image_btn(self.confirm_image, self.confirm_rename, self.anim_create)
        self.mili.text_element(
            "Renaming will modify the file on disk. Do not include the file type.",
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

    def confirm_rename(self):
        new_name = self.entryline.text.strip()
        if not new_name or self.entryline.text[-1] == ".":
            pygame.display.message_box(
                "Invalid name",
                "Enter a valid name to rename the music. A name must be a valid file name (cannot end with '.', must be non empty)",
                "error",
                None,
                ("Understood",),
            )
            return
        if new_name == self.original_ref.stem:
            pygame.display.message_box(
                "Invalid name",
                "Cannot change name to the same name.",
                "error",
                None,
                ("Understood",),
            )
            return
        new_path = self.original_ref.parent / f"{new_name}{self.original_ref.suffix}"
        if os.path.exists(new_path):
            pygame.display.message_box(
                "File already exists",
                f"A file with the same name already exists in '{self.original_ref.parent}'.",
                "error",
                None,
                ("Understood",),
            )
            return
        self.final_rename(new_path, new_name)
        self.close()

    def final_rename(self, new_path, new_stem):
        if self.original_path == self.app.music:
            self.app.end_music()

        try:
            os.rename(self.original_ref, new_path)
        except Exception as e:
            pygame.display.message_box(
                "Operation failed",
                f"Failed to rename file due to OS error: '{e}'",
                "error",
                None,
                ("Understood",),
            )
            self.close()
            return

        mp3path = f"data/mp3_from_mp4/{self.app.playlist_viewer.playlist.name}_{self.original_ref.stem}.mp3"
        newmp3path = (
            f"data/mp3_from_mp4/{self.app.playlist_viewer.playlist.name}_{new_stem}.mp3"
        )
        if os.path.exists(mp3path):
            if not os.path.exists(newmp3path):
                os.rename(mp3path, newmp3path)

        coverpath = f"data/music_covers/{self.app.playlist_viewer.playlist.name}_{self.original_ref.stem}.png"
        if os.path.exists(coverpath):
            newcoverpath = f"data/music_covers/{self.app.playlist_viewer.playlist.name}_{new_stem}.png"
            if not os.path.exists(newcoverpath):
                os.rename(coverpath, newcoverpath)

        idx = self.app.playlist_viewer.playlist.filepaths.index(self.original_path)
        self.app.playlist_viewer.playlist.remove(self.original_path)
        self.app.playlist_viewer.playlist.load_music(
            new_path, self.app.playlist_viewer.playlist.filepaths
        )
        for pt in [new_path.resolve(), pathlib.Path(newmp3path).resolve()]:
            if pt in self.app.playlist_viewer.playlist.filepaths:
                self.app.playlist_viewer.playlist.filepaths.remove(pt)
                self.app.playlist_viewer.playlist.filepaths.insert(idx, pt)
                break

        self.close()

    def close(self):
        self.entryline.text = ""
        self.original_path = None
        self.original_ref = None
        self.app.playlist_viewer.modal_state = "none"

    def event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
        self.entryline.event(event)
