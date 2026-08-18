import base64
import threading
import time
import tkinter as tk
from dataclasses import replace
from tkinter import messagebox

from catalog import CatalogEntry, load_catalog
from config import APP_TITLE, PALETTE, set_color_theme
from inventory import classically_uninstalled_modpacks, installed_modpacks, installed_revisions, installed_sizes
from preferences import load_preferences, save_preferences
from utils.resources import resource_path
from utils.http import get_bytes
from utils.launcher import launch_minecraft_launcher

from .core.state import log_queue
from .core.windows import clear_window_rounding, round_window
from .screens.home import build_home_screen
from .screens.install import InstallationScreen
from .screens.modpacks import build_modpack_screen
from .screens.prepare import open_settings
from .screens.splash import build_splash_screen
from .screens.uninstall import UninstallationScreen, build_uninstall_options_screen


class ThemeButton(tk.Canvas):
    def __init__(self, parent, dark_mode: tk.BooleanVar, command):
        super().__init__(parent, width=34, height=34, bg=PALETTE["bg"], bd=0, highlightthickness=0, cursor="hand2")
        self.dark_mode = dark_mode
        self.command = command
        self.hovered = False
        self.bind("<Button-1>", lambda _event: self.command())
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Configure>", self._draw)
        self._draw()

    def set_background(self, color: str):
        self.configure(bg=color)

    def _enter(self, _event):
        self.hovered = True
        self._draw()

    def _leave(self, _event):
        self.hovered = False
        self._draw()

    def _draw(self, _event=None):
        self.delete("all")
        width = max(34, self.winfo_width())
        height = max(34, self.winfo_height())
        symbol = "☀" if self.dark_mode.get() else "☾"
        if self.dark_mode.get():
            color = PALETTE["text"] if self.hovered else PALETTE["warning"]
        else:
            color = PALETTE["text"] if self.hovered else PALETTE["accent"]
        self.create_text(width / 2, height / 2, text=symbol, fill=color, font=("Segoe UI Symbol", 17))


class InstallerGui:
    def __init__(self, run_func):
        self.run_func = run_func
        self.modpacks = []
        self.logos = {}
        self.detail_logos = {}
        self.loader_logos = {}
        self.install_options = load_preferences()
        dark_theme = self.install_options.get("_dark_theme", True)
        set_color_theme(dark_theme)
        self._bootstrap = None
        self._splash_started = time.monotonic()
        self.root = tk.Tk()
        self.dark_mode = tk.BooleanVar(self.root, value=dark_theme)
        self.root.title(APP_TITLE)
        self.root.configure(bg=PALETTE["bg"])
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.brand_logo = self._photo(file=resource_path("assets/icons/loveball.png"), size=128)
        if self.brand_logo:
            self.root.iconphoto(True, self.brand_logo)
        try:
            self.root.iconbitmap(str(resource_path("assets/icons/loveball.ico")))
        except tk.TclError:
            pass

        self.state = {
            "status": "idle",
            "progress": 0,
            "selected_modpack": None,
        }

        self.install_screen = None
        self.uninstall_func = None
        self.container = tk.Frame(self.root, bg=PALETTE["bg"])
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)
        self.current_view = None
        self.theme_control = None
        self._configure_splash()
        build_splash_screen(self.container, self.brand_logo)
        threading.Thread(target=self._load_bootstrap, daemon=True).start()
        self.root.after(50, self._poll_bootstrap)

    def _center(self, width: int, height: int) -> str:
        x = max(0, (self.root.winfo_screenwidth() - width) // 2)
        y = max(0, (self.root.winfo_screenheight() - height) // 2)
        return f"{width}x{height}+{x}+{y}"

    def _photo(self, data=None, file=None, size: int = 58):
        try:
            image = tk.PhotoImage(data=base64.b64encode(data)) if data else tk.PhotoImage(file=str(file))
            factor = max(1, (max(image.width(), image.height()) + size - 1) // size)
            return image.subsample(factor, factor)
        except (OSError, tk.TclError):
            return None

    def _configure_splash(self):
        self.root.overrideredirect(True)
        self.root.geometry(self._center(520, 320))
        self.root.after_idle(lambda: round_window(self.root, 28))

    def _load_bootstrap(self):
        try:
            packs = load_catalog()
            images = {}
            for pack in packs:
                if not pack.logo:
                    continue
                try:
                    images[pack.id] = get_bytes(pack.logo)
                except Exception:
                    pass
            self._bootstrap = packs, images, None
        except Exception as exc:
            self._bootstrap = [], {}, exc

    def _poll_bootstrap(self):
        if self._bootstrap is None or time.monotonic() - self._splash_started < 1.2:
            self.root.after(50, self._poll_bootstrap)
            return
        packs, images, error = self._bootstrap
        installed = installed_modpacks()
        revisions = installed_revisions()
        sizes = installed_sizes()
        classic_done = classically_uninstalled_modpacks()
        self.modpacks = []
        for pack in packs:
            keys = {pack.id.casefold(), pack.name.casefold()}
            key = next((value for value in keys if value in installed), None)
            status = "Non installé" if key is None else "Réinstallation nécessaire" if keys & classic_done else "Installé" if not pack.revision else "À jour" if revisions.get(key) == pack.revision else "Mise à jour disponible"
            installed_size = next((sizes[value] for value in keys if value in sizes), None)
            size_mb = installed_size / 1024 / 1024 if installed_size is not None else pack.size_mb
            self.modpacks.append(replace(pack, update_status=status, size_mb=size_mb))
        for key, data in images.items():
            try:
                if key.startswith("loader:"):
                    if image := self._photo(data=data, size=30):
                        self.loader_logos[key.removeprefix("loader:")] = image
                    continue
                if image := self._photo(data=data):
                    self.logos[key] = image
                if image := self._photo(data=data, size=128):
                    self.detail_logos[key] = image
            except (OSError, tk.TclError):
                pass
        for pack in self.modpacks:
            local_logo = resource_path(f"assets/modpacks/{pack.id}.png")
            if local_logo.is_file():
                if image := self._photo(file=local_logo):
                    self.logos[pack.id] = image
                if image := self._photo(file=local_logo, size=128):
                    self.detail_logos[pack.id] = image
            if pack.loader not in self.loader_logos:
                local_icon = resource_path(f"assets/loaders/{pack.loader}.png")
                if local_icon.is_file() and (image := self._photo(file=local_icon, size=30)):
                    self.loader_logos[pack.loader] = image
        clear_window_rounding(self.root)
        self.root.overrideredirect(False)
        self._configure_window()
        self._create_theme_control()
        self.show_home()
        if error:
            messagebox.showerror("Catalogue indisponible", str(error), parent=self.root)

    def _configure_window(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = max(960, int(screen_width * 2 / 3))
        height = min(screen_height - 80, max(700, int(screen_height * 0.78)))
        self.root.geometry(self._center(width, height))
        self.root.minsize(900, 600)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

    def run(self):
        self.root.mainloop()

    def clear(self):
        self.install_screen = None
        for child in self.container.winfo_children():
            child.destroy()

    def _create_theme_control(self):
        self.theme_control = ThemeButton(self.root, self.dark_mode, self._toggle_theme_button)
        self._show_theme_control()

    def _show_theme_control(self, on_surface: bool = False):
        if self.theme_control and self.theme_control.winfo_exists():
            self.theme_control.set_background(PALETTE["surface"] if on_surface else PALETTE["bg"])
            if on_surface:
                self.theme_control.place(relx=1, x=-31, y=31, anchor="ne")
            else:
                self.theme_control.place(relx=1, x=-28, y=18, anchor="ne")
            self.theme_control.tk.call("raise", self.theme_control._w)

    def _toggle_theme(self):
        set_color_theme(self.dark_mode.get())
        self.install_options["_dark_theme"] = self.dark_mode.get()
        save_preferences(self.install_options)
        self.root.configure(bg=PALETTE["bg"])
        if self.theme_control:
            self.theme_control.destroy()
        self._create_theme_control()
        if self.current_view:
            self.current_view()

    def _toggle_theme_button(self):
        self.dark_mode.set(not self.dark_mode.get())
        self._toggle_theme()

    def show_home(self):
        self.current_view = self.show_home
        self.state["status"] = "idle"
        self.state["progress"] = 0
        self.clear()
        build_home_screen(
            self.container,
            on_launch=self.show_modpacks,
            on_uninstall=self.show_uninstall_modpacks,
            on_close=self.root.destroy,
            logo=self.brand_logo,
        )
        self._show_theme_control()

    def show_modpacks(self):
        self.current_view = self.show_modpacks
        self.clear()
        build_modpack_screen(
            self.container,
            on_select=self.show_install_details,
            on_back=self.show_home,
            modpacks=self.modpacks,
            logos=self.logos,
        )
        self._show_theme_control()

    def show_install_details(self, modpack: CatalogEntry, _safe_mode: bool = False):
        from utils.system import get_recommended_ram_gb

        self.current_view = lambda: self.show_install_details(modpack)
        self.clear()
        defaults = {
            "safe_mode": False,
            "activate_resourcepacks": True,
            "activate_shader": True,
            "datapack_world": "",
            "ram_gb": get_recommended_ram_gb(modpack.recommended_ram_ratio),
        }
        saved = self.install_options.get(modpack.id)
        options = defaults | saved if isinstance(saved, dict) else defaults
        self.install_options[modpack.id] = options
        self.install_screen = InstallationScreen(
            self.container,
            self.root,
            modpack,
            self.detail_logos.get(modpack.id),
            self.loader_logos.get(modpack.id) or self.loader_logos.get(modpack.loader),
            options,
            on_start=lambda: self.start_install(modpack, options),
            on_settings=lambda: open_settings(self.root, modpack, options, self.save_install_settings),
            on_open_launcher=self.open_launcher,
            on_back=self.show_home,
            on_success=lambda: self.mark_updated(modpack.id, self.install_screen.final_size_mb),
        )
        self.install_screen.render()
        self._show_theme_control(on_surface=True)

    def save_install_settings(self):
        save_preferences(self.install_options)
        if self.install_screen:
            self.install_screen.refresh_options()

    def mark_updated(self, modpack_id: str, size_mb: float | None = None):
        self.modpacks = [
            replace(pack, update_status="À jour", size_mb=size_mb if size_mb is not None else pack.size_mb)
            if pack.id == modpack_id else pack
            for pack in self.modpacks
        ]

    def show_uninstall_modpacks(self):
        self.current_view = self.show_uninstall_modpacks
        self.clear()
        installed = installed_modpacks()
        packs = [
            pack for pack in self.modpacks
            if {pack.id.casefold(), pack.name.casefold()} & installed
        ]
        build_modpack_screen(
            self.container,
            on_select=lambda modpack, _safe_mode=False: self.show_uninstall_options(modpack),
            on_back=self.show_home,
            modpacks=packs,
            logos=self.logos,
            title_text="Désinstaller un modpack",
            install_mode=False,
        )
        self._show_theme_control()

    def show_uninstall_options(self, modpack: CatalogEntry):
        self.current_view = lambda: self.show_uninstall_options(modpack)
        self.state["selected_modpack"] = modpack.id
        self.clear()
        classic_done = classically_uninstalled_modpacks()
        keys = {modpack.id.casefold(), modpack.name.casefold()}
        build_uninstall_options_screen(
            self.container,
            modpack.name,
            on_select=lambda mode: self.start_uninstall(modpack, mode),
            on_back=self.show_uninstall_modpacks,
            classic_available=not keys & classic_done,
        )
        self._show_theme_control()

    def start_install(self, modpack: CatalogEntry, options: dict):
        if self.theme_control:
            self.theme_control.place_forget()
        self.state["selected_modpack"] = modpack.id
        run_options = dict(options, revision=modpack.revision)
        self.state["options"] = run_options
        self.state["status"] = "running"
        self.state["progress"] = 0

        while not log_queue.empty():
            log_queue.get()

        self.install_screen.start(self.state)
        self.install_screen.process_logs()

        threading.Thread(target=self.run_install, args=(modpack, run_options), daemon=True).start()

    def start_uninstall(self, modpack: CatalogEntry, mode):
        if self.theme_control:
            self.theme_control.place_forget()
        if getattr(mode, "value", mode) == "full":
            confirmed = messagebox.askyesno(
                "Confirmer la désinstallation",
                "Cette option supprime entièrement le dossier du modpack, sauvegardes et réglages inclus.\n\n"
                "Continuer ?",
                parent=self.root,
            )
            if not confirmed:
                return

        self.state["selected_modpack"] = modpack.id
        self.state["status"] = "running"
        self.state["progress"] = 0

        while not log_queue.empty():
            log_queue.get()

        self.clear()
        self.install_screen = UninstallationScreen(
            self.container,
            self.root,
            self.state,
            modpack.name,
            on_back=self.show_home,
        )
        self.install_screen.render()
        self.install_screen.process_logs()

        threading.Thread(target=self.run_uninstall, args=(modpack, mode), daemon=True).start()

    def run_install(self, modpack: CatalogEntry, options: dict):
        try:
            self.run_func(modpack, options)
            log_queue.put(("done", "success"))
        except Exception as exc:
            log_queue.put(("log", f"Erreur: {exc}", "fatal"))
            log_queue.put(("done", "error"))

    def run_uninstall(self, modpack: CatalogEntry, mode):
        try:
            self.uninstall_func(modpack, mode)
            log_queue.put(("done", "success"))
        except Exception as exc:
            log_queue.put(("log", f"Erreur: {exc}", "fatal"))
            log_queue.put(("done", "error"))

    def open_launcher(self):
        if self.state["status"] != "success":
            return

        self.root.destroy()
        launch_minecraft_launcher()


def start_gui(run_func, uninstall_func=None):
    gui = InstallerGui(run_func)
    gui.uninstall_func = uninstall_func
    gui.run()
