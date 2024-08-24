import os
import mili
import pygame
import pathlib
from ui.common import *
import tkinter.filedialog as filedialog


class NewPlaylistUI(UIComponent):
    def init(self):
        self.anim_close = animation(-5)
        self.anim_create = animation(-3)
        self.anim_upload = animation(-3)
        self.entryline = UIEntryline("Enter name...")
        self.cache = mili.ImageCache()

        self.create_type = "empty"
        self.selected_folder = None

        self.confirm_image = load_icon("confirm")
        self.upload_image = load_icon("upload")

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
            "New Playlist", {"size": self.mult(26)}, None, mili.CENTER
        )
        with self.mili.begin(
            None,
            {"fillx": True, "resizey": True, "axis": "x", "anchor": "max_spacing"}
            | mili.PADLESS,
            get_data=True,
        ) as row:
            with self.mili.begin(
                (0, 0, row.rect.w / 2.01, 0),
                {"resizey": True, "padx": 0, "pady": 0},
                get_data=True,
            ) as left_cont:
                self.ui_section_btn(left_cont, "empty", "Empty")

            with self.mili.begin(
                (0, 0, row.rect.w / 2.01, 0),
                {"resizey": True, "padx": 0, "pady": 0},
            ) as right_cont:
                self.ui_section_btn(right_cont, "folder", "Load Folder")

        if self.create_type == "empty":
            self.ui_empty_playlist_modal()
        else:
            self.ui_folder_playlist_modal()

    def ui_section_btn(self, cont, ctype, txt):
        color = (255,) * 3 if self.create_type == ctype else (120,) * 3
        if self.mili.element(None, mili.CENTER | {"blocking": False}):
            if cont.hovered and self.app.can_interact():
                self.mili.rect({"color": (MODALB_CV[0],) * 3, "border_radius": "10"})
            self.mili.text(
                txt,
                {"size": self.mult(21), "color": color},
            )

        self.mili.line_element(
            [("-48", 0), ("48", 0)],
            {"color": color},
            (0, 0, 0, self.mult(20)),
            {"fillx": True, "blocking": False},
        )
        if cont.left_just_released and self.app.can_interact():
            self.create_type = ctype

    def ui_empty_playlist_modal(self):
        self.entryline.update()
        self.entryline.ui(
            self.mili,
            pygame.Rect(
                0, 0, mili.percentage(80, self.app.window.size[0] / 1.35), self.mult(35)
            ),
            {"align": "center"},
            self.mult,
        )
        self.app.ui_image_btn(
            self.confirm_image, self.action_create_empty, self.anim_create
        )

    def ui_folder_playlist_modal(self):
        self.mili.text_element(
            f"{self.selected_folder}" if self.selected_folder else "No folder selected",
            {
                "color": "white" if self.selected_folder else (150,) * 3,
                "size": self.mult(20) if self.selected_folder else self.mult(18),
            },
            None,
            {"align": "center"},
        )
        with self.mili.begin(
            None,
            {
                "resizex": True,
                "resizey": True,
                "axis": "x",
                "align": "center",
                "clip_draw": False,
            }
            | mili.PADLESS,
        ):
            self.app.ui_image_btn(
                self.upload_image,
                self.action_folder_from_dialog,
                self.anim_upload,
                br="30",
            )
            self.app.ui_image_btn(
                self.confirm_image, self.action_create_from_folder, self.anim_create
            )
        self.mili.text_element(
            "Creating might take some time if MP4 files are present",
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

    def action_folder_from_dialog(self):
        result = filedialog.askdirectory(mustexist=True)
        if result:
            self.selected_folder = result

    def action_create_empty(self):
        if not self.entryline.text.strip() or self.entryline.text[-1] == ".":
            pygame.display.message_box(
                "Invalid name",
                "Enter a valid name to create the playlist",
                "error",
                None,
                ("Understood",),
            )
            return
        name = self.entryline.text.strip()
        if not self.remove_duplicates(name):
            return
        self.app.playlists.append(Playlist(name, []))
        self.close()

    def action_create_from_folder(self):
        if self.selected_folder is None:
            pygame.display.message_box(
                "No folder selected",
                "Select a valid folder to create the playlist",
                "error",
                None,
                ("Understood",),
            )
            return
        if not os.path.exists(self.selected_folder):
            pygame.display.message_box(
                "Folder not found",
                "The selected folder doesn't exist",
                "error",
                None,
                ("Understood",),
            )
            self.selected_folder = None
            return
        path = pathlib.Path(self.selected_folder)
        name = path.name
        paths = [
            path / file
            for file in os.listdir(path)
            if (path / file).suffix[1:].lower() in FORMATS
        ]
        if not self.remove_duplicates(name):
            return
        playlist = Playlist(name, paths)
        self.app.playlists.append(playlist)
        self.close()

    def remove_duplicates(self, name):
        for p in self.app.playlists.copy():
            if p.name == name:
                btn = pygame.display.message_box(
                    "Duplicate playlist",
                    "A playlist with the same name already exists. Proceeding will override the virtual contents of the previous playlist.",
                    "warn",
                    None,
                    ("Proceed", "Cancel"),
                )
                if btn == 1:
                    return False
                self.app.playlists.remove(p)
        return True

    def close(self):
        self.app.list_viewer.modal_state = "none"
        self.selected_folder = None
        self.entryline.text = ""

    def event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
        if self.create_type == "empty":
            self.entryline.event(event)
