import os
import io
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog

from PIL import Image, ImageDraw, ImageTk

from config import CACHE_DIR_NAME, GUI_FONT, GUI_FONT_SEMIBOLD, INSTALLATIONS_DIR_NAME, PALETTE, get_minecraft_dir
from gui.components import RoundedPanel, RoundedProgress, SmoothScrollbar, create_button
from gui.core.state import log_queue
from utils.resources import resource_path


class PackChoiceCard(tk.Canvas):
    def __init__(self, parent, title, subtitle, value, preview_path, variable, command):
        super().__init__(parent, height=92, bg=parent.cget("bg"), bd=0, highlightthickness=0, cursor="hand2")
        self.title, self.subtitle, self.value = title, subtitle, value
        self.preview_path, self.variable, self.command = preview_path, variable, command
        self.hovered = False
        self.bind("<Button-1>", self._select)
        self.bind("<Enter>", lambda _event: self._set_hover(True))
        self.bind("<Leave>", lambda _event: self._set_hover(False))
        self.bind("<Configure>", self._draw)

    def _select(self, _event=None):
        self.variable.set(self.value)
        self.command()

    def _set_hover(self, value):
        self.hovered = value
        self._draw()

    def _draw(self, _event=None):
        width, height, scale = max(260, self.winfo_width()), 92, 4
        selected = self.variable.get() == self.value
        image = Image.new("RGB", (width * scale, height * scale), self.cget("bg"))
        draw = ImageDraw.Draw(image)
        border = PALETTE["accent"] if selected else PALETTE["button_alt_hover"] if self.hovered else PALETTE["border"]
        fill = PALETTE["button_alt"] if selected or self.hovered else PALETTE["surface_alt"]
        draw.rounded_rectangle((2 * scale, 2 * scale, (width - 3) * scale, (height - 3) * scale), radius=13 * scale, fill=fill, outline=border, width=(2 if selected else 1) * scale)

        size, left, top = 66 * scale, 14 * scale, 13 * scale
        try:
            source = io.BytesIO(self.preview_path) if isinstance(self.preview_path, bytes) else self.preview_path
            preview = Image.open(source).convert("RGB")
            side = min(preview.size)
            x, y = (preview.width - side) // 2, (preview.height - side) // 2
            preview = preview.crop((x, y, x + side, y + side)).resize((size, size), Image.Resampling.LANCZOS)
            mask = Image.new("L", (size, size), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=9 * scale, fill=255)
            image.paste(preview, (left, top), mask)
        except (OSError, ValueError):
            draw.rounded_rectangle((left, top, left + size, top + size), radius=9 * scale, fill=PALETTE["button_disabled"])

        cx, cy, radius = (width - 22) * scale, (height // 2) * scale, 10 * scale
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=PALETTE["accent"] if selected else PALETTE["surface"], outline=PALETTE["accent"] if selected else PALETTE["muted"], width=2 * scale)
        if selected:
            draw.line(((cx - 5 * scale, cy), (cx - scale, cy + 4 * scale), (cx + 6 * scale, cy - 5 * scale)), fill="#ffffff", width=2 * scale, joint="curve")

        image = image.resize((width, height), Image.Resampling.LANCZOS)
        self._surface = ImageTk.PhotoImage(image, master=self)
        self.delete("all")
        self.create_image(0, 0, image=self._surface, anchor="nw")
        self.create_text(94, 34, text=self.title, fill=PALETTE["text"], font=(GUI_FONT_SEMIBOLD, 11), anchor="w")
        self.create_text(94, 57, text=self.subtitle, fill=PALETTE["muted"], font=(GUI_FONT, 9), anchor="w")


def _mb(value: int) -> float:
    return value / 1024 / 1024


class InstallationScreen:
    def __init__(self, parent, root, modpack, logo, loader_logo, options, on_start, on_settings, on_open_launcher, on_back, on_success, on_options_changed=None, profiles=None, profile_logos=None):
        self.parent = parent
        self.root = root
        self.modpack = modpack
        self.logo = logo
        self.loader_logo = loader_logo
        self.options = options
        self.on_start = on_start
        self.on_settings = on_settings
        self.on_open_launcher = on_open_launcher
        self.on_back = on_back
        self.on_success = on_success
        self.on_options_changed = on_options_changed
        self.profiles = profiles
        self.profile_logos = profile_logos or {}
        self.state = None
        self.screen = None
        self.downloads = {}
        self.error = ""
        self.log_path = None
        self.log_lines = []
        self.log_window = None
        self.log_text = None
        self.active_stage = None
        self.emoji_images = {}
        self.world_icon = None
        self.pack_preview_images = []
        self.total_size_mb = modpack.size_mb
        self.final_size_mb = None

    def _load_emoji_images(self):
        names = ("pending", "success", "error", "skipped", "validate", "java", "loader_neoforge", "loader_fabric", "profile", "mods", "resourcepacks", "shaders", "datapacks", "configs", "activate", "enabled", "disabled")
        for name in names:
            try:
                image = tk.PhotoImage(file=str(resource_path(f"assets/ui/emoji/{name}.png")))
                self.emoji_images[name] = image if name in {"enabled", "disabled"} else image.subsample(3, 3)
            except (OSError, tk.TclError):
                self.emoji_images[name] = None

    def render(self):
        self._load_emoji_images()
        self.screen = tk.Frame(self.parent, bg=PALETTE["bg"])
        self.screen.grid(row=0, column=0, sticky="nsew")
        self.screen.grid_rowconfigure(0, weight=1)
        self.screen.grid_columnconfigure(0, weight=1)
        viewport = tk.Canvas(self.screen, bg=PALETTE["bg"], bd=0, highlightthickness=0)
        scrollbar = SmoothScrollbar(self.screen, viewport.yview)
        viewport.configure(yscrollcommand=scrollbar.set)
        viewport.grid(row=0, column=0, sticky="nsew")
        self.viewport = viewport
        holder = tk.Frame(viewport, bg=PALETTE["bg"])
        self.viewport_holder = holder
        holder.grid_columnconfigure(0, weight=1)
        holder_window = viewport.create_window(0, 0, anchor="nw", window=holder)
        has_declared_profiles = bool(self.profiles and self.profiles.profiles)
        profile_count = len(self.profiles.profiles) if has_declared_profiles else (2 if self.modpack.id == "cozy_adventure" else 0)
        profile_rows = (profile_count + 1) // 2
        base_shell_height = 780 + profile_rows * 106 if profile_count else 730
        self.stage_extra_height = 0
        shell = RoundedPanel(holder, PALETTE["surface"], radius=8, border=PALETTE["border"], height=base_shell_height)
        self.shell = shell
        shell.grid(row=0, column=0, sticky="ew", padx=24, pady=24)

        def resize_shell(viewport_height=None):
            available = (viewport_height if viewport_height is not None else viewport.winfo_height()) - 48
            shell.configure(height=max(base_shell_height + self.stage_extra_height, available))

        self.resize_shell = resize_shell

        def update_scrollbar():
            viewport.configure(scrollregion=viewport.bbox("all"))
            if holder.winfo_reqheight() > viewport.winfo_height():
                scrollbar.grid(row=0, column=1, sticky="ns")
            else:
                scrollbar.grid_remove()
                viewport.yview_moveto(0)

        holder.bind("<Configure>", lambda _event: viewport.after_idle(update_scrollbar))
        viewport.bind("<Configure>", lambda event: (viewport.itemconfigure(holder_window, width=event.width), resize_shell(event.height), viewport.after_idle(update_scrollbar)))

        def scroll(event):
            if viewport.winfo_exists():
                viewport.yview_scroll(-max(1, abs(event.delta) // 120) if event.delta > 0 else max(1, abs(event.delta) // 120), "units")

        self.root.bind("<MouseWheel>", scroll)
        card = shell.content
        card.config(padx=34, pady=28)
        card.grid_columnconfigure(0, weight=1)
        header = tk.Frame(card, bg=PALETTE["surface"])
        header.grid(row=0, column=0)
        brand = tk.Frame(header, bg=PALETTE["surface"])
        brand.grid(row=0, column=0)
        if self.logo:
            tk.Label(brand, image=self.logo, bg=PALETTE["surface"]).grid(row=0, column=0, rowspan=2, padx=(0, 24))
        tk.Label(brand, text=self.modpack.name, bg=PALETTE["surface"], fg=PALETTE["text"], font=(GUI_FONT_SEMIBOLD, 30)).grid(row=0, column=1, sticky="sw")
        tk.Label(brand, text=self.modpack.description, bg=PALETTE["surface"], fg=PALETTE["muted"], font=(GUI_FONT, 11), wraplength=760, justify="left").grid(row=1, column=1, sticky="nw", pady=(6, 0))
        info_panel = RoundedPanel(card, PALETTE["surface_alt"], radius=8, border=PALETTE["border"], height=290 + profile_rows * 106 if profile_count else 238)
        info_panel.grid(row=1, column=0, sticky="ew", pady=(24, 18))
        info = info_panel.content
        info.config(padx=18, pady=12)
        size = f"{self.total_size_mb:.1f} Mo" if self.total_size_mb is not None else "Indisponible"
        values = (("TAILLE", size), ("LANCEUR", self.modpack.loader.title()), ("MINECRAFT", self.modpack.minecraft_version), ("ÉTAT", self.modpack.update_status))
        for column, (label, value) in enumerate(values):
            info.grid_columnconfigure(column, weight=1)
            tk.Label(info, text=label, bg=PALETTE["surface_alt"], fg=PALETTE["muted"], font=(GUI_FONT_SEMIBOLD, 9)).grid(row=0, column=column)
            value_row = tk.Frame(info, bg=PALETTE["surface_alt"])
            value_row.grid(row=1, column=column, pady=(4, 0))
            if label == "LANCEUR" and self.loader_logo:
                tk.Label(value_row, image=self.loader_logo, bg=PALETTE["surface_alt"]).pack(side="left", padx=(0, 7))
            color = self._status_color(value) if label == "ÉTAT" else PALETTE["text"]
            value_label = tk.Label(value_row, text=value, bg=PALETTE["surface_alt"], fg=color, font=(GUI_FONT_SEMIBOLD, 11))
            value_label.pack(side="left")
            if label == "TAILLE":
                self.size_value = value_label
        tk.Frame(info, bg=PALETTE["border"], height=1).grid(row=2, column=0, columnspan=4, sticky="ew", pady=(14, 10))
        tk.Label(info, text="Configuration", bg=PALETTE["surface_alt"], fg=PALETTE["text"], font=(GUI_FONT_SEMIBOLD, 13)).grid(row=3, column=0, columnspan=4, sticky="w", pady=(0, 8))
        self.option_values = {}
        options_panel = RoundedPanel(info, PALETTE["surface_alt"], radius=7, border=PALETTE["border"], height=82)
        options_panel.grid(row=4, column=0, columnspan=4, sticky="ew")
        options_row = options_panel.content
        options_row.config(padx=10, pady=8)
        option_labels = (("resourcepacks", "PACKS DE RESSOURCES"), ("shader", "SHADER"), ("datapacks", "DATAPACKS"), ("safe_mode", "SAFEMODE"))
        for column, (key, label) in enumerate(option_labels):
            options_row.grid_columnconfigure(column, weight=1)
            cell = tk.Frame(options_row, bg=PALETTE["surface_alt"])
            cell.grid(row=0, column=column, sticky="nsew")
            cell.grid_columnconfigure(0, weight=1)
            tk.Label(cell, text=label, bg=PALETTE["surface_alt"], fg=PALETTE["muted"], font=(GUI_FONT_SEMIBOLD, 9), anchor="center").grid(row=0, column=0, sticky="ew")
            value = tk.Label(cell, bg=PALETTE["surface_alt"], fg=PALETTE["text"], font=(GUI_FONT, 10), anchor="center")
            value.grid(row=1, column=0, sticky="ew", pady=(5, 0))
            self.option_values[key] = value
        if profile_count:
            interface_row = tk.Frame(info, bg=PALETTE["surface_alt"])
            interface_row.grid(row=5, column=0, columnspan=4, sticky="ew", pady=(12, 0))
            tk.Label(interface_row, text="PROFIL VISUEL", bg=PALETTE["surface_alt"], fg=PALETTE["muted"], font=(GUI_FONT_SEMIBOLD, 9)).grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(0, 7))
            fallback = self.profiles.default if has_declared_profiles else "flowery"
            self.interface_pack_var = tk.StringVar(value=self.options.get("visual_profile", self.options.get("interface_pack", fallback)))
            self.pack_choice_cards = []
            declared = [
                (profile.name, f"{len(profile.resourcepacks)} pack(s)" + (" · shader inclus" if profile.shader else ""), profile.id, self.profile_logos.get(profile.id))
                for profile in self.profiles.profiles
            ] if has_declared_profiles else [
                ("Flowery", "Packs fleuris", "flowery", resource_path("assets/resourcepacks/flowery.png")),
                ("Simple Hotbar", "Interface épurée", "simple_hotbar", resource_path("assets/resourcepacks/simple_hotbar.png")),
            ]
            for column in range(4):
                interface_row.grid_columnconfigure(column, weight=1, uniform="pack-choice")
            for index, (title, subtitle, value, preview) in enumerate(declared):
                row = 1 + index // 2
                column = 1 if len(declared) % 2 and index == len(declared) - 1 else (index % 2) * 2
                choice = PackChoiceCard(
                    interface_row, title, subtitle, value, preview or "",
                    self.interface_pack_var, self._change_interface_pack,
                )
                choice.grid(row=row, column=column, columnspan=2, sticky="ew", padx=6, pady=(0, 8))
                self.pack_choice_cards.append(choice)
        progress_panel = RoundedPanel(card, PALETTE["surface_alt"], radius=8, border=PALETTE["border"], height=180)
        self.progress_panel = progress_panel
        progress_panel.grid(row=2, column=0, sticky="ew")
        progress = progress_panel.content
        progress.config(padx=24, pady=20)
        progress.grid_columnconfigure(0, weight=1)
        tk.Label(progress, text="Progression", bg=PALETTE["surface_alt"], fg=PALETTE["text"], font=(GUI_FONT_SEMIBOLD, 15)).grid(row=0, column=0, sticky="w")
        self.status = tk.Label(progress, text="Prêt à installer", bg=PALETTE["surface_alt"], fg=PALETTE["text"], font=(GUI_FONT_SEMIBOLD, 12), anchor="w")
        checklist = tk.Frame(progress, bg=PALETTE["surface_alt"])
        checklist.grid(row=1, column=0, sticky="ew", pady=(10, 8))
        checklist.grid_columnconfigure(0, weight=1)
        self.checklist = checklist
        self.stage_labels = {}
        self.stage_state_icons = {}
        self.stage_texts = {}
        self.stage_row = 0
        self.stage_names = {
            "validate": "Validation des manifests", "java": "Vérification de Java",
            "loader": f"Vérification de {self.modpack.loader.title()}",
            "profile": "Préparation du profil Minecraft", "mods": "Synchronisation des mods",
            "resourcepacks": "Synchronisation des packs de ressources",
            "shaders": "Synchronisation des shaders", "datapacks": "Synchronisation des datapacks",
            "configs": "Synchronisation des configs", "activate": "Activation des packs",
        }
        self.current = tk.Label(progress, text="Aucun téléchargement en cours", bg=PALETTE["surface_alt"], fg=PALETTE["muted"], font=(GUI_FONT, 10), anchor="w")
        self.progress_bar = RoundedProgress(progress, show_bytes=True, height=26)
        self.progress_bar.grid(row=2, column=0, sticky="ew", pady=(8, 14))
        self.progress_bar.set(0, 0, self.total_size_mb)
        self.message = tk.Label(progress, text="Vérifie les réglages puis lance l'installation.", bg=PALETTE["surface_alt"], fg=PALETTE["muted"], font=(GUI_FONT, 10), wraplength=520, justify="left")
        self.message.grid(row=3, column=0, sticky="w")
        self.actions = tk.Frame(card, bg=PALETTE["surface"])
        self.actions.grid(row=3, column=0, pady=(18, 0))
        self.install = create_button(self.actions, "Installer", self.on_start)
        self.settings = create_button(self.actions, "Réglages", self.on_settings, variant="secondary")
        self.logs = create_button(self.actions, "Logs", self.open_logs, variant="secondary")
        self.back = create_button(self.actions, "Retour", self.on_back, variant="secondary")
        self.launch = create_button(self.actions, "Lancer Minecraft", self.on_open_launcher)
        self.export = create_button(self.actions, "Télécharger le journal", self.export_log, variant="secondary")
        self.install.grid(row=0, column=0, padx=6)
        self.settings.grid(row=0, column=1, padx=6)
        self.logs.grid(row=0, column=2, padx=6)
        self.back.grid(row=0, column=3, padx=6)
        self.refresh_options()
        def initialize_scroll():
            self.root.update_idletasks()
            viewport.itemconfigure(holder_window, width=viewport.winfo_width())
            viewport.configure(scrollregion=(0, 0, viewport.winfo_width(), holder.winfo_reqheight()))
            update_scrollbar()

        self.root.after_idle(initialize_scroll)
        self.root.after(50, initialize_scroll)
        self.root.after(250, initialize_scroll)

    def refresh_options(self):
        if not hasattr(self, "option_values"):
            return
        world = self.options.get("datapack_world") or "Aucun monde"
        booleans = {
            "safe_mode": self.options.get("safe_mode", False),
            "resourcepacks": self.options.get("activate_resourcepacks", True),
            "shader": self.options.get("activate_shader", True),
        }
        for key, value in booleans.items():
            image = self.emoji_images["enabled" if value else "disabled"]
            self.option_values[key].config(text="", image=image, compound="center")

        self.world_icon = None
        if world != "Aucun monde":
            installation_dir = self.modpack.installation_dir or self.modpack.id
            icon_path = get_minecraft_dir() / INSTALLATIONS_DIR_NAME / installation_dir / "saves" / world / "icon.png"
            if icon_path.is_file():
                try:
                    image = tk.PhotoImage(file=str(icon_path))
                    factor = max(1, (max(image.width(), image.height()) + 35) // 36)
                    self.world_icon = image.subsample(factor, factor)
                except (OSError, tk.TclError):
                    pass
        self.option_values["datapacks"].config(text=world, image=self.world_icon or "", compound="left", padx=6)
        if hasattr(self, "interface_pack_var"):
            self.interface_pack_var.set(self.options.get("visual_profile", self.options.get("interface_pack", "flowery")))

    def _change_interface_pack(self):
        self.options["visual_profile"] = self.interface_pack_var.get()
        self.options.pop("interface_pack", None)
        for card in getattr(self, "pack_choice_cards", []):
            card._draw()
        if self.on_options_changed:
            self.on_options_changed()

    @staticmethod
    def _status_color(status: str):
        normalized = status.casefold()
        if "à jour" in normalized or normalized == "installé":
            return PALETTE["success"]
        if "mise à jour" in normalized or "réinstallation" in normalized:
            return PALETTE["error"]
        if "impossible" in normalized:
            return PALETTE["warning"]
        return PALETTE["text"]

    def start(self, state):
        self.state = state
        self.downloads.clear()
        self.log_lines.clear()
        self.error = ""
        root_path = Path(os.getenv("LOCALAPPDATA") or Path.cwd()) / CACHE_DIR_NAME / "logs"
        root_path.mkdir(parents=True, exist_ok=True)
        self.log_path = root_path / f"installation-{datetime.now():%Y%m%d-%H%M%S}.log"
        for button in (self.install, self.settings, self.back):
            button.config(state="disabled", cursor="")
        self.status.config(text="Préparation de l'installation...", fg=PALETTE["text"])
        self.message.config(text="Le lanceur restera fermé jusqu'à la fin.", fg=PALETTE["muted"])
        self.root.after_idle(self._scroll_to_progress)
        self.root.after(180, self._scroll_to_progress)

    def _scroll_to_progress(self):
        if not self.screen or not self.screen.winfo_exists():
            return
        self.root.update_idletasks()
        bbox = self.viewport.bbox("all")
        if not bbox or bbox[3] <= self.viewport.winfo_height():
            return
        bar_bottom = self.progress_bar.winfo_rooty() - self.viewport_holder.winfo_rooty() + self.progress_bar.winfo_height()
        target = max(0, bar_bottom - self.viewport.winfo_height() + 90)
        self.viewport.yview_moveto(min(1.0, target / bbox[3]))

    def _write(self, text: str):
        self.log_lines.append(text)
        if self.log_text and self.log_text.winfo_exists():
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, text + "\n")
            self.log_text.config(state="disabled")
            self.log_text.see(tk.END)
        if self.log_path:
            with self.log_path.open("a", encoding="utf-8") as file:
                file.write(text + "\n")

    def set_progress(self, value):
        value = max(0, min(100, int(value)))
        self.state["progress"] = value
        if value == 100 and self.final_size_mb is not None:
            self.progress_bar.set(value, self.final_size_mb, self.final_size_mb)
        else:
            self.progress_bar.set(value)

    def set_download(self, name: str, received: int, total: int | None):
        self.downloads[name] = received, total
        current = sum(value[0] for value in self.downloads.values())
        total = self.total_size_mb
        if self.active_stage in self.stage_labels:
            base = self.stage_texts[self.active_stage]
            self.stage_labels[self.active_stage].config(text=f"{base}\nTéléchargement de : {name}")
        self.progress_bar.set(self.state.get("progress", 0), _mb(current), total)

    def set_stage(self, text: str, icon: str = ""):
        label = text.removesuffix("...")
        self.status.config(text="Installation en cours", fg=PALETTE["text"])

    def set_stage_active(self, key: str, text: str):
        self.active_stage = key
        self.set_stage(text)
        base = self.stage_names.get(key, text.removesuffix("..."))
        self.stage_texts[key] = base
        if key not in self.stage_labels:
            row = tk.Frame(self.checklist, bg=PALETTE["surface_alt"])
            row.grid(row=self.stage_row, column=0, sticky="ew", pady=4)
            row.grid_columnconfigure(2, weight=1)
            state_icon = tk.Label(row, image=self.emoji_images["pending"], bg=PALETTE["surface_alt"])
            state_icon.grid(row=0, column=0, sticky="n", padx=(0, 8))
            image_key = f"loader_{self.modpack.loader}" if key == "loader" else key
            tk.Label(row, image=self.emoji_images.get(image_key), bg=PALETTE["surface_alt"]).grid(row=0, column=1, sticky="n", padx=(0, 8))
            label = tk.Label(row, text=base, bg=PALETTE["surface_alt"], fg=PALETTE["accent"], font=(GUI_FONT, 11), anchor="w", justify="left")
            label.grid(row=0, column=2, sticky="ew")
            self.stage_labels[key] = label
            self.stage_state_icons[key] = state_icon
            self.stage_row += 1
            extra_height = self.stage_row * 38
            self.stage_extra_height = extra_height
            self.progress_panel.configure(height=180 + extra_height)
            self.resize_shell()
            self.root.update_idletasks()
            self.root.after_idle(self._scroll_to_progress)

    def set_stage_done(self, key: str, text: str):
        if key in self.stage_labels:
            self.stage_state_icons[key].config(image=self.emoji_images["success"])
            self.stage_labels[key].config(text=text.strip(), fg=PALETTE["success"])
        self._write(text)

    def set_stage_skipped(self, key: str, text: str):
        if key in self.stage_labels:
            self.stage_state_icons[key].config(image=self.emoji_images["skipped"])
            self.stage_labels[key].config(text=text.strip(), fg=PALETTE["warning"])
        self._write(text)

    def set_stage_error(self, message: str):
        key = self.active_stage
        if key in self.stage_labels:
            self.stage_state_icons[key].config(image=self.emoji_images["error"])
            self.stage_labels[key].config(text=f"{self.stage_texts[key]}\nErreur : {message}", fg=PALETTE["error"])

    def process_logs(self):
        while not log_queue.empty():
            data = log_queue.get()
            if data[0] == "progress":
                self.set_progress(data[1])
            elif data[0] == "stage":
                self.set_stage_active(data[1], data[2])
                self._write(data[2])
            elif data[0] == "stage_done":
                self.set_stage_done(data[1], data[2])
            elif data[0] == "stage_skipped":
                self.set_stage_skipped(data[1], data[2])
            elif data[0] == "download":
                self.set_download(data[1], data[2], data[3])
            elif data[0] == "size_total":
                self.final_size_mb = data[1] / 1024 / 1024
                self.total_size_mb = self.final_size_mb
                self.size_value.config(text=f"{self.final_size_mb:.1f} Mo")
                self.progress_bar.set(self.state.get("progress", 0), total=self.final_size_mb)
            elif data[0] == "log":
                self._write(data[1])
                if data[2] == "fatal":
                    self.error = data[1]
                    self.set_stage_error(data[1].removeprefix("Erreur: "))
            elif data[0] == "done":
                self.finish(data[1] == "success")
        if self.screen and self.screen.winfo_exists() and self.state["status"] == "running":
            self.root.after(50, self.process_logs)

    def finish(self, success: bool):
        self.state["status"] = "success" if success else "error"
        for button in (self.install, self.settings, self.back):
            button.grid_remove()
        if success:
            self.on_success()
            self.set_progress(100)
            self.status.config(text="Installation terminée", fg=PALETTE["success"])
            self.message.config(text="Le modpack peut maintenant être lancé.", fg=PALETTE["success"])
            self.launch.grid(row=0, column=0, padx=6)
        else:
            self.status.config(text="Installation échouée", fg=PALETTE["error"])
            self.message.config(text=self.error or "Une erreur est survenue.", fg=PALETTE["error"])
            self.set_stage_error((self.error or "Une erreur est survenue.").removeprefix("Erreur: "))
            self.export.grid(row=0, column=0, padx=6)
            self.root.after(100, self.open_logs)
        self.back.config(state="normal", cursor="hand2")
        self.back.grid(row=0, column=1, padx=6)
        self._write("Installation terminée." if success else "Installation échouée.")

    def open_logs(self):
        if self.log_window and self.log_window.winfo_exists():
            self.log_window.lift()
            return
        window = tk.Toplevel(self.root)
        self.log_window = window
        window.title("Logs d'installation")
        window.configure(bg=PALETTE["bg"])
        window.geometry("760x480")
        window.minsize(520, 320)
        body = tk.Frame(window, bg=PALETTE["surface"], padx=16, pady=16)
        body.pack(fill="both", expand=True, padx=14, pady=14)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)
        text = tk.Text(body, wrap="word", bg=PALETTE["log_bg"], fg=PALETTE["text"], insertbackground=PALETTE["text"], relief="flat", padx=12, pady=12, font=("Cascadia Mono", 9))
        self.log_text = text
        scrollbar = SmoothScrollbar(body, text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        text.insert("1.0", "\n".join(self.log_lines))
        text.config(state="disabled")
        actions = tk.Frame(body, bg=PALETTE["surface"])
        actions.grid(row=1, column=0, columnspan=2, pady=(12, 0))
        create_button(actions, "Télécharger log.txt", self.export_log, variant="secondary").pack(side="left", padx=5)
        create_button(actions, "Fermer", window.destroy, variant="secondary").pack(side="left", padx=5)
        window.protocol("WM_DELETE_WINDOW", window.destroy)

    def export_log(self):
        target = filedialog.asksaveasfilename(parent=self.root, title="Enregistrer le journal", initialfile="log.txt", defaultextension=".txt", filetypes=(("Journal texte", "*.txt"), ("Journal", "*.log")))
        if target:
            Path(target).write_text("\n".join(self.log_lines) + "\n", encoding="utf-8")
