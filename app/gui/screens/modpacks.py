import tkinter as tk

from catalog import CatalogEntry
from config import GUI_FONT, GUI_FONT_SEMIBOLD, PALETTE
from gui.components import SmoothScrollbar, create_button
from gui.components.antialias import box, render_photo


def _fallback_logo(parent, modpack: CatalogEntry, disabled: bool):
    size = 58
    canvas = tk.Canvas(parent, width=size, height=size, bd=0, highlightthickness=0, bg=PALETTE["surface"])
    colors = (PALETTE["accent"], PALETTE["magenta"], PALETTE["success"], PALETTE["warning"])
    color = PALETTE["button_disabled_text"] if disabled else colors[sum(map(ord, modpack.id)) % len(colors)]
    canvas._surface = render_photo(canvas, size, size, PALETTE["surface"], lambda draw, scale: draw.ellipse(box((3, 3, size - 3, size - 3), scale), fill=color))
    canvas.create_image(0, 0, image=canvas._surface, anchor="nw")
    initials = "".join(word[0] for word in modpack.name.split()[:2]).upper()
    canvas.create_text(size / 2, size / 2, text=initials, fill=PALETTE["bg"], font=(GUI_FONT_SEMIBOLD, 16))
    return canvas


def _logo(parent, image, disabled: bool):
    size = 64
    canvas = tk.Canvas(parent, width=size, height=size, bd=0, highlightthickness=0, bg=PALETTE["surface"])
    color = PALETTE["button_disabled"] if disabled else PALETTE["border"]
    canvas._surface = render_photo(canvas, size, size, PALETTE["surface"], lambda draw, scale: draw.ellipse(box((2, 2, size - 2, size - 2), scale), fill=color))
    canvas.create_image(0, 0, image=canvas._surface, anchor="nw")
    canvas.create_image(size / 2, size / 2, image=image)
    return canvas


def _card(parent, modpack: CatalogEntry, logo, on_select, install_mode: bool, row: int):
    disabled = install_mode and not modpack.enabled
    card = tk.Frame(parent, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1, padx=18, pady=14)
    card.grid(row=row, column=0, sticky="ew", pady=(0, 12))
    card.grid_columnconfigure(1, weight=1)
    if logo:
        _logo(card, logo, disabled).grid(row=0, column=0, rowspan=2, padx=(0, 16))
    else:
        _fallback_logo(card, modpack, disabled).grid(row=0, column=0, rowspan=2, padx=(0, 16))
    color = PALETTE["button_disabled_text"] if disabled else PALETTE["text"]
    tk.Label(card, text=modpack.name, bg=PALETTE["surface"], fg=color, anchor="w", font=(GUI_FONT_SEMIBOLD, 15)).grid(row=0, column=1, sticky="sw")
    details = "Indisponible" if disabled else " · ".join(value for value in (modpack.minecraft_version, modpack.loader.title()) if value)
    tk.Label(card, text=details, bg=PALETTE["surface"], fg=PALETTE["button_disabled_text"] if disabled else PALETTE["muted"], anchor="w", font=(GUI_FONT, 10)).grid(row=1, column=1, sticky="nw", pady=(4, 0))
    if disabled:
        button = create_button(card, "Désactivé", lambda: None, variant="secondary")
        button.config(state="disabled", bg=PALETTE["button_disabled"], disabledforeground=PALETTE["button_disabled_text"], cursor="", width=10)
    else:
        button = create_button(card, "Choisir", lambda: on_select(modpack), variant="secondary")
        button.config(width=10)
    button.grid(row=0, column=2, rowspan=2, padx=(18, 0))


def build_modpack_screen(parent, on_select, on_back, modpacks: list[CatalogEntry], logos: dict[str, tk.PhotoImage] | None = None, default_logo=None, title_text: str = "Choisir un modpack", install_mode: bool = True):
    screen = tk.Frame(parent, bg=PALETTE["bg"])
    screen.grid(row=0, column=0, sticky="nsew")
    screen.grid_rowconfigure(1, weight=1)
    screen.grid_columnconfigure(0, weight=1)
    tk.Label(screen, text=title_text, bg=PALETTE["bg"], fg=PALETTE["text"], font=(GUI_FONT_SEMIBOLD, 30)).grid(row=0, column=0, pady=(34, 22))
    body = tk.Frame(screen, bg=PALETTE["bg"])
    body.grid(row=1, column=0, sticky="nsew", padx=90)
    body.grid_rowconfigure(0, weight=1)
    body.grid_columnconfigure(0, weight=1)
    canvas = tk.Canvas(body, bg=PALETTE["bg"], bd=0, highlightthickness=0)
    scrollbar = SmoothScrollbar(body, canvas.yview)
    content = tk.Frame(canvas, bg=PALETTE["bg"])
    content.grid_columnconfigure(0, weight=1)
    window = canvas.create_window((0, 0), window=content, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    content.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window, width=event.width))
    canvas.bind("<MouseWheel>", lambda event: canvas.yview_scroll(-int(event.delta / 120), "units"))
    select = lambda pack: on_select(pack, False) if install_mode else on_select(pack)
    for index, modpack in enumerate(modpacks):
        _card(content, modpack, (logos or {}).get(modpack.id) or default_logo, select, install_mode, index)
    if not modpacks:
        tk.Label(content, text="Aucun modpack installé.", bg=PALETTE["bg"], fg=PALETTE["muted"], font=(GUI_FONT, 12)).grid(row=0, column=0, pady=60)
    create_button(screen, "Retour", on_back, variant="secondary").grid(row=2, column=0, pady=24)
    return screen
