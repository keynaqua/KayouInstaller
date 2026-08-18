import tkinter as tk

from config import PALETTE
from .antialias import box, render_photo


class SmoothScrollbar(tk.Canvas):
    def __init__(self, parent, command):
        super().__init__(parent, width=12, bg=parent.cget("bg"), bd=0, highlightthickness=0, cursor="hand2")
        self.command = command
        self.first = 0.0
        self.last = 1.0
        self.drag_offset = 0
        self.bind("<Configure>", self._draw)
        self.bind("<Button-1>", self._press)
        self.bind("<B1-Motion>", self._drag)

    def set(self, first, last):
        self.first, self.last = float(first), float(last)
        self._draw()
        self.after_idle(self._update_visibility)

    def _update_visibility(self):
        if not self.winfo_exists():
            return
        if self.first <= 0.001 and self.last >= 0.999:
            self.grid_remove()
        else:
            self.grid()

    def _bounds(self):
        height = max(1, self.winfo_height())
        top = int(self.first * height)
        bottom = max(top + 34, int(self.last * height))
        if bottom > height:
            top -= bottom - height
            bottom = height
        return max(0, top), bottom

    def _draw(self, _event=None):
        self.delete("all")
        if self.first <= 0.001 and self.last >= 0.999:
            return
        top, bottom = self._bounds()
        color = PALETTE["button_alt_hover"]
        width, height = max(1, self.winfo_width()), max(1, self.winfo_height())

        def paint(draw, scale):
            draw.rounded_rectangle(box((2, top, width - 2, bottom), scale), radius=4 * scale, fill=color)

        self._surface = render_photo(self, width, height, self.cget("bg"), paint)
        self.create_image(0, 0, image=self._surface, anchor="nw")

    def _press(self, event):
        top, bottom = self._bounds()
        self.drag_offset = event.y - top if top <= event.y <= bottom else (bottom - top) // 2
        self._move(event.y)

    def _drag(self, event):
        self._move(event.y)

    def _move(self, y):
        height = max(1, self.winfo_height())
        thumb = max(34, int((self.last - self.first) * height))
        position = max(0, min(height - thumb, y - self.drag_offset))
        self.command("moveto", position / max(1, height - thumb))
