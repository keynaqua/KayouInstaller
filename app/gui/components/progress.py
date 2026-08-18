import tkinter as tk

from config import GUI_FONT_SEMIBOLD, PALETTE
from .antialias import box, render_photo


class RoundedProgress(tk.Canvas):
    def __init__(self, parent, *, show_bytes=True, height=24):
        super().__init__(parent, height=height, bg=parent.cget("bg"), bd=0, highlightthickness=0)
        self.value = 0
        self.received = 0.0
        self.total = None
        self.show_bytes = show_bytes
        self.bind("<Configure>", self._draw)

    def set(self, value, received=None, total=None):
        self.value = max(0, min(100, int(value)))
        if received is not None:
            self.received = received
        if total is not None:
            self.total = total
        self._draw()

    def _label(self):
        if self.show_bytes and self.total is not None:
            return f"{self.value} %  ·  {self.received:.1f}/{self.total:.1f} Mo"
        return f"{self.value} %"

    def _draw(self, _event=None):
        self.delete("all")
        width, height = self.winfo_width(), self.winfo_height()
        if width <= 1 or height <= 1:
            return
        fill_width = int(width * self.value / 100)

        def paint(draw, scale):
            draw.rounded_rectangle(box((0, 0, width - 1, height - 1), scale), radius=height * scale // 2, fill=PALETTE["accent_dark"])
            if fill_width:
                radius = min(height / 2, fill_width / 2)
                draw.rounded_rectangle(box((0, 0, fill_width, height - 1), scale), radius=round(radius * scale), fill=PALETTE["accent"])

        self._surface = render_photo(self, width, height, self.cget("bg"), paint)
        self.create_image(0, 0, image=self._surface, anchor="nw")
        self.create_text(width / 2, height / 2, text=self._label(), fill=PALETTE["text"], font=(GUI_FONT_SEMIBOLD, 9))
