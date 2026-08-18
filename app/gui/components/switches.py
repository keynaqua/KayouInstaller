import tkinter as tk

from config import GUI_FONT, PALETTE
from .antialias import box, render_photo


class Switch(tk.Canvas):
    def __init__(self, parent, text: str, variable: tk.BooleanVar, command=None):
        super().__init__(parent, height=42, bg=parent.cget("bg"), bd=0, highlightthickness=0, cursor="hand2")
        self.text = text
        self.variable = variable
        self.command = command
        self.bind("<Button-1>", self._toggle)
        self.bind("<Configure>", self._draw)
        self._draw()

    def _toggle(self, _event=None):
        self.variable.set(not self.variable.get())
        self._draw()
        if self.command:
            self.command()

    def _draw(self, _event=None):
        self.delete("all")
        active = self.variable.get()
        center = max(21, self.winfo_height() / 2)
        self.create_text(0, center, text=self.text, fill=PALETTE["text"], font=(GUI_FONT, 11), anchor="w")
        left = max(0, self.winfo_width() - 48)
        color = PALETTE["accent"] if active else PALETTE["button_disabled"]
        top = center - 11
        knob_left = 28 if active else 4

        def paint(draw, scale):
            draw.rounded_rectangle(box((0, 0, 48, 22), scale), radius=11 * scale, fill=color)
            draw.ellipse(box((knob_left, 3, knob_left + 16, 19), scale), fill=PALETTE["text"])

        self._switch_surface = render_photo(self, 48, 22, self.cget("bg"), paint)
        self.create_image(left, top, image=self._switch_surface, anchor="nw")
