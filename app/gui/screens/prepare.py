import json
import re
import shutil
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox

from catalog import CatalogEntry
from config import GUI_FONT, GUI_FONT_SEMIBOLD, INSTALLATIONS_DIR_NAME, PALETTE, get_launcher_profiles_path, get_minecraft_dir
from gui.components import RoundedPanel, SmoothScrollbar, Switch, create_button
from gui.core.windows import center_window
from minecraft.worlds import create_world as create_minecraft_world
from utils.resources import resource_path
from gui.components.antialias import box as aa_box, render_photo
from utils.system import get_ram_limits, get_recommended_ram_gb, get_total_ram_gb


@dataclass(frozen=True)
class World:
    name: str
    path: Path

    @property
    def icon(self):
        return self.path / "icon.png"


def _key(value: str) -> str:
    return "".join(char for char in value.casefold() if char.isalnum())


def _game_dirs(modpack: CatalogEntry) -> set[Path]:
    try:
        root = get_minecraft_dir() / INSTALLATIONS_DIR_NAME
    except RuntimeError:
        return set()
    installation_dir = modpack.installation_dir or modpack.id
    keys = {_key(modpack.id), _key(modpack.name), _key(installation_dir)}
    found = set()
    expected = root / installation_dir
    if expected.is_dir():
        found.add(expected)
    try:
        profiles = json.loads(get_launcher_profiles_path().read_text(encoding="utf-8")).get("profiles", {})
        for key, profile in profiles.items():
            if {_key(key), _key(str(profile.get("name", "")))} & keys and profile.get("gameDir"):
                found.add(Path(profile["gameDir"]))
    except (OSError, ValueError, AttributeError):
        pass
    if root.is_dir():
        found.update(path for path in root.iterdir() if path.is_dir() and _key(path.name) in keys)
    return found


def _worlds(modpack: CatalogEntry) -> list[World]:
    worlds = {}
    for game_dir in _game_dirs(modpack):
        saves = game_dir / "saves"
        if saves.is_dir():
            for path in saves.iterdir():
                if path.is_dir():
                    worlds.setdefault(path.name.casefold(), World(path.name, path))
    return sorted(worlds.values(), key=lambda world: world.name.casefold())


def _world_settings_dialog(parent) -> dict | None:
    dialog = tk.Toplevel(parent)
    dialog.title("Créer un monde")
    dialog.configure(bg=PALETTE["bg"])
    dialog.transient(parent)
    dialog.grab_set()
    center_window(dialog, parent, 620, 610)
    result = {}
    name = tk.StringVar(value="Nouveau monde")
    mode = tk.IntVar(value=0)
    difficulty = tk.IntVar(value=2)
    commands = tk.BooleanVar(value=False)

    shell = RoundedPanel(dialog, PALETTE["surface"], radius=8, border=PALETTE["border"])
    shell.pack(fill="both", expand=True, padx=18, pady=18)
    card = shell.content
    card.config(padx=30, pady=26)
    card.grid_columnconfigure(0, weight=1)
    tk.Label(card, text="Créer un nouveau monde", bg=PALETTE["surface"], fg=PALETTE["text"], font=(GUI_FONT_SEMIBOLD, 23)).grid(row=0, column=0, sticky="w")
    tk.Label(card, text="Configure sa première génération. Ces réglages pourront être modifiés dans Minecraft.", bg=PALETTE["surface"], fg=PALETTE["muted"], font=(GUI_FONT, 10), wraplength=520, justify="left").grid(row=1, column=0, sticky="w", pady=(5, 20))
    tk.Label(card, text="NOM DU MONDE", bg=PALETTE["surface"], fg=PALETTE["muted"], font=(GUI_FONT_SEMIBOLD, 9)).grid(row=2, column=0, sticky="w")
    entry_frame = tk.Frame(card, bg=PALETTE["border"], padx=1, pady=1)
    entry_frame.grid(row=3, column=0, sticky="ew", pady=(6, 18))
    entry = tk.Entry(entry_frame, textvariable=name, bg=PALETTE["surface_alt"], fg=PALETTE["text"], insertbackground=PALETTE["text"], relief="flat", font=(GUI_FONT, 12))
    entry.pack(fill="x", ipady=11, padx=1, pady=1)

    def choices(row, title, variable, values):
        tk.Label(card, text=title, bg=PALETTE["surface"], fg=PALETTE["muted"], font=(GUI_FONT_SEMIBOLD, 9)).grid(row=row, column=0, sticky="w")
        frame = tk.Frame(card, bg=PALETTE["surface"])
        frame.grid(row=row + 1, column=0, sticky="ew", pady=(7, 17))
        buttons = []

        def select(value):
            variable.set(value)
            for button, button_value in buttons:
                active = button_value == value
                button.config(
                    bg=PALETTE["accent_dark"] if active else PALETTE["surface_alt"],
                    fg=PALETTE["accent"] if active else PALETTE["text"],
                    highlightbackground=PALETTE["accent"] if active else PALETTE["border"],
                )

        for column, (text, value) in enumerate(values):
            frame.grid_columnconfigure(column, weight=1)
            button = tk.Button(
                frame, text=text, command=lambda selected=value: select(selected), relief="flat", bd=0,
                highlightthickness=1, activebackground=PALETTE["accent_dark"], activeforeground=PALETTE["accent"],
                cursor="hand2", font=(GUI_FONT_SEMIBOLD, 10), pady=10,
            )
            button.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 4, 0 if column == len(values) - 1 else 4))
            buttons.append((button, value))
        select(variable.get())

    choices(4, "MODE DE JEU", mode, (("Survie", 0), ("Créatif", 1), ("Aventure", 2), ("Spectateur", 3)))
    choices(6, "DIFFICULTÉ", difficulty, (("Paisible", 0), ("Facile", 1), ("Normale", 2), ("Difficile", 3)))
    command_box = RoundedPanel(card, PALETTE["surface_alt"], radius=8, border=PALETTE["border"], height=62)
    command_box.grid(row=8, column=0, sticky="ew", pady=(0, 12))
    command_box.content.config(padx=14, pady=6)
    Switch(command_box.content, "Autoriser les commandes", commands).pack(fill="both", expand=True)

    def confirm():
        if not name.get().strip():
            messagebox.showerror("Nom invalide", "Donne un nom au monde.", parent=dialog)
            return
        result.update(name=name.get().strip(), mode=mode.get(), difficulty=difficulty.get(), commands=commands.get())
        dialog.destroy()

    actions = tk.Frame(card, bg=PALETTE["surface"])
    actions.grid(row=9, column=0, pady=(12, 0))
    create_button(actions, "Créer", confirm).grid(row=0, column=0, padx=6)
    create_button(actions, "Annuler", dialog.destroy, variant="secondary").grid(row=0, column=1, padx=6)
    entry.focus_set()
    dialog.wait_window()
    return result or None


def _create_world(modpack: CatalogEntry, parent) -> World | None:
    settings = _world_settings_dialog(parent)
    if not settings:
        return None
    name = settings["name"]
    folder = re.sub(r'[<>:"/\\|?*]+', "_", name).strip(" .") or "Nouveau monde"
    try:
        installation_dir = modpack.installation_dir or modpack.id
        game_dir = get_minecraft_dir() / INSTALLATIONS_DIR_NAME / installation_dir
    except RuntimeError as exc:
        messagebox.showerror("Création impossible", str(exc), parent=parent)
        return None
    world_dir = game_dir / "saves" / folder
    suffix = 2
    while world_dir.exists():
        world_dir = game_dir / "saves" / f"{folder} ({suffix})"
        suffix += 1
    try:
        (world_dir / "datapacks").mkdir(parents=True)
        create_minecraft_world(
            game_dir, world_dir.name, name, modpack.minecraft_version,
            settings["mode"], settings["difficulty"], settings["commands"],
        )
    except (OSError, RuntimeError) as exc:
        shutil.rmtree(world_dir, ignore_errors=True)
        messagebox.showerror("Création impossible", str(exc), parent=parent)
        return None
    return World(world_dir.name, world_dir)


def _fallback_icon(parent, name: str):
    canvas = tk.Canvas(parent, width=76, height=76, bg=PALETTE["surface_alt"], bd=0, highlightthickness=0)
    def paint(draw, scale):
        draw.ellipse(aa_box((2, 2, 74, 74), scale), fill=PALETTE["accent_dark"], outline=PALETTE["border"], width=scale)

    canvas._surface = render_photo(canvas, 76, 76, PALETTE["surface_alt"], paint)
    canvas.create_image(0, 0, image=canvas._surface, anchor="nw")
    canvas.create_text(38, 38, text=name[:1].upper(), fill=PALETTE["text"], font=(GUI_FONT_SEMIBOLD, 23))
    return canvas


class RamSlider(tk.Canvas):
    def __init__(self, parent, variable: tk.IntVar, minimum: int, maximum: int):
        self.disabled = minimum >= maximum
        super().__init__(parent, height=34, bg=parent.cget("bg"), bd=0, highlightthickness=0, cursor="arrow" if self.disabled else "hand2")
        self.variable = variable
        self.minimum = minimum
        self.maximum = max(minimum, maximum)
        self.bind("<Configure>", self._draw)
        self.bind("<Button-1>", self._set_from_event)
        self.bind("<B1-Motion>", self._set_from_event)
        self.variable.trace_add("write", lambda *_args: self._draw())

    def _position(self) -> float:
        span = max(1, self.maximum - self.minimum)
        return (self.variable.get() - self.minimum) / span

    def _set_from_event(self, event):
        if self.disabled:
            return
        left, right = 12, max(13, self.winfo_width() - 12)
        ratio = max(0.0, min(1.0, (event.x - left) / max(1, right - left)))
        self.variable.set(round(self.minimum + ratio * (self.maximum - self.minimum)))

    def _draw(self, _event=None):
        self.delete("all")
        left, right = 12, max(13, self.winfo_width() - 12)
        center = 17
        position = left + (right - left) * self._position()
        width, height = max(1, self.winfo_width()), max(1, self.winfo_height())
        active = PALETTE["button_disabled_text"] if self.disabled else PALETTE["accent"]

        def paint(draw, scale):
            draw.rounded_rectangle(aa_box((left, center - 4, right, center + 4), scale), radius=4 * scale, fill=PALETTE["button_disabled"])
            draw.rounded_rectangle(aa_box((left, center - 4, max(left + 8, position), center + 4), scale), radius=4 * scale, fill=active)
            draw.ellipse(aa_box((position - 9, center - 9, position + 9, center + 9), scale), fill=PALETTE["text"], outline=active, width=3 * scale)

        self._surface = render_photo(self, width, height, self.cget("bg"), paint)
        self.create_image(0, 0, image=self._surface, anchor="nw")


def open_world_selector(root, modpack: CatalogEntry, selected: str, on_select):
    window = tk.Toplevel(root)
    window.title("Choisir un monde")
    window.configure(bg=PALETTE["bg"])
    window.transient(root)
    window.grab_set()
    center_window(window, root, 680, 520)
    shell = RoundedPanel(window, PALETTE["surface"], radius=8, border=PALETTE["border"])
    shell.pack(fill="both", expand=True, padx=18, pady=18)
    card = shell.content
    card.config(padx=22, pady=18)
    card.grid_columnconfigure(0, weight=1)
    card.grid_rowconfigure(2, weight=1)
    tk.Label(card, text="Monde des datapacks", bg=PALETTE["surface"], fg=PALETTE["text"], font=(GUI_FONT_SEMIBOLD, 21)).grid(row=0, column=0, sticky="w")
    tk.Label(card, text="Les datapacks seront copiés dans le monde sélectionné.", bg=PALETTE["surface"], fg=PALETTE["muted"], font=(GUI_FONT, 10)).grid(row=1, column=0, sticky="w", pady=(4, 14))
    body = tk.Frame(card, bg=PALETTE["surface"])
    body.grid(row=2, column=0, sticky="nsew")
    body.grid_columnconfigure(0, weight=1)
    body.grid_rowconfigure(0, weight=1)
    canvas = tk.Canvas(body, bg=PALETTE["surface"], bd=0, highlightthickness=0)
    scrollbar = SmoothScrollbar(body, canvas.yview)
    list_frame = tk.Frame(canvas, bg=PALETTE["surface"])
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    canvas.create_window((0, 0), window=list_frame, anchor="nw", tags="content")

    def update_world_scroll(_event=None):
        canvas.itemconfigure("content", width=canvas.winfo_width())
        canvas.configure(scrollregion=canvas.bbox("all"))
        if list_frame.winfo_reqheight() > canvas.winfo_height():
            scrollbar.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        else:
            scrollbar.grid_remove()
            canvas.yview_moveto(0)

    canvas.bind("<Configure>", lambda _event: canvas.after_idle(update_world_scroll))
    list_frame.bind("<Configure>", lambda _event: canvas.after_idle(update_world_scroll))
    canvas.bind("<MouseWheel>", lambda event: canvas.yview_scroll(-1 if event.delta > 0 else 1, "units"))
    window.images = []

    def choose(name: str):
        on_select(name)
        window.destroy()

    def add_world(world: World | None):
        name = world.name if world else "Aucun monde"
        active = name == selected or not world and not selected
        row = tk.Frame(list_frame, bg=PALETTE["surface_alt"], highlightbackground=PALETTE["accent"] if active else PALETTE["border"], highlightthickness=1, padx=14, pady=10)
        row.pack(fill="x", pady=4, padx=2)
        icon_path = (
            world.icon
            if world and world.icon.is_file()
            else resource_path("assets/world_templates/default_icon.png")
            if world
            else resource_path("assets/ui/emoji/no_world.png")
        )
        if icon_path and icon_path.is_file():
            try:
                image = tk.PhotoImage(file=str(icon_path))
                factor = max(1, (max(image.width(), image.height()) + 75) // 76)
                image = image.subsample(factor, factor)
                window.images.append(image)
                tk.Label(row, image=image, bg=PALETTE["surface_alt"]).pack(side="left", padx=(0, 14))
            except tk.TclError:
                _fallback_icon(row, name).pack(side="left", padx=(0, 14))
        else:
            _fallback_icon(row, name).pack(side="left", padx=(0, 14))
        text = tk.Frame(row, bg=PALETTE["surface_alt"])
        text.pack(side="left", fill="x", expand=True)
        tk.Label(text, text=name, bg=PALETTE["surface_alt"], fg=PALETTE["text"], font=(GUI_FONT_SEMIBOLD, 12)).pack(anchor="w")
        tk.Label(text, text="Datapacks désactivés" if not world else world.path.name, bg=PALETTE["surface_alt"], fg=PALETTE["muted"], font=(GUI_FONT, 9)).pack(anchor="w", pady=(3, 0))
        create_button(row, "Choisir", lambda value="" if not world else name: choose(value), variant="secondary").pack(side="right")

    add_world(None)
    for item in _worlds(modpack):
        add_world(item)

    def create_world():
        world = _create_world(modpack, window)
        if world:
            choose(world.name)

    actions = tk.Frame(card, bg=PALETTE["surface"])
    actions.grid(row=3, column=0, pady=(14, 0))
    create_button(actions, "Créer un monde", create_world, variant="secondary").grid(row=0, column=0, padx=6)
    create_button(actions, "Fermer", window.destroy, variant="secondary").grid(row=0, column=1, padx=6)


def open_settings(root, modpack: CatalogEntry, options: dict, on_save):
    window = tk.Toplevel(root)
    window.title(f"Réglages — {modpack.name}")
    window.configure(bg=PALETTE["bg"])
    window.transient(root)
    window.grab_set()
    center_window(window, root, 620, 560)
    window.minsize(480, 420)
    shell = RoundedPanel(window, PALETTE["surface"], radius=8, border=PALETTE["border"])
    shell.pack(fill="both", expand=True, padx=18, pady=18)
    host = shell.content
    host.grid_rowconfigure(0, weight=1)
    host.grid_columnconfigure(0, weight=1)
    viewport = tk.Canvas(host, bg=PALETTE["surface"], bd=0, highlightthickness=0)
    scrollbar = SmoothScrollbar(host, viewport.yview)
    viewport.configure(yscrollcommand=scrollbar.set)
    viewport.grid(row=0, column=0, sticky="nsew")
    card = tk.Frame(viewport, bg=PALETTE["surface"])
    card_window = viewport.create_window(0, 0, anchor="nw", window=card)
    card.config(padx=26, pady=22)
    card.grid_columnconfigure(0, weight=1)
    def update_scrollbar():
        viewport.configure(scrollregion=viewport.bbox("all"))
        needs_scroll = card.winfo_reqheight() > viewport.winfo_height()
        if needs_scroll:
            scrollbar.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        else:
            scrollbar.grid_remove()
            viewport.yview_moveto(0)

    card.bind("<Configure>", lambda _event: viewport.after_idle(update_scrollbar))
    viewport.bind("<Configure>", lambda event: (viewport.itemconfigure(card_window, width=event.width), viewport.after_idle(update_scrollbar)))
    viewport.bind_all("<MouseWheel>", lambda event: viewport.yview_scroll(-1 if event.delta > 0 else 1, "units"))
    window.bind("<Destroy>", lambda _event: viewport.unbind_all("<MouseWheel>"), add="+")
    safe = tk.BooleanVar(value=options.get("safe_mode", False))
    resources = tk.BooleanVar(value=options.get("activate_resourcepacks", True))
    shader = tk.BooleanVar(value=options.get("activate_shader", True))
    selected_world = tk.StringVar(value=options.get("datapack_world", ""))
    total_ram = get_total_ram_gb()
    minimum_ram, maximum_ram = get_ram_limits()
    recommended_ram = get_recommended_ram_gb(modpack.recommended_ram_ratio)
    selected_ram = max(minimum_ram, min(maximum_ram, int(options.get("ram_gb", recommended_ram))))
    ram = tk.IntVar(value=selected_ram)
    tk.Label(card, text="Réglages d'installation", bg=PALETTE["surface"], fg=PALETTE["text"], font=(GUI_FONT_SEMIBOLD, 22)).grid(row=0, column=0, sticky="w")
    tk.Label(card, text="Personnalise le contenu avant de lancer l'installation.", bg=PALETTE["surface"], fg=PALETTE["muted"], font=(GUI_FONT, 10)).grid(row=1, column=0, sticky="w", pady=(5, 16))
    box = RoundedPanel(card, PALETTE["surface_alt"], radius=8, border=PALETTE["border"], height=186)
    box.grid(row=2, column=0, sticky="ew")
    settings = box.content
    settings.config(padx=18, pady=12)
    settings.grid_columnconfigure(0, weight=1)
    for row, (text, variable) in enumerate((("Packs de ressources", resources), ("Shader au lancement", shader), ("Safemode", safe))):
        Switch(settings, text, variable).grid(row=row, column=0, sticky="ew")
    ram_box = RoundedPanel(card, PALETTE["surface_alt"], radius=8, border=PALETTE["border"], height=140)
    ram_box.grid(row=3, column=0, sticky="ew", pady=(14, 0))
    ram_row = ram_box.content
    ram_row.config(padx=18, pady=12)
    ram_row.grid_columnconfigure(0, weight=1)
    tk.Label(ram_row, text="MÉMOIRE ALLOUÉE", bg=PALETTE["surface_alt"], fg=PALETTE["muted"], font=(GUI_FONT_SEMIBOLD, 9)).grid(row=0, column=0, sticky="w")
    ram_value = tk.Label(ram_row, text=f"{ram.get()} Go", bg=PALETTE["surface_alt"], fg=PALETTE["button_disabled_text"] if minimum_ram == maximum_ram else PALETTE["accent"], font=(GUI_FONT_SEMIBOLD, 12))
    ram_value.grid(row=0, column=1, sticky="e")
    ram.trace_add("write", lambda *_args: ram_value.config(text=f"{ram.get()} Go"))
    tk.Label(ram_row, text=f"Recommandé : {recommended_ram} Go  •  Minimum : {minimum_ram} Go", bg=PALETTE["surface_alt"], fg=PALETTE["muted"], font=(GUI_FONT, 9)).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))
    RamSlider(ram_row, ram, minimum_ram, maximum_ram).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))
    tk.Label(ram_row, text=f"{minimum_ram} Go", bg=PALETTE["surface_alt"], fg=PALETTE["muted"], font=(GUI_FONT, 8)).grid(row=3, column=0, sticky="w")
    tk.Label(ram_row, text=f"Maximum : {maximum_ram} Go (2 Go réservés au système)", bg=PALETTE["surface_alt"], fg=PALETTE["muted"], font=(GUI_FONT, 8)).grid(row=3, column=1, sticky="e")

    world_box = RoundedPanel(card, PALETTE["surface_alt"], radius=8, border=PALETTE["border"], height=86)
    world_box.grid(row=4, column=0, sticky="ew", pady=(14, 0))
    world_row = world_box.content
    world_row.config(padx=18, pady=12)
    world_row.grid_columnconfigure(0, weight=1)
    tk.Label(world_row, text="MONDE DES DATAPACKS", bg=PALETTE["surface_alt"], fg=PALETTE["muted"], font=(GUI_FONT_SEMIBOLD, 9)).grid(row=0, column=0, sticky="w")
    world_value = tk.Label(world_row, text=options.get("datapack_world") or "Aucun monde", bg=PALETTE["surface_alt"], fg=PALETTE["text"], font=(GUI_FONT, 11))
    world_value.grid(row=1, column=0, sticky="w", pady=(4, 0))

    def set_world(name: str):
        selected_world.set(name)
        world_value.config(text=name or "Aucun monde")
        window.grab_set()

    create_button(world_row, "Choisir", lambda: open_world_selector(window, modpack, selected_world.get(), set_world), variant="secondary").grid(row=0, column=1, rowspan=2, padx=(12, 0))

    def save():
        world = selected_world.get()
        if world:
            installation_dir = modpack.installation_dir or modpack.id
            path = get_minecraft_dir() / INSTALLATIONS_DIR_NAME / installation_dir / "saves" / world
            if not (path / "level.dat").is_file():
                messagebox.showerror("Monde introuvable", f"Le monde '{world}' n'existe plus. Choisis ou crée un monde valide.", parent=window)
                return
        options.update(safe_mode=safe.get(), activate_resourcepacks=resources.get(), activate_shader=shader.get(), datapack_world=selected_world.get(), ram_gb=ram.get())
        on_save()
        window.destroy()

    actions = tk.Frame(card, bg=PALETTE["surface"])
    actions.grid(row=5, column=0, pady=(18, 0))
    create_button(actions, "Enregistrer", save).grid(row=0, column=0, padx=6)
    create_button(actions, "Annuler", window.destroy, variant="secondary").grid(row=0, column=1, padx=6)
