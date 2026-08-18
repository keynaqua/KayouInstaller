import tkinter as tk

from config import GUI_FONT, GUI_FONT_SEMIBOLD, PALETTE
from gui.components import RoundedProgress, create_button
from gui.core.state import log_queue
from uninstall import UninstallMode


CLASSIC_DESCRIPTION = (
    "Supprime les mods, packs de ressources et shaders déclarés dans les manifestes. "
    "Les sauvegardes, options, journaux et configurations restent dans le dossier."
)
FULL_DESCRIPTION = (
    "Supprime entièrement le dossier du modpack et retire son profil du lanceur. "
    "Les sauvegardes et réglages de ce modpack sont supprimés avec le dossier."
)


def build_uninstall_options_screen(parent, modpack_name: str, on_select, on_back, classic_available: bool = True):
    screen = tk.Frame(parent, bg=PALETTE["bg"])
    screen.grid(row=0, column=0, sticky="nsew")
    screen.grid_rowconfigure(0, weight=1)
    screen.grid_columnconfigure(0, weight=1)

    center = tk.Frame(screen, bg=PALETTE["bg"])
    center.grid(row=0, column=0)
    center.grid_columnconfigure(0, weight=1)

    tk.Label(
        center,
        text=f"Désinstaller {modpack_name}",
        bg=PALETTE["bg"],
        fg=PALETTE["text"],
        font=(GUI_FONT_SEMIBOLD, 32),
    ).grid(row=0, column=0, pady=(0, 24))

    options = tk.Frame(
        center,
        bg=PALETTE["surface"],
        highlightbackground=PALETTE["border"],
        highlightthickness=1,
        padx=32,
        pady=28,
        width=520,
        height=270,
    )
    options.grid(row=1, column=0)
    options.grid_columnconfigure(0, weight=1, minsize=380)
    options.grid_propagate(False)

    description = tk.Label(
        options,
        text="Survole une option pour voir ce qui sera supprimé.",
        bg=PALETTE["surface"],
        fg=PALETTE["muted"],
        font=(GUI_FONT, 10),
        wraplength=390,
        justify="left",
        anchor="w",
    )
    description.grid(row=2, column=0, sticky="ew", pady=(18, 0))

    def attach_description(button, text: str):
        button.bind("<Enter>", lambda event: description.config(text=text), add="+")
        button.bind(
            "<Leave>",
            lambda event: description.config(
                text="Survole une option pour voir ce qui sera supprimé."
            ),
            add="+",
        )

    classic = create_button(
        options,
        "Désinstallation classique",
        lambda: on_select(UninstallMode.CLASSIC),
        variant="primary",
    )
    classic.grid(row=0, column=0, sticky="ew")
    if classic_available:
        attach_description(classic, CLASSIC_DESCRIPTION)
    else:
        classic.config(text="Désinstallation classique effectuée", state="disabled", bg=PALETTE["button_disabled"], disabledforeground=PALETTE["button_disabled_text"], cursor="")
        description.config(text="Les fichiers du modpack ont déjà été retirés. Seule la désinstallation complète reste disponible.")

    full = create_button(
        options,
        "Désinstallation complète",
        lambda: on_select(UninstallMode.FULL),
        variant="danger",
    )
    full.grid(row=1, column=0, sticky="ew", pady=(12, 0))
    attach_description(full, FULL_DESCRIPTION)

    back = create_button(center, "Retour", on_back, variant="secondary")
    back.grid(row=2, column=0, pady=(18, 0))

    return screen


class UninstallationScreen:
    def __init__(self, parent, root, state, modpack_name: str, on_back):
        self.parent = parent
        self.root = root
        self.state = state
        self.modpack_name = modpack_name
        self.on_back = on_back
        self.screen = None
        self.status = None
        self.progress = None
        self.message = None
        self.back = None
        self.error = ""

    def render(self):
        self.screen = tk.Frame(self.parent, bg=PALETTE["bg"])
        self.screen.grid(row=0, column=0, sticky="nsew")
        self.screen.grid_rowconfigure(0, weight=1)
        self.screen.grid_columnconfigure(0, weight=1)
        center = tk.Frame(self.screen, bg=PALETTE["surface"], padx=42, pady=36)
        center.grid(row=0, column=0)
        center.grid_columnconfigure(0, weight=1, minsize=430)
        tk.Label(center, text=f"Désinstallation de {self.modpack_name}", bg=PALETTE["surface"], fg=PALETTE["text"], font=(GUI_FONT_SEMIBOLD, 24)).grid(row=0, column=0, pady=(0, 20))
        self.status = tk.Label(center, text="Préparation...", bg=PALETTE["surface"], fg=PALETTE["muted"], font=(GUI_FONT, 11))
        self.status.grid(row=1, column=0, pady=(0, 12))
        self.progress = RoundedProgress(center, show_bytes=False, height=26)
        self.progress.grid(row=2, column=0, sticky="ew")
        self.progress.set(0)
        self.message = tk.Label(center, text="", bg=PALETTE["surface"], fg=PALETTE["muted"], font=(GUI_FONT, 10), wraplength=420)
        self.message.grid(row=3, column=0, pady=(16, 0))
        self.back = create_button(center, "Retour", self.on_back, variant="secondary")
        self.back.grid(row=4, column=0, pady=(22, 0))
        self.back.grid_remove()

    def set_progress(self, value):
        value = max(0, min(100, int(value)))
        self.state["progress"] = value
        self.progress.set(value)

    def process_logs(self):
        while not log_queue.empty():
            data = log_queue.get()
            if data[0] == "progress":
                self.set_progress(data[1])
            elif data[0] == "log":
                self.status.config(text=data[1])
                if data[2] == "fatal":
                    self.error = data[1]
            elif data[0] == "done":
                self.finish(data[1] == "success")
        if self.screen and self.screen.winfo_exists() and self.state["status"] == "running":
            self.root.after(50, self.process_logs)

    def finish(self, success: bool):
        self.state["status"] = "success" if success else "error"
        if success:
            self.set_progress(100)
            self.status.config(text="Désinstallation terminée", fg=PALETTE["success"])
            self.message.config(text="Le modpack a été désinstallé correctement.")
        else:
            self.status.config(text="Désinstallation échouée", fg=PALETTE["error"])
            self.message.config(text=self.error or "Une erreur est survenue.", fg=PALETTE["error"])
        self.back.grid()
