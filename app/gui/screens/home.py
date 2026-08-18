import tkinter as tk

from config import APP_TITLE, GUI_FONT_SEMIBOLD, PALETTE
from gui.components import create_button, create_mark


def build_home_screen(parent, on_launch, on_uninstall, on_close, logo=None):
    screen = tk.Frame(parent, bg=PALETTE["bg"])
    screen.grid(row=0, column=0, sticky="nsew")
    screen.grid_rowconfigure(0, weight=1)
    screen.grid_columnconfigure(0, weight=1)

    center = tk.Frame(screen, bg=PALETTE["bg"])
    center.grid(row=0, column=0)
    center.grid_columnconfigure(0, weight=1)

    create_mark(center, 88, image=logo).grid(row=0, column=0, pady=(0, 14))

    title = tk.Label(
        center,
        text=APP_TITLE,
        bg=PALETTE["bg"],
        fg=PALETTE["text"],
        font=(GUI_FONT_SEMIBOLD, 42),
    )
    title.grid(row=1, column=0, pady=(0, 28))

    menu = tk.Frame(
        center,
        bg=PALETTE["surface"],
        highlightbackground=PALETTE["border"],
        highlightthickness=1,
        padx=32,
        pady=30,
        width=390,
        height=264,
    )
    menu.grid(row=2, column=0)
    menu.grid_columnconfigure(0, weight=1, minsize=256)
    menu.grid_propagate(False)

    launch = create_button(menu, "Installer", on_launch)
    launch.grid(row=0, column=0, sticky="ew", pady=(0, 14))

    uninstall = create_button(menu, "Désinstaller", on_uninstall, variant="secondary")
    uninstall.grid(row=1, column=0, sticky="ew")

    close = create_button(menu, "Fermer", on_close, variant="secondary")
    close.grid(row=2, column=0, sticky="ew", pady=(14, 0))

    return screen
