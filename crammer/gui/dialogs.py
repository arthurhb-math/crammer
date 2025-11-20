"""
Common dialog windows for Crammer GUI.

Provides reusable dialogs for About, License, and other common interactions.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import webbrowser
from pathlib import Path

from crammer.i18n import get_translator
from crammer.utils.version import get_version_info


class AboutDialog:
    """About dialog showing version, license, and author information."""

    def __init__(self, parent, logo_path: Path = None):
        """
        Create and show the About dialog.

        Args:
            parent: Parent window
            logo_path: Optional path to logo SVG file
        """
        self.parent = parent
        self.logo_path = logo_path
        self.t = get_translator()

        self.window = tk.Toplevel(parent)
        self.window.title(self.t("gpl_disclaimer_title"))
        self.window.geometry("640x640")
        self.window.resizable(False, False)

        self._center_on_parent()

        self.window.transient(parent)
        self.window.grab_set()

        self._build_ui()

    def _center_on_parent(self):
        """Center the dialog on the parent window."""
        self.parent.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 320
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - 384
        self.window.geometry(f"+{x}+{y}")

    def _build_ui(self):
        """Build the dialog UI."""
        main_frame = ttk.Frame(self.window, padding="15")
        main_frame.pack(fill="both", expand=True)

        if self.logo_path and self.logo_path.exists():
            try:
                from .widgets.png_image import load_png

                logo_photo = load_png(str(self.logo_path), (250, 250))
                if logo_photo:
                    logo_label = ttk.Label(main_frame, image=logo_photo)
                    logo_label.image = logo_photo
                    logo_label.pack(pady=5)
            except Exception:
                ttk.Label(main_frame, text="CRAMMER", font=("Helvetica", 16, "bold")).pack(pady=5)
        else:
            ttk.Label(main_frame, text="CRAMMER", font=("Helvetica", 16, "bold")).pack(pady=5)

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

        ttk.Button(
            button_frame, text=self.t("view_full_license"), command=self._open_license_url
        ).pack(side="left")

        ttk.Button(button_frame, text=self.t("close"), command=self.window.destroy).pack(
            side="right"
        )

    def _open_license_url(self):
        """Open GPL license URL in browser."""
        webbrowser.open("https://www.gnu.org/licenses/gpl-3.0.html")

    def show(self):
        """Show the dialog and wait for it to close."""
        self.parent.wait_window(self.window)


def show_error(parent, title: str, message: str):
    """
    Show an error message dialog.

    Args:
        parent: Parent window
        title: Dialog title
        message: Error message
    """
    from tkinter import messagebox

    messagebox.showerror(title, message, parent=parent)


def show_warning(parent, title: str, message: str):
    """
    Show a warning message dialog.

    Args:
        parent: Parent window
        title: Dialog title
        message: Warning message
    """
    from tkinter import messagebox

    messagebox.showwarning(title, message, parent=parent)


def show_info(parent, title: str, message: str):
    """
    Show an information message dialog.

    Args:
        parent: Parent window
        title: Dialog title
        message: Information message
    """
    from tkinter import messagebox

    messagebox.showinfo(title, message, parent=parent)


def ask_yes_no(parent, title: str, message: str) -> bool:
    """
    Show a yes/no question dialog.

    Args:
        parent: Parent window
        title: Dialog title
        message: Question message

    Returns:
        True if yes, False if no
    """
    from tkinter import messagebox

    return messagebox.askyesno(title, message, parent=parent)


def ask_string(parent, title: str, prompt: str) -> str:
    """
    Show a string input dialog.

    Args:
        parent: Parent window
        title: Dialog title
        prompt: Input prompt

    Returns:
        User input string, or None if cancelled
    """
    from tkinter import simpledialog

    return simpledialog.askstring(title, prompt, parent=parent)
