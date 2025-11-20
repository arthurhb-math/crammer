import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path

from crammer.i18n import get_translator
from crammer.utils.version import get_version_info
from crammer.utils.paths import get_data_path, get_resources_path
from crammer.gui.widgets import load_png
from crammer.gui.tabs import GenerateTab, QuestionsTab, ClassesTab, TemplatesTab
from crammer.gui.dialogs import AboutDialog


class CrammerApp(tk.Tk):
    """Main Crammer application window."""

    def __init__(self):
        """Initialize the application."""
        super().__init__()

        self.config_file = get_data_path() / "config.json"
        self.app_config = self._load_config()

        self.t = get_translator(self.app_config.get("language"))
        self.show_about_on_startup = self.app_config.get("show_about_on_startup", True)

        logo_path = get_resources_path() / "assets" / "logo.png"
        if logo_path.exists():
            from crammer.gui.widgets import load_png

            self.logo_icon = load_png(str(logo_path))
            if self.logo_icon:
                self.iconphoto(True, self.logo_icon)

        self.title(self.t("app_title"))
        self.geometry("1280x720")
        self.minsize(1280, 720)

        self.withdraw()

        self._build_ui()

        self.update_idletasks()
        width = 1280
        height = 720
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.deiconify()

        if self.show_about_on_startup:
            self.after(100, self._show_about)

    def _build_ui(self):
        """Build the application UI."""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=1, fill="both")

        self.tab_generate = GenerateTab(self.notebook, self)
        self.tab_questions = QuestionsTab(self.notebook, self)
        self.tab_classes = ClassesTab(self.notebook, self)
        self.tab_templates = TemplatesTab(self.notebook, self)

        self.tab_classes.templates_tab = self.tab_templates

        self.notebook.add(self.tab_generate, text=self.t("tab_generate"))
        self.notebook.add(self.tab_questions, text=self.t("tab_questions"))
        self.notebook.add(self.tab_classes, text=self.t("tab_classes"))
        self.notebook.add(self.tab_templates, text=self.t("tab_templates"))

        self._build_menu()

    def _build_menu(self):
        """Build the application menu bar."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        language_menu = tk.Menu(menubar, tearoff=0)
        language_menu.add_command(label="English", command=lambda: self._change_language("en"))
        language_menu.add_command(label="Português", command=lambda: self._change_language("pt_br"))
        menubar.add_cascade(label=self.t("language"), menu=language_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label=self.t("tab_about"), command=self._show_about)
        menubar.add_cascade(label=self.t("help"), menu=help_menu)

    def _change_language(self, lang: str):
        """Change application language and save the setting."""

        new_t = get_translator(lang)

        self.app_config["language"] = lang
        self._save_config(self.app_config)

        from tkinter import messagebox

        messagebox.showinfo(
            new_t("language"),
            "Please restart the application to apply language changes.\n\n"
            "Por favor, reinicie o aplicativo para aplicar as mudanças de idioma.",
        )

    def _load_config(self) -> dict:
        """
        Load configuration from file.

        Returns:
            The configuration dictionary
        """
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config
        except (FileNotFoundError, json.JSONDecodeError):
            return {"show_about_on_startup": True, "language": None}

    def _save_config(self, config_data: dict):
        """
        Save configuration to file.

        Args:
            config_data: The configuration dictionary to save
        """
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)

    def _show_about(self):
        """Show the About dialog."""
        dialog_window = tk.Toplevel(self)
        dialog_window.title(self.t("gpl_disclaimer_title"))

        dialog_window.update_idletasks()
        width = 640
        height = 640

        screen_width = dialog_window.winfo_screenwidth()
        screen_height = dialog_window.winfo_screenheight()

        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        dialog_window.geometry(f"{width}x{height}+{x}+{y}")
        dialog_window.resizable(False, False)

        dialog_window.transient(self)
        dialog_window.grab_set()

        from tkinter import scrolledtext
        import webbrowser

        main_frame = ttk.Frame(dialog_window, padding="15")
        main_frame.pack(fill="both", expand=True)

        logo_path = get_resources_path() / "assets" / "logo.png"
        if logo_path and logo_path.exists():
            try:
                from crammer.gui.widgets import load_png

                logo_photo = load_png(str(logo_path), (200, 200))
                if logo_photo:
                    logo_label = ttk.Label(main_frame, image=logo_photo)
                    logo_label.image = logo_photo
                    logo_label.pack(pady=5)
            except Exception:
                pass

        ttk.Label(main_frame, text="Crammer", font=("Helvetica", 16, "bold")).pack()

        info_frame = ttk.Frame(main_frame, padding="10")
        info_frame.pack(pady=5)

        version_info = get_version_info()

        info_items = {
            self.t(
                "about_version"
            ): f"v{version_info['version']} \"{version_info['version_name']}\"",
            self.t("about_build"): version_info["build_number"],
            self.t("about_author"): version_info["author"],
            self.t("about_contact"): version_info["email"],
        }

        for i, (label, value) in enumerate(info_items.items()):
            ttk.Label(info_frame, text=f"{label}:", font=("Helvetica", 10, "bold")).grid(
                row=i, column=0, sticky="e", padx=5
            )

            ttk.Label(info_frame, text=value, wraplength=400).grid(
                row=i, column=1, sticky="w", padx=5
            )

        info_frame.columnconfigure(1, weight=1)

        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=10)

        text_widget = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=10)
        text_widget.pack(fill="both", expand=True, pady=(0, 15))
        text_widget.insert("1.0", self.t("gpl_disclaimer_text"))
        text_widget.config(state="disabled")

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))

        def open_license_url():
            webbrowser.open("https://www.gnu.org/licenses/gpl-3.0.html")

        show_on_startup_var = tk.BooleanVar(value=self.show_about_on_startup)
        show_on_startup_check = ttk.Checkbutton(
            button_frame, text=self.t("show_on_startup"), variable=show_on_startup_var
        )

        def on_close():
            self.show_about_on_startup = show_on_startup_var.get()
            self.app_config["show_about_on_startup"] = self.show_about_on_startup
            self._save_config(self.app_config)
            dialog_window.destroy()

        ttk.Button(button_frame, text=self.t("view_full_license"), command=open_license_url).pack(
            side="left"
        )

        show_on_startup_check.pack(side="left", expand=True)

        ttk.Button(button_frame, text=self.t("close"), command=on_close).pack(side="right")

        dialog_window.protocol("WM_DELETE_WINDOW", on_close)

        self.wait_window(dialog_window)


def main():
    """Main entry point for GUI application."""
    app = CrammerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
