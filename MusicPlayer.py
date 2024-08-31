import sys
import mili
import time
import pygame
import pathlib
import faulthandler

pygame.mixer.pre_init(buffer=2048)

from ui.common import *
import moviepy.editor as moviepy
from ui.history import HistoryUI
from ui.settings import SettingsUI
from ui.list_viewer import ListViewerUI
from health_check import main as health_check
from ui.music_controls import MusicControlsUI
from ui.playlist_viewer import PlaylistViewerUI
from ui.discord_presence import DiscordPresence
from ui.data import HistoryData, MusicData, Playlist, ResizeHandle, NotCached

try:
    faulthandler.enable()
except RuntimeError:
    ...


if "win" in sys.platform or os.name == "nt":
    import ctypes

    myappid = "damusss.mili_musicplayer.1.0"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


class MusicPlayerApp(mili.GenericApp):
    def __init__(self):
        self.init_pygame()
        self.init_attributes()
        self.init_data_folder_check()
        self.init_load_icons()
        self.init_load_settings()
        self.init_loading_screen()
        self.init_load_data()
        self.init_mili_settings()
        self.init_sld2()
        self.init_try_set_icon_mac()
        self.make_bg_image()
        health_check()

    def init_pygame(self):
        pygame.mixer.init()
        pygame.font.init()
        super().__init__(
            pygame.Window(
                "Music Player",
                PREFERRED_SIZES,
                resizable=True,
                borderless=True,
            )
        )
        self.window.minimum_size = WIN_MIN_SIZE

    def init_attributes(self):
        # components
        self.playlist_viewer = PlaylistViewerUI(self)
        self.list_viewer = ListViewerUI(self)
        self.music_controls = MusicControlsUI(self)
        self.settings = SettingsUI(self)
        self.history = HistoryUI(self)
        self.discord_presence = DiscordPresence(self)
        # settings
        self.user_framerate = 60
        self.volume = 1
        self.loops = True
        self.shuffle = False
        self.custom_title = True
        # status
        self.start_style = mili.PADLESS | {"spacing": 0}
        self.start_time = time.time()
        self.vol_before_mute = 1
        self.view_state = "list"
        self.modal_state = "none"
        self.playlists: list[Playlist] = []
        self.history_data: list[HistoryData] = []
        self.before_maximize_data = None
        self.maximized = False
        self.focused = True
        self.ui_mult = 1
        # be effect/mili
        self.bg_effect_image = None
        self.bg_black_image = None
        self.bg_effect = False
        self.bg_cache = mili.ImageCache()
        self.anims = [animation(-3) for i in range(4)]
        self.anim_settings = animation(-5)
        # menu
        self.menu_open = False
        self.menu_data: Playlist | pathlib.Path = None
        self.menu_buttons = None
        self.menu_pos = None
        # music
        self.music: MusicData = None
        self.music_paused = False
        self.music_index = -1
        self.music_play_time = 0
        self.music_play_offset = 0
        self.music_loops = False
        self.music_videoclip = None
        self.music_start_time = None
        # custom title
        self.tbarh = 0
        self.tbar_rect = pygame.Rect()
        self.drag_rel_pos = pygame.Vector2()
        self.drag_press_pos = pygame.Vector2()
        self.window_drag = False
        self.window_resize = False
        self.window_stop_special = False
        self.window_drag_effective = False
        self.resize_gmpos = None
        self.resize_winsize = None
        self.resize_winpos = None
        self.resize_handle = None
        self.resize_handles = [
            ResizeHandle(
                self, "topleft", True, None, "xy", pygame.SYSTEM_CURSOR_SIZENWSE
            ),
            ResizeHandle(
                self, "topright", True, None, "y", pygame.SYSTEM_CURSOR_SIZENESW
            ),
            ResizeHandle(
                self, "bottomleft", True, None, "x", pygame.SYSTEM_CURSOR_SIZENESW
            ),
            ResizeHandle(
                self, "bottomright", True, None, None, pygame.SYSTEM_CURSOR_SIZENWSE
            ),
            ResizeHandle(self, "top", False, "x", "y", pygame.SYSTEM_CURSOR_SIZENS),
            ResizeHandle(self, "left", False, "y", "x", pygame.SYSTEM_CURSOR_SIZEWE),
            ResizeHandle(self, "bottom", False, "x", None, pygame.SYSTEM_CURSOR_SIZENS),
            ResizeHandle(self, "right", False, "y", None, pygame.SYSTEM_CURSOR_SIZEWE),
        ]

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
        self.minimize_image = load_icon("minimize")
        self.maximize_image = load_icon("maximize")
        self.resize_image = load_icon("resize")
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
        custom_title = True
        win_pos = self.window.position
        win_size = self.window.size
        discord_presence = False
        try:
            data = load_json(
                "data/settings.json",
                {
                    "volume": 1,
                    "loops": True,
                    "shuffle": False,
                    "fps": 60,
                    "custom_title": True,
                    "win_pos": win_pos,
                    "win_size": win_size,
                    "discord_presence": discord_presence,
                },
            )
            self.volume = data.get("volume", 1)
            self.loops = data.get("loops", True)
            self.shuffle = data.get("shuffle", False)
            self.user_framerate = data.get("fps", 60)
            custom_title = data.get("custom_title", True)
            win_pos = data.get("win_pos", win_pos)
            win_size = data.get("win_size", win_size)
            discord_presence = data.get("discord_presence", False)
        except Exception:
            pass
        self.target_framerate = self.user_framerate
        if win_pos != self.window.position:
            self.window.position = win_pos
        if win_size != self.window.size:
            self.window.size = win_size
        if not custom_title:
            self.toggle_custom_title()
        if discord_presence:
            self.discord_presence.start()

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

    def toggle_custom_title(self):
        if self.custom_title:
            self.custom_title = False
            self.window.borderless = False
            self.window.resizable = True
        else:
            self.custom_title = True
            self.window.borderless = True
            self.window.resizable = True

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
        self.music_start_time = time.time()
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
        self.discord_presence.update()

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
        self.discord_presence.update()

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
                "custom_title": self.custom_title,
                "win_pos": self.window.position,
                "win_size": self.window.size,
                "discord_presence": self.discord_presence.active,
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

        if self.custom_title:
            self.update_borders()
        elif self.focused:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        ratio = self.window.size[0] / self.window.size[1]
        if ratio < 0.45:
            self.window.size = (self.window.size[1] * 0.46, self.window.size[1])

        multx = self.window.size[0] / UI_SIZES[0]
        multy = self.window.size[1] / UI_SIZES[1]
        self.ui_mult = max(0.3, (multx * 0.1 + multy * 1) / 1.1)

        if self.custom_title:
            self.tbarh = 30
            self.tbar_rect = pygame.Rect(0, 0, self.window.size[0], self.tbarh)
        else:
            self.tbarh = 0

        self.start_style = mili.PADLESS | {"spacing": int(self.ui_mult * 3)}
        mili.animation.update_all()

        if (
            self.discord_presence.active
            and pygame.time.get_ticks() - self.discord_presence.last_update
            >= DISCORD_COOLDOWN
        ):
            self.discord_presence.update()

        if self.discord_presence.connect_error is not None:
            self.discord_presence.show_error()
        else:
            if self.discord_presence.connecting:
                self.discord_presence.update_connecting()

    def update_borders(self):
        if not self.can_abs_interact():
            return
        self.window_stop_special = False

        just = pygame.mouse.get_just_pressed()[0]
        mpos = pygame.Vector2(pygame.mouse.get_pos())
        pressed = pygame.mouse.get_pressed()[0]

        for handle in self.resize_handles:
            handle.make_rect()

        anyhover = False
        if not self.window_resize:
            if self.tbar_rect.collidepoint(mpos):
                anyhover = True
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            for handle in self.resize_handles:
                if handle.rect.collidepoint(mpos):
                    pygame.mouse.set_cursor(handle.cursor)
                    anyhover = True
                    break
            if not anyhover:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        if just:
            for handle in self.resize_handles:
                if handle.rect.collidepoint(mpos):
                    self.window_resize = True
                    self.resize_handle = handle
                    self.resize_gmpos = mpos + self.window.position
                    self.resize_winpos = self.window.position
                    self.resize_winsize = self.window.size
                    break
        if pressed:
            if self.window_resize:
                self.resize_handle.update(mpos)
        else:
            if self.window_resize:
                self.window_stop_special = True
            self.window_resize = False

        if self.window_resize:
            return

        if just and self.tbar_rect.collidepoint(mpos):
            self.drag_rel_pos = mpos
            self.drag_press_pos = pygame.Vector2(
                self.drag_rel_pos + self.window.position
            )
            self.window_drag = True
            self.window_drag_effective = False

        if pressed:
            if not just and self.window_drag:
                new = pygame.Vector2(self.window.position) + pygame.mouse.get_pos()
                prev = pygame.Vector2(self.window.position)
                self.window.position = (
                    self.drag_press_pos
                    + (new - self.drag_press_pos)
                    - self.drag_rel_pos
                )
                if (prev - self.window.position).length() != 0:
                    self.window_drag_effective = True
        else:
            if self.window_drag and self.window_drag_effective:
                self.window_stop_special = True
            self.window_drag = False
            self.window_drag_effective = False

    def ui(self):
        self.mili.rect({"color": (BG_CV,) * 3, "border_radius": 0})
        if self.custom_title:
            self.mili.rect(
                {
                    "color": (BORDER_CV,) * 3,
                    "outline": 1,
                    "draw_above": True,
                    "border_radius": 0,
                }
            )
        self.ui_bg_effect()
        self.ui_top()

        with self.mili.begin(None, {"fillx": True, "filly": True} | mili.PADLESS):
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
                    self.anim_settings,
                    self.open_settings,
                    self.settings_image,
                    "bottom",
                )

    def ui_top(self):
        if self.custom_title:
            with self.mili.begin(
                (0, 0, 0, self.tbarh), {"fillx": True, "blocking": False}
            ):
                self.mili.rect({"border_radius": 0, "color": (BORDER_CV / 8,) * 3})

                self.ui_overlay_top_btn(
                    self.anims[0], self.quit, self.close_image, "right", red=True
                )
                self.ui_overlay_top_btn(
                    self.anims[1],
                    self.action_maximize,
                    self.maximize_image,
                    "right",
                    1,
                )
                self.ui_overlay_top_btn(
                    self.anims[2],
                    self.action_minimize,
                    self.minimize_image,
                    "right",
                    2,
                )
                self.ui_overlay_top_btn(
                    self.anims[3],
                    self.toggle_custom_title,
                    self.resize_image,
                    "right",
                    3,
                )
                if self.view_state == "playlist":
                    self.playlist_viewer.ui_top_buttons()
                elif self.view_state == "list":
                    self.list_viewer.ui_top_buttons()
        else:
            self.ui_overlay_top_btn(
                self.anims[0],
                self.quit,
                self.close_image,
                "right",
            )
            if self.view_state == "playlist":
                self.playlist_viewer.ui_top_buttons()
            elif self.view_state == "list":
                self.list_viewer.ui_top_buttons()

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
        xoffset = offset * 0.8
        if (self.view_state == "list" and self.list_viewer.scrollbar.needed) or (
            self.view_state == "playlist" and self.playlist_viewer.scrollbar.needed
        ):
            xoffset = offset * 1.5
        if it := self.mili.element(
            pygame.Rect(0, 0, size, size).move_to(
                bottomright=(
                    self.window.size[0] - xoffset,
                    self.window.size[1]
                    - self.tbarh
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

    def ui_overlay_top_btn(
        self, anim, on_action, line_points_or_image, side, sidei=0, red=False
    ):
        if self.custom_title:
            size = self.tbarh
        else:
            y = self.mili.text_size("Music Player", {"size": self.mult(35)}).y
            size = self.mult(36)
            offset = self.mult(10)
        if it := self.mili.element(
            pygame.Rect(0, 0, size, size).move_to(
                topleft=(
                    0,
                    0,
                )
                if self.custom_title
                else (offset, y / 2 - size / 2 + 5)
            )
            if side == "left"
            else pygame.Rect(0, 0, size, size).move_to(
                topright=(self.window.size[0] - (size * sidei), 0)
                if self.custom_title
                else (
                    self.window.size[0]
                    - (offset if side == "right" else offset * 2 + size),
                    y / 2 - size / 2 + 5,
                )
            ),
            {
                "ignore_grid": True,
                "clip_draw": False,
                "z": 9999,
            },
        ):
            if red:
                color = (TOPB_CV[0],) * 3
                if self.can_abs_interact():
                    if it.hovered:
                        color = (200, 0, 0)
                    if it.left_pressed:
                        color = (80, 0, 0)
            else:
                color = (cond(self, it, *TOPB_CV),) * 3
            self.mili.rect(
                {"color": color, "border_radius": 0}
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
        self.mili._ctx._memory = {}
        self.discord_presence.update()

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

    def action_maximize(self):
        if self.maximized:
            self.window.position = self.before_maximize_data[0]
            self.window.size = self.before_maximize_data[1]
            self.maximized = False
        else:
            self.before_maximize_data = self.window.position, self.window.size
            self.window.position = (0, 0)
            self.window.size = pygame.display.get_desktop_sizes()[0]
            self.maximized = True
        self.make_bg_image()

    def action_minimize(self):
        self.window.minimize()

    def can_interact(self):
        return (
            self.can_abs_interact()
            and not self.window_drag
            and not self.window_resize
            and not self.window_stop_special
        )

    def can_abs_interact(self):
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
        if (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_q
            and event.mod & pygame.KMOD_CTRL
        ):
            self.quit()
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
