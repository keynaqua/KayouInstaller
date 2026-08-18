import tkinter as tk

from config import APP_TITLE, GUI_FONT_SEMIBOLD, PALETTE
from gui.components import create_mark


def build_splash_screen(parent, logo=None):
    screen = tk.Frame(parent, bg=PALETTE["bg"])
    screen.grid(row=0, column=0, sticky="nsew")
    screen.grid_rowconfigure(0, weight=1)
    screen.grid_columnconfigure(0, weight=1)
    center = tk.Frame(screen, bg=PALETTE["bg"])
    center.grid(row=0, column=0)
    create_mark(center, 104, image=logo).grid(row=0, column=0, pady=(0, 18))
    tk.Label(
        center,
        text=APP_TITLE,
        bg=PALETTE["bg"],
        fg=PALETTE["text"],
        font=(GUI_FONT_SEMIBOLD, 30),
    ).grid(row=1, column=0)
    return screen
