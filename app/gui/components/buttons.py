import tkinter as tk

from config import GUI_FONT_SEMIBOLD, PALETTE
from .antialias import box, render_photo


class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, bg, hover):
        self.text = text
        self.command = command
        self.normal = bg
        self.hover = hover
        self.fill = bg
        self.foreground = PALETTE["text"]
        self.disabledforeground = PALETTE["button_disabled_text"]
        self.state = "normal"
        self.button_width = max(140, len(text) * 10 + 54)
        super().__init__(parent, width=self.button_width, height=50, bg=parent.cget("bg"), bd=0, highlightthickness=0, cursor="hand2")
        self.bind("<Configure>", self._draw, add="+")
        self.bind("<Enter>", self._enter, add="+")
        self.bind("<Leave>", self._leave, add="+")
        self.bind("<Button-1>", self._click, add="+")
        self._draw()

    def _draw(self, _event=None):
        self.delete("all")
        width = max(self.winfo_width(), self.button_width)
        height = max(self.winfo_height(), 50)
        color = self.fill if self.state == "normal" else PALETTE["button_disabled"]
        text = self.foreground if self.state == "normal" else self.disabledforeground
        background = self.cget("bg")

        def paint(draw, scale):
            draw.rounded_rectangle(box((2, 2, width - 3, height - 3), scale), radius=12 * scale, fill=color)

        self._surface = render_photo(self, width, height, background, paint)
        self.create_image(0, 0, image=self._surface, anchor="nw")
        self.create_text(width / 2, height / 2, text=self.text, fill=text, font=(GUI_FONT_SEMIBOLD, 12))

    def _enter(self, _event):
        if self.state == "normal":
            self.fill = self.hover
            self._draw()

    def _leave(self, _event):
        self.fill = self.normal
        self._draw()

    def _click(self, _event):
        if self.state == "normal":
            self.command()

    def config(self, **values):
        if "text" in values:
            self.text = values.pop("text")
            self.button_width = max(140, len(self.text) * 10 + 54)
            values["width"] = self.button_width
        if "state" in values:
            self.state = values.pop("state")
        if "bg" in values:
            self.normal = values.pop("bg")
            self.fill = self.normal
        if "fg" in values:
            self.foreground = values.pop("fg")
        if "disabledforeground" in values:
            self.disabledforeground = values.pop("disabledforeground")
        if "width" in values:
            self.button_width = max(140, int(values.pop("width")) * 12)
            values["width"] = self.button_width
        if values:
            super().config(**values)
        self._draw()

    configure = config


def create_button(parent, text: str, command, variant: str = "primary"):
    if variant == "primary":
        colors = PALETTE["button"], PALETTE["button_hover"]
    elif variant == "danger":
        colors = PALETTE["error_dark"], PALETTE["error"]
    else:
        colors = PALETTE["button_alt"], PALETTE["button_alt_hover"]
    return RoundedButton(parent, text, command, *colors)
