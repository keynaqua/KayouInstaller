import tkinter as tk

from config import PALETTE
from .antialias import box, render_photo


def create_mark(parent, size: int = 84, bg: str | None = None, image=None):
    background = bg or PALETTE["bg"]
    if image:
        return tk.Label(parent, image=image, bg=background, bd=0)
    canvas = tk.Canvas(parent, width=size, height=size, bg=background, bd=0, highlightthickness=0)
    pad, center, radius = max(3, size // 16), size / 2, size * 0.15

    def paint(draw, scale):
        bounds = box((pad, pad, size - pad, size - pad), scale)
        draw.ellipse(bounds, fill=PALETTE["accent"])
        draw.pieslice(bounds, start=180, end=360, fill=PALETTE["magenta"])
        draw.rectangle(box((pad, center - size * 0.06, size - pad, center + size * 0.06), scale), fill=background)
        draw.ellipse(box((center - radius, center - radius, center + radius, center + radius), scale), fill=PALETTE["text"], outline=background, width=max(2, size // 28) * scale)

    canvas._surface = render_photo(canvas, size, size, background, paint)
    canvas.create_image(0, 0, image=canvas._surface, anchor="nw")
    return canvas
