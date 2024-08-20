import pygame
import mili
import pathlib
from health_check import main as health_check
from ui.list_viewer import ListViewerUI
from ui.playlist_viewer import PlaylistViewerUI
from ui.music_controls import MusicControlsUI
from ui.settings import SettingsUI
from ui.common import *


class MusicPlayerApp(mili.GenericApp):
    def __init__(self):
        pygame.init()
        super().__init__(
            pygame.Window(
                "MILI Music Player",
                (PREFERRED_SIZES[0] - 50, PREFERRED_SIZES[1]),
                resizable=True,
            )
        )
        self.window.minimum_size = (200, 300)

        self.start_style = mili.PADLESS
        self.target_framerate = 120

        self.playlist_viewer = PlaylistViewerUI(self)
        self.list_viewer = ListViewerUI(self)
        self.music_controls = MusicControlsUI(self)
        self.settings = SettingsUI(self)

        self.view_state = "list"
        self.modal_state = "none"
        self.playlists: list[Playlist] = []
        self.music: pathlib.Path = None
        self.music_ref: pathlib.Path = None
        self.music_cover: pygame.Surface = None
        self.music_paused = False
        self.music_index = -1
        self.music_playlist: Playlist = None
        self.music_duration = None
        self.music_play_time = 0
        self.music_play_offset = 0
        self.music_loops = False

        self.volume = 1
        self.loops = True
        self.shuffle = False
        self.vol_before_mute = 1
        self.ui_mult = 1
        self.focused = True

        if not os.path.exists("data"):
            pygame.display.message_box(
                "Data folder not found",
                "Data folder not found. The folder is required to load icons and to store user data. "
                "If you moved the application, remember to move the data folder aswell. The application will now quit.",
                "error",
                None,
                ("Understood",),
            )
            pygame.quit()
            raise SystemExit

        try:
            data = load_json(
                "data/settings.json",
                {"volume": 1, "loops": True, "shuffle": self.shuffle},
            )
            self.volume = data["volume"]
            self.loops = data["loops"]
            self.shuffle = data["shuffle"]
        except Exception:
            pass

        screen = self.window.get_surface()
        screen.fill((BG_CV,) * 3)
        txt = pygame.font.Font("data/ytfont.ttf", 30).render(
            "Loading music and covers...",
            True,
            "white",
            wraplength=int(screen.width / 1.2),
        )
        screen.blit(txt, txt.get_rect(center=(screen.width / 2, screen.height / 2)))
        self.window.flip()

        global ERROR_COVER
        ERROR_COVER = None
        self.close_image = load_icon("close")
        self.playlistadd_image = load_icon("playlist_add")
        self.music_cover_image = load_icon("music")
        self.playlist_cover = load_icon("playlist")
        self.settings_image = load_icon("settings")

        make_data_folders("mp3_from_mp4", "covers", "music_covers")

        playlist_data = load_json("data/playlists.json", [])
        for pdata in playlist_data:
            name = pdata["name"]
            paths = [pathlib.Path(path) for path in pdata["paths"]]
            self.playlists.append(Playlist(name, paths))

        self.mili.default_styles(
            text={
                "sysfont": False,
                "name": "data/ytfont.ttf",
                "growx": True,
                "growy": True,
            },
            line={"color": (255,) * 3},
            circle={"antialias": True},
            image={"smoothscale": True},
        )
        mili.ImageCache.preallocate_caches(1000)
        self.anim_quit = animation(-3)
        self.anim_settings = animation(-5)
        self.menu_open = False
        self.menu_data: Playlist | pathlib.Path = None
        self.menu_buttons = None
        self.menu_pos = None

        health_check()

    def play_from_playlist(self, playlist: Playlist, path, idx):
        self.music = path
        self.music_ref = playlist.filepaths_table[path]
        self.music_cover = playlist.music_covers.get(path, self.music_cover_image)
        self.music_controls.offset = 0
        self.music_controls.offset_restart_time = pygame.time.get_ticks()
        self.music_paused = False
        self.music_index = idx
        self.music_playlist = playlist
        self.music_play_time = pygame.time.get_ticks()
        self.music_play_offset = 0
        if path not in playlist.musics_durations:
            playlist.cache_duration(path)
        self.music_duration = playlist.musics_durations[path]
        pygame.mixer.music.load(path)
        pygame.mixer.music.play(0)
        pygame.mixer.music.set_endevent(MUSIC_ENDEVENT)

    def end_music(self):
        self.music = None
        self.music_duration = None
        self.music_paused = False
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        if self.music_controls.minip.window is not None:
            self.music_controls.minip.close()

    def on_quit(self):
        playlist_data = [
            {
                "name": p.name,
                "paths": [str(p.filepaths_table[path]) for path in p.filepaths],
            }
            for p in self.playlists
        ]
        write_json("data/playlists.json", playlist_data)
        write_json(
            "data/settings.json",
            {"volume": self.volume, "loops": self.loops, "shuffle": self.shuffle},
        )
        for playlist in self.playlists:
            if playlist.cover is not None:
                if not os.path.exists(f"data/covers/{playlist.name}.png"):
                    pygame.image.save(
                        playlist.cover, f"data/covers/{playlist.name}.png"
                    )

    def ui(self):
        multx = self.window.size[0] / PREFERRED_SIZES[0]
        multy = self.window.size[1] / PREFERRED_SIZES[1]
        self.ui_mult = max(0.3, (multx * 0.1 + multy * 1) / 1.1)
        self.start_style = mili.PADLESS | {"spacing": int(self.ui_mult * 3)}

        mili.animation.update_all()
        self.mili.rect({"color": (BG_CV,) * 3, "border_radius": 0})

        if self.view_state == "list":
            self.list_viewer.ui()
        elif self.view_state == "playlist":
            self.playlist_viewer.ui()

        if self.modal_state == "settings":
            self.settings.ui()

        self.music_controls.ui()

        if self.menu_open:
            self.ui_menu()

        if (
            self.playlist_viewer.modal_state == "none"
            and self.list_viewer.modal_state == "none"
            and self.modal_state == "none"
        ):
            self.ui_overlay_btn(
                self.anim_settings, self.open_settings, self.settings_image, "bottom"
            )

        self.ui_overlay_top_btn(
            self.anim_quit,
            self.quit,
            self.close_image,  # ([("-20", "-20"), ("20", "20")], [("-20", "20"), ("20", "-20")]),
            "right",
        )

    def open_settings(self):
        self.modal_state = "settings"

    def ui_menu(self):
        with self.mili.begin(
            (self.menu_pos, (0, 0)),
            {
                "resizex": True,
                "resizey": True,
                "ignore_grid": True,
                "parent_id": 0,
                "axis": "x",
                "z": 9999,
                "padx": 7,
                "pady": 7,
            },
        ) as menu:
            self.mili.rect({"color": (MENU_CV[0],) * 3, "border_radius": "50"})
            self.mili.rect(
                {"color": (MENU_CV[1],) * 3, "border_radius": "50", "outline": 1}
            )
            for bimage, baction, banim in self.menu_buttons:
                self.ui_image_btn(bimage, baction, banim, 50)
            if not menu.absolute_hover and any(
                [btn is True for btn in pygame.mouse.get_pressed()]
            ):
                self.close_menu()

    def ui_overlay_btn(self, anim, on_action, line_points_or_image, side="bottom"):
        size = self.mult(55)
        offset = self.mult(8)
        if it := self.mili.element(
            pygame.Rect(0, 0, size, size).move_to(
                bottomright=(
                    self.window.size[0] - offset * 1.2,
                    self.window.size[1]
                    - offset
                    - self.music_controls.cont_height
                    - {
                        "bottom": 0,
                        "top": size + self.mult(5),
                        "supertop": size * 2 + offset,
                        "megatop": size * 3 + offset * 1.5,
                    }[side],
                )
            ),
            {"ignore_grid": True, "clip_draw": False},
        ):
            self.mili.circle(
                {"color": (cond(self, it, *OVERLAY_CV),) * 3, "border_radius": "50"}
                | mili.style.same(int(anim.value / 1.8), "padx", "pady")
            )
            if isinstance(line_points_or_image, pygame.Surface):
                self.mili.image(
                    line_points_or_image,
                    {"cache": mili.ImageCache.get_next_cache()}
                    | mili.style.same(self.mult(8 + anim.value / 1.8), "padx", "pady"),
                )
            else:
                self.mili.line(line_points_or_image[0], {"size": "5"})
                self.mili.line(line_points_or_image[1], {"size": "5"})
            if it.just_hovered and self.can_interact():
                anim.goto_b()
            elif it.just_unhovered:
                anim.goto_a()
            if it.left_just_released and self.can_interact():
                on_action()
                anim.goto_a()

    def ui_overlay_top_btn(self, anim, on_action, line_points_or_image, side):
        y = self.mili.text_size("Music Player", {"size": self.mult(35)}).y
        size = self.mult(40)
        offset = self.mult(10)
        if it := self.mili.element(
            pygame.Rect(0, 0, size, size).move_to(
                topleft=(
                    offset,
                    y / 2 - size / 2 + 5,
                )
            )
            if side == "left"
            else pygame.Rect(0, 0, size, size).move_to(
                topright=(
                    self.window.size[0]
                    - (offset if side == "right" else offset * 2 + size),
                    y / 2 - size / 2 + 5,
                )
            ),
            {"ignore_grid": True, "clip_draw": False, "z": 9999},
        ):
            self.mili.rect(
                {"color": (cond(self, it, *OVERLAY_CV),) * 3, "border_radius": 0}
                | mili.style.same(int(anim.value), "padx", "pady")
            )
            if isinstance(line_points_or_image, pygame.Surface):
                self.mili.image(
                    line_points_or_image,
                    {"cache": mili.ImageCache.get_next_cache(), "smoothscale": True}
                    | mili.style.same(self.mult(3 + anim.value), "padx", "pady"),
                )
            else:
                self.mili.line(line_points_or_image[0], {"size": "5"})
                self.mili.line(line_points_or_image[1], {"size": "5"})
            if it.just_hovered and self.can_interact():
                anim.goto_b()
            elif it.just_unhovered:
                anim.goto_a()
            if it.left_just_released and self.can_interact():
                on_action()
                anim.goto_a()

    def ui_image_btn(self, image, action, anim, size=62, br="50"):
        if it := self.mili.element(
            (0, 0, self.mult(size), self.mult(size)),
            {"align": "center", "clip_draw": False},
        ):
            (self.mili.rect if br != "50" else self.mili.circle)(
                {
                    "color": (cond(self, it, MODAL_CV, MODALB_CV[1], MODALB_CV[2]),)
                    * 3,
                    "border_radius": br,
                }
                | mili.style.same(
                    (anim.value if br != "50" else anim.value / 1.8), "padx", "pady"
                )
            )
            self.mili.image(
                image,
                mili.style.same(self.mult(3) + anim.value, "padx", "pady")
                | {"smoothscale": True},
            )
            if it.left_just_released and self.can_interact():
                action()
            if it.just_hovered and self.can_interact():
                anim.goto_b()
            if it.just_unhovered:
                anim.goto_a()

    def change_state(self, state):
        self.view_state = state
        self.close_menu()

    def close_menu(self):
        self.menu_open = False
        self.menu_buttons = None
        self.menu_pos = None

    def open_menu(self, data, *buttons):
        self.menu_open = True
        self.menu_data = data
        self.menu_buttons = buttons
        self.menu_pos = pygame.mouse.get_pos()

    def mult(self, size):
        return max(1, int(size * self.ui_mult))

    def can_interact(self):
        if self.music_controls.minip.window is None:
            return True
        return not self.music_controls.minip.focused and self.focused

    def event(self, event):
        if event.type == pygame.WINDOWFOCUSGAINED and event.window == self.window:
            self.focused = True
        if event.type == pygame.WINDOWFOCUSLOST and event.window == self.window:
            self.focused = False
        self.music_controls.event(event)
        if not self.can_interact():
            return
        if self.modal_state == "settings":
            if self.settings.event(event):
                return
        if self.view_state == "list":
            self.list_viewer.event(event)
        elif self.view_state == "playlist":
            self.playlist_viewer.event(event)


if __name__ == "__main__":
    MusicPlayerApp().run()
