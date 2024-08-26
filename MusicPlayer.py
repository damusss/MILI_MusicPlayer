import sys
import mili
import pygame
import pathlib
import faulthandler
from ui.common import *
import moviepy.editor as moviepy
from ui.history import HistoryUI
from ui.settings import SettingsUI
from ui.list_viewer import ListViewerUI
from health_check import main as health_check
from ui.music_controls import MusicControlsUI
from ui.playlist_viewer import PlaylistViewerUI

faulthandler.enable()


if "win" in sys.platform or os.name == "nt":
    import ctypes

    myappid = "damusss.mili_musicplayer.1.0"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


class MusicPlayerApp(mili.GenericApp):
    def __init__(self):
        pygame.mixer.pre_init(buffer=2048)
        pygame.mixer.init(buffer=2048)
        pygame.font.init()
        super().__init__(
            pygame.Window(
                "Music Player",
                (PREFERRED_SIZES[0], PREFERRED_SIZES[1]),
                resizable=True,
            )
        )
        self.window.minimum_size = (200, 300)
        self.start_style = mili.PADLESS
        self.user_framerate = 60

        self.playlist_viewer = PlaylistViewerUI(self)
        self.list_viewer = ListViewerUI(self)
        self.music_controls = MusicControlsUI(self)
        self.settings = SettingsUI(self)
        self.history = HistoryUI(self)

        self.view_state = "list"
        self.modal_state = "none"
        self.playlists: list[Playlist] = []
        self.history_data: list[HistoryData] = []
        self.volume = 1
        self.loops = True
        self.shuffle = False
        self.vol_before_mute = 1
        self.ui_mult = 1
        self.focused = True
        self.bg_effect_image = None
        self.bg_black_image = None
        self.bg_effect = False
        self.make_bg_image()
        self.bg_cache = mili.ImageCache()
        self.anim_quit = animation(-3)
        self.anim_settings = animation(-5)
        self.menu_open = False
        self.menu_data: Playlist | pathlib.Path = None
        self.menu_buttons = None
        self.menu_pos = None

        self.music: MusicData = None
        self.music_paused = False
        self.music_index = -1
        self.music_play_time = 0
        self.music_play_offset = 0
        self.music_loops = False
        self.music_videoclip = None

        self.init_data_folder_check()
        self.init_load_settings()
        self.init_loading_screen()
        self.init_load_icons()
        self.init_load_data()
        self.init_mili_settings()
        self.init_sld2()
        self.init_try_set_icon_mac()
        health_check()

    def init_load_icons(self):
        self.close_image = load_icon("close")
        self.playlistadd_image = load_icon("playlist_add")
        self.music_cover_image = load_icon("music")
        self.playlist_cover = load_icon("playlist")
        self.settings_image = load_icon("settings")
        self.loading_image = load_icon("loading")
        self.confirm_image = load_icon("confirm")
        self.back_image = load_icon("back")
        self.delete_image = load_icon("delete")
        self.rename_image = load_icon("edit")
        self.loopon_image = load_icon("loopon")
        self.loopoff_image = load_icon("loopoff")
        self.window.set_icon(self.playlist_cover)

    def init_load_data(self):
        make_data_folders("mp3_from_mp4", "covers", "music_covers")
        playlist_data = load_json("data/playlists.json", [])
        write_json("data/playlists_backup.json", playlist_data)
        history_data = load_json("data/history.json", [])

        for pdata in playlist_data:
            name = pdata["name"]
            paths = [pathlib.Path(path) for path in pdata["paths"]]
            self.playlists.append(Playlist(name, paths, self.loading_image))

        for hdata in history_data:
            obj = HistoryData.load_from_data(hdata, self)
            if obj is not None:
                self.history_data.append(obj)

    def init_sld2(self):
        try:
            import sdl2

            self.sdl2 = sdl2
        except (ModuleNotFoundError, ImportError):
            self.sdl2 = None
            print(
                "\nWARNING: PySDL2 not installed. Miniplayer hover feature is disabled"
            )

    def init_mili_settings(self):
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
        mili.ImageCache.preallocate_caches(2000)

    def init_load_settings(self):
        try:
            data = load_json(
                "data/settings.json",
                {"volume": 1, "loops": True, "shuffle": False, "fps": 60},
            )
            self.volume = data["volume"]
            self.loops = data["loops"]
            self.shuffle = data["shuffle"]
            self.user_framerate = data["fps"]
        except Exception:
            pass
        self.target_framerate = self.user_framerate

    def init_data_folder_check(self):
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

    def init_loading_screen(self):
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

    def init_try_set_icon_mac(self):
        if not (os.name == "posix" and sys.platform == "darwin"):
            return
        try:
            from AppKit import NSApplication, NSImage
            from Foundation import NSURL

            app = NSApplication.sharedApplication()
            icon_image = NSImage.alloc().initByReferencingFile_(
                "data/icons/playlist.png"
            )
            app.setApplicationIconImage_(icon_image)

        except ImportError:
            if not os.path.exists("ignore-pyobjc-dep.txt"):
                btn = pygame.display.message_box(
                    "Could not set taskbar icon",
                    "The module 'pyobjc' is required to set the taskbar icon on MacOS. Please make sure the module is "
                    "installed the next time you run the application. Create a file named 'ignore-pyobjc-dep.txt' "
                    "to suppress this warning.",
                    "warn",
                    None,
                    ("Understood", "Create ignore file"),
                )
                if btn == 1:
                    with open("ignore-pyobjc-dep.txt", "w") as file:
                        file.write("")
        except Exception:
            pass

    def get_music_pos(self):
        return (
            self.music_play_offset
            + (pygame.time.get_ticks() - self.music_play_time) / 1000
        )

    def add_to_history(self):
        pos = self.get_music_pos()
        data = HistoryData(self.music, pos, self.music.duration)
        for olddata in self.history_data.copy():
            if olddata.music is self.music:
                self.history_data.remove(olddata)
        self.history_data.append(data)
        if len(self.history_data) > HISTORY_LEN:
            self.history_data.pop(0)

    def play_music(self, music, idx):
        if self.music is not None:
            self.add_to_history()
        self.music = music
        self.music_paused = False
        self.music_index = idx
        self.music_play_time = pygame.time.get_ticks()
        self.music_play_offset = 0
        if self.music.duration is NotCached:
            self.music.cache_duration()

        self.music_videoclip = None
        if self.music.isvideo:
            try:
                self.music_videoclip = moviepy.VideoFileClip(str(self.music.realpath))
            except Exception:
                pass

        self.music_controls.offset = 0
        self.music_controls.offset_restart_time = pygame.time.get_ticks()
        self.music_controls.music_videoclip_cover = None
        self.music_controls.last_videoclip_cover = None

        pygame.mixer.music.load(self.music.audiopath)
        pygame.mixer.music.play(0)
        pygame.mixer.music.set_endevent(MUSIC_ENDEVENT)
        pygame.mixer.music.set_volume(self.volume)

    def end_music(self):
        if self.music is not None:
            self.add_to_history()
        self.music = None
        self.music_paused = False
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        if self.music_controls.minip.window is not None:
            self.music_controls.minip.close()
        if self.music_videoclip is not None:
            self.music_videoclip.close()
        self.music_videoclip = None

    def on_quit(self):
        if self.music is not None:
            self.add_to_history()
        playlist_data = [
            {
                "name": p.name,
                "paths": [str(m.realpath) for m in p.musiclist],
            }
            for p in self.playlists
        ]
        history_data = [history.get_save_data() for history in self.history_data]
        write_json("data/playlists.json", playlist_data)
        write_json("data/history.json", history_data)
        write_json(
            "data/settings.json",
            {
                "volume": self.volume,
                "loops": self.loops,
                "shuffle": self.shuffle,
                "fps": self.user_framerate,
            },
        )
        for playlist in self.playlists:
            if playlist.cover is not None:
                if not os.path.exists(f"data/covers/{playlist.name}.png"):
                    pygame.image.save(
                        playlist.cover, f"data/covers/{playlist.name}.png"
                    )

    def update(self):
        self.target_framerate = self.user_framerate
        if (
            not self.focused
            and (
                self.music_controls.music_videoclip_cover is None
                or self.music_paused
                or self.music is None
            )
            and (
                not self.music_controls.minip.focused
                or self.music_controls.minip.window is None
            )
        ):
            self.target_framerate = 10

        ratio = self.window.size[0] / self.window.size[1]
        if ratio < 0.45:
            self.window.size = (self.window.size[1] * 0.46, self.window.size[1])

        multx = self.window.size[0] / UI_SIZES[0]
        multy = self.window.size[1] / UI_SIZES[1]
        self.ui_mult = max(0.3, (multx * 0.1 + multy * 1) / 1.1)

        self.start_style = mili.PADLESS | {"spacing": int(self.ui_mult * 3)}
        mili.animation.update_all()

    def ui(self):
        self.mili.rect({"color": (BG_CV,) * 3, "border_radius": 0})
        self.ui_bg_effect()

        if self.view_state == "list":
            self.list_viewer.ui()
        elif self.view_state == "playlist":
            self.playlist_viewer.ui()

        if self.modal_state == "settings":
            self.settings.ui()
        if self.modal_state == "history":
            self.history.ui()

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

    def ui_bg_effect(self):
        if not self.bg_effect:
            return
        self.mili.image(self.bg_effect_image)
        self.mili.image(self.bg_black_image, {"cache": self.bg_cache})

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

    def open_settings(self):
        self.modal_state = "settings"

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

    def make_bg_image(self):
        self.bg_black_image = pygame.Surface(self.window.size, pygame.SRCALPHA)
        self.bg_effect_image = pygame.Surface(self.window.size, pygame.SRCALPHA)
        for i in range(self.bg_black_image.height):
            alpha = pygame.math.lerp(0, 255, i / (self.bg_black_image.height / 1.5))
            self.bg_black_image.fill(
                (0, 0, 0, alpha), (0, i, self.bg_black_image.width, 1)
            )

    def event(self, event):
        if event.type == pygame.WINDOWFOCUSGAINED and event.window == self.window:
            self.focused = True
        if event.type == pygame.WINDOWFOCUSLOST and event.window == self.window:
            self.focused = False
        if event.type == pygame.WINDOWRESIZED and event.window == self.window:
            self.make_bg_image()
        self.music_controls.event(event)
        if not self.can_interact():
            return
        if self.modal_state == "settings":
            if self.settings.event(event):
                return
        if self.modal_state == "history":
            if self.history.event(event):
                return
        if self.view_state == "list":
            self.list_viewer.event(event)
        elif self.view_state == "playlist":
            self.playlist_viewer.event(event)


if __name__ == "__main__":
    MusicPlayerApp().run()
