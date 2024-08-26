import mili
import pygame
import functools


class UIEntryline:
    def __init__(self, placeholder="Enter text...", target_files=True):
        self.text = ""
        self.cursor = 0
        self.placeholder = placeholder
        self.cursor_on = True
        self.cursor_time = pygame.time.get_ticks()
        self.action_start_time = pygame.time.get_ticks()
        self.action_data = None
        self.action_time = pygame.time.get_ticks()
        self.target_files = target_files

    def add(self, char):
        left, right = self.text[: self.cursor], self.text[self.cursor :]
        self.text = left + char + right
        self.cursor += 1

    def remove(self):
        if self.cursor > 0:
            left, right = self.text[: self.cursor], self.text[self.cursor :]
            self.text = left[:-1] + right
            self.cursor -= 1

    def canc(self):
        if self.cursor <= len(self.text):
            left, right = self.text[: self.cursor], self.text[self.cursor :]
            self.text = left[: self.cursor] + right[1:]

    def move(self, dir):
        self.cursor += dir
        if self.cursor < 0:
            self.cursor = 0
        if self.cursor > len(self.text):
            self.cursor = len(self.text)

    def start_action(self, func, *args):
        self.action_start_time = pygame.time.get_ticks()
        self.action_data = (func, args)

    def event(self, event):
        if event.type == pygame.TEXTINPUT:
            if self.target_files and event.text in [
                "<",
                ">",
                ":",
                '"',
                "/",
                "\\",
                "|",
                "?",
                "*",
                ".",
            ]:
                return
            self.set_cursor_on()
            self.add(event.text)
            self.start_action(self.add, event.text)
        if event.type == pygame.KEYDOWN:
            self.set_cursor_on()
            if event.key == pygame.K_LEFT:
                self.move(-1)
                self.start_action(self.move, -1)
            elif event.key == pygame.K_RIGHT:
                self.move(1)
                self.start_action(self.move, 1)
            elif event.key == pygame.K_BACKSPACE:
                self.remove()
                self.start_action(self.remove)
            elif event.key == pygame.K_DELETE:
                self.canc()
                self.start_action(self.canc)
        if event.type == pygame.KEYUP:
            self.action_data = None

    def update(self):
        if pygame.time.get_ticks() - self.cursor_time >= 350:
            self.cursor_on = not self.cursor_on
            self.cursor_time = pygame.time.get_ticks()

        if self.action_data is None:
            return
        if pygame.time.get_ticks() - self.action_start_time < (
            800 if self.action_data[0] is self.add else 500
        ):
            self.set_cursor_on()
            return

        if pygame.time.get_ticks() - self.action_time >= (
            80 if self.action_data[0] is self.add else 30
        ):
            self.action_time = pygame.time.get_ticks()
            self.action_data[0](*self.action_data[1])
            self.set_cursor_on()

    def set_cursor_on(self):
        self.cursor_on = True
        self.cursor_time = pygame.time.get_ticks()

    def draw_cursor(self, csize, offset, canva, element_data, rect):
        if not self.cursor_on:
            return
        curs = rect.h / 1.5
        xpos = rect.x + csize - offset + 5
        if offset != 0:
            xpos += 5
        pygame.draw.line(
            canva,
            (255,) * 3,
            (xpos, rect.y + rect.h / 2 - curs / 2),
            (xpos, rect.y + rect.h / 2 + curs / 2),
        )

    def ui(self, mili_: mili.MILI, rect, style, mult, bgcol=20, outlinecol=40):
        with mili_.begin(rect, style | {"axis": "x"}, get_data=True) as data:
            rect = data.rect
            mili_.rect({"color": (bgcol,) * 3, "border_radius": 0})
            mili_.rect(
                {
                    "color": (outlinecol,) * 3,
                    "outline": 1,
                    "border_radius": 0,
                    "draw_above": True,
                }
            )

            txtocursor = self.text[: self.cursor]
            size = mili_.text_size(txtocursor, {"size": mult(20)})
            offsetx = size.x - (rect.w - 15)
            if offsetx < 0:
                offsetx = 0

            if mili_.element(
                (0, 0, 0, 0),
                {
                    "align": "center",
                    "offset": (-offsetx, 0),
                    "post_draw_func": functools.partial(
                        self.draw_cursor, size.x, offsetx
                    ),
                },
                get_data=True,
            ):
                text = self.text
                if len(self.text) == 1:
                    text = f"{text} "
                mili_.text(
                    text if self.text else self.placeholder,
                    {"color": (255 if self.text else 120,) * 3, "size": mult(20)},
                )
