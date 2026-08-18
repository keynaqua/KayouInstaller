import tkinter as tk


def _rounded(canvas, left, top, right, bottom, radius, color, tag):
    radius = int(max(0, min(radius, (right - left) / 2, (bottom - top) / 2)))
    if not radius:
        canvas.create_rectangle(left, top, right, bottom, fill=color, outline=color, tags=tag)
        return
    # Overlap every primitive by one pixel. Tk's non-antialiased arcs otherwise
    # leave a pinhole where an arc meets a rectangle on some Windows DPI scales.
    canvas.create_rectangle(left + radius - 1, top, right - radius + 1, bottom, fill=color, outline=color, tags=tag)
    canvas.create_rectangle(left, top + radius - 1, right, bottom - radius + 1, fill=color, outline=color, tags=tag)
    canvas.create_arc(left, top, left + radius * 2, top + radius * 2, start=90, extent=90, style="pieslice", fill=color, outline=color, tags=tag)
    canvas.create_arc(right - radius * 2, top, right, top + radius * 2, start=0, extent=90, style="pieslice", fill=color, outline=color, tags=tag)
    canvas.create_arc(left, bottom - radius * 2, left + radius * 2, bottom, start=180, extent=90, style="pieslice", fill=color, outline=color, tags=tag)
    canvas.create_arc(right - radius * 2, bottom - radius * 2, right, bottom, start=270, extent=90, style="pieslice", fill=color, outline=color, tags=tag)


class RoundedPanel(tk.Canvas):
    def __init__(self, parent, fill, radius=8, border=None, width=200, height=100, padding=0):
        super().__init__(parent, width=width, height=height, bg=parent.cget("bg"), bd=0, highlightthickness=0)
        self.fill = fill
        self.radius = radius
        self.border = border or fill
        self.padding = padding
        self.content = tk.Frame(self, bg=fill)
        self.window = self.create_window(0, 0, anchor="nw", window=self.content)
        self.bind("<Configure>", self._draw)

    def _draw(self, event):
        width = max(1, event.width)
        height = max(1, event.height)
        self.delete("panel")
        _rounded(self, 0, 0, width - 1, height - 1, self.radius, self.border, "panel")
        _rounded(self, 1, 1, width - 2, height - 2, max(0, self.radius - 1), self.fill, "panel")
        inset = max(self.radius, self.padding + 2)
        self.coords(self.window, inset, inset)
        self.itemconfigure(self.window, width=max(1, width - inset * 2), height=max(1, height - inset * 2))
        self.tag_lower("panel")
