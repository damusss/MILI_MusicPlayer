import mili
import pygame
import pathlib
from ui.common import *
from ui.entryline import UIEntryline
from ui.data import PlaylistGroup
import tkinter.filedialog as filedialog


class PlaylistAddUI(UIComponent):
    def init(self):
        self.anim_close = animation(-5)
        self.anim_create = animation(-3)
        self.anim_upload = animation(-3)
        self.selected_files = None
        self.entryline = UIEntryline("Enter name...", False)
        self.cache = mili.ImageCache()
        self.upload_image = load_icon("uploadf")
        self.create_type = "music"

    def ui(self):
        self.mili.id_checkpoint(3000)
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

                self.mili.text_element(
                    "Add", {"size": self.mult(26)}, None, mili.CENTER
                )
                self.ui_modal_content()

            self.ui_overlay_btn(
                self.anim_close,
                self.close,
                self.app.close_image,
            )

    def ui_modal_content(self):
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
                self.ui_section_btn(left_cont, "music", "Music")

            with self.mili.begin(
                (0, 0, row.rect.w / 2.01, 0),
                {"resizey": True, "padx": 0, "pady": 0},
            ) as right_cont:
                self.ui_section_btn(right_cont, "group", "Group")

        if self.create_type == "music":
            self.ui_add_music_content()
        else:
            self.ui_create_group_content()

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
        if self.app.can_interact():
            if cont.left_just_released:
                self.create_type = ctype
            if cont.hovered or cont.unhover_pressed:
                self.app.cursor_hover = True

    def ui_add_music_content(self):
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
            self.ui_image_btn(
                self.upload_image,
                self.action_music_from_dialog,
                self.anim_upload,
                br="30",
            )
            self.ui_image_btn(
                self.app.confirm_image, self.action_confirm_music, self.anim_create
            )
        self.ui_warning()

    def ui_create_group_content(self):
        self.entryline.update(self.app)
        self.entryline.ui(
            self.mili,
            pygame.Rect(
                0, 0, mili.percentage(80, self.app.window.size[0] / 1.35), self.mult(35)
            ),
            {"align": "center"},
            self.mult,
        )
        self.ui_image_btn(
            self.app.confirm_image, self.action_confirm_group, self.anim_create
        )

    def ui_warning(self):
        self.mili.text_element(
            "Adding might take some time if video files are chosen",
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
                    "size": self.mult(17),
                    "growx": False,
                    "wraplen": "100",
                    "slow_grow": True,
                },
                (0, 0, mili.percentage(70, self.app.window.size[0]), 0),
                {"align": "center"},
            )
            if i >= 3:
                if len(self.selected_files) - i - 1 > 0:
                    self.mili.text_element(
                        f"... and {len(self.selected_files)-i-1} more",
                        {
                            "color": (255,) * 3,
                            "size": self.mult(17),
                        },
                        None,
                        {"align": "center"},
                    )
                break

    def action_music_from_dialog(self):
        paths = filedialog.askopenfilenames()
        paths = [pathlib.Path(path) for path in paths]
        paths = [file for file in paths if (file).suffix[1:].lower() in FORMATS]
        if len(paths) < 0:
            self.selected_files = None
            return
        self.selected_files = paths

    def action_confirm_music(self):
        if self.selected_files is None:
            pygame.display.message_box(
                "No file selected",
                "Select one ore more valid files to add them.",
                "error",
                None,
                ("Understood",),
            )
            return
        for path in self.selected_files:
            self.app.playlist_viewer.playlist.load_music(path, self.app.loading_image)
        self.close()

    def action_confirm_group(self):
        name = self.entryline.text.strip()
        if not name:
            pygame.display.message_box(
                "Invalid name",
                "The group name must not be empty.",
                "error",
                None,
                ("Understood",),
            )
            return
        self.app.playlist_viewer.playlist.groups.append(
            PlaylistGroup(name, self.app.playlist_viewer.playlist, [], 0)
        )
        self.close()

    def close(self):
        self.selected_files = None
        self.app.playlist_viewer.modal_state = "none"
        self.create_type = "music"

    def event(self, event):
        if self.app.listening_key:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return True
        if Keybinds.check("confirm", event, ignore_input=self.create_type == "group"):
            if self.create_type == "music":
                self.action_confirm_music()
            else:
                self.action_confirm_group()
        if self.create_type == "group":
            self.entryline.event(event)
        return False
