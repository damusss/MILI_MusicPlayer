import mili
import pygame
import pathlib
import tkinter.filedialog as filedialog
from ui.common import *


class AddMusicUI(UIComponent):
    def init(self):
        self.anim_close = animation(-5)
        self.anim_create = animation(-3)
        self.anim_upload = animation(-3)
        self.selected_files = None
        self.cache = mili.ImageCache()

        self.confirm_image = load_icon("confirm")
        self.upload_image = load_icon("uploadf")

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
        self.mili.text_element("Add Music", {"size": self.mult(26)}, None, mili.CENTER)
        if self.selected_files is None:
            self.mili.text_element(
                "No file selected",
                {
                    "color": (150,) * 3,
                    "size": self.mult(18),
                },
                None,
                {"align": "center"},
            )
        else:
            with self.mili.begin(
                None, {"resizex": True, "resizey": True, "align": "center"}
            ):
                self.ui_selected_paths()
        with self.mili.begin(
            None,
            {
                "resizex": True,
                "resizey": True,
                "clip_draw": False,
                "axis": "x",
                "align": "center",
            },
        ):
            self.app.ui_image_btn(
                self.upload_image,
                self.action_music_from_dialog,
                self.anim_upload,
                br="30",
            )
            self.app.ui_image_btn(
                self.confirm_image, self.confirm_add, self.anim_create
            )
        self.ui_warning()

    def ui_warning(self):
        self.mili.text_element(
            "Adding might take some time if MP4 files are chosen",
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

    def ui_selected_paths(self):
        for i, path in enumerate(self.selected_files):
            self.mili.text_element(
                f"{path}",
                {
                    "color": (255,) * 3,
                    "size": self.mult(20),
                },
                None,
                {"align": "center"},
            )
            if i >= 5:
                if len(self.selected_files) - i - 1 > 0:
                    self.mili.text_element(
                        f"... and {len(self.selected_files)-i-1} more",
                        {
                            "color": (255,) * 3,
                            "size": self.mult(20),
                        },
                        None,
                        {"align": "center"},
                    )
                break

    def action_music_from_dialog(self):
        paths = filedialog.askopenfilenames()
        paths = [pathlib.Path(path) for path in paths]
        paths = [file for file in paths if (file).suffix[1:].lower() in FORMATS]
        self.selected_files = paths

    def confirm_add(self):
        if self.selected_files is None:
            pygame.display.message_box(
                "No file selected",
                "Select one ore more valid files to add them",
                "error",
                None,
                ("Understood",),
            )
            return
        for path in self.selected_files:
            self.app.playlist_viewer.playlist.load_music(
                path, self.app.playlist_viewer.playlist.filepaths
            )
        self.close()

    def close(self):
        self.selected_files = None
        self.app.playlist_viewer.modal_state = "none"

    def event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return True
        return False
