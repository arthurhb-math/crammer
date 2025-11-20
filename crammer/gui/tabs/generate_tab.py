import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import subprocess
import sys
import os
from pathlib import Path

from crammer.i18n import get_translator
from crammer.gui.widgets import load_png
from crammer.utils.paths import get_resources_path


class GenerateTab(ttk.Frame):
    """Tab for generating assessments from templates."""

    def __init__(self, parent, app):
        """
        Initialize the Generate tab.

        Args:
            parent: Parent notebook widget
            app: Main application instance
        """
        super().__init__(parent)
        self.app = app
        self.t = get_translator()

        self.selected_template_path = tk.StringVar()
        self.last_output_folder = None

        self._build_ui()

    def _build_ui(self):
        """Build the tab UI."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        main_frame.rowconfigure(2, weight=1)
        main_frame.columnconfigure(0, weight=1)

        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        control_frame.columnconfigure(0, weight=1)

        logo_path = get_resources_path() / "assets" / "logo.png"
        if logo_path.exists():
            logo_photo = load_png(str(logo_path), (200, 200))
            if logo_photo:
                logo_label = ttk.Label(control_frame, image=logo_photo)
                logo_label.image = logo_photo
                logo_label.grid(row=0, column=0, pady=10)
        else:
            ttk.Label(control_frame, text="CRAMMER", font=("Helvetica", 16, "bold")).grid(
                row=0, column=0, pady=10
            )

        ttk.Label(
            control_frame,
            text=self.t("execute_generation_prompt"),
            justify="center",
            font=("Helvetica", 10, "italic"),
        ).grid(row=1, column=0, pady=5, padx=10)

        selection_frame = ttk.Frame(control_frame)
        selection_frame.grid(row=2, column=0, sticky="ew", pady=5, padx=10)
        selection_frame.columnconfigure(1, weight=1)

        ttk.Button(
            selection_frame, text=self.t("select_template_button"), command=self._select_template
        ).grid(row=0, column=0, sticky="w", pady=5)

        self.template_label = ttk.Label(selection_frame, text=self.t("no_template_selected"))
        self.template_label.grid(row=0, column=1, sticky="ew", padx=10, pady=5)

        self.generate_button = ttk.Button(
            control_frame,
            text=self.t("generate_button"),
            state="disabled",
            command=self._run_generation,
        )
        self.generate_button.grid(row=3, column=0, pady=10, padx=10, ipady=10, sticky="ew")

        progress_frame = ttk.LabelFrame(main_frame, text=self.t("progress_frame"), padding="5")
        progress_frame.grid(row=1, column=0, sticky="nsew", pady=10, padx=10)

        progress_frame.rowconfigure(0, weight=1)
        progress_frame.columnconfigure(0, weight=1)

        self.progress_text = scrolledtext.ScrolledText(
            progress_frame, height=10, wrap=tk.WORD, state="disabled", bg="#f0f0f0"
        )
        self.progress_text.grid(row=0, column=0, sticky="nsew")

        self.results_button = ttk.Button(
            main_frame, text=self.t("open_results_button"), command=self._open_output_folder
        )

    def _select_template(self):
        """Open file dialog to select a template."""
        from crammer.utils.paths import get_data_path

        templates_dir = get_data_path() / "templates"

        filepath = filedialog.askopenfilename(
            initialdir=str(templates_dir),
            title=self.t("select_template_button"),
            filetypes=[("JSON Templates", "*.json"), ("Python Templates", "*.py")],
        )

        if filepath:
            self.selected_template_path.set(filepath)
            filename = Path(filepath).name
            self.template_label.config(text=self.t("template_label", filename=filename))
            self.generate_button.config(state="normal")
            self.results_button.grid_forget()

    def _run_generation(self):
        """Start assessment generation in background thread."""
        self.generate_button.config(state="disabled")
        self.results_button.grid_forget()

        self.progress_text.config(state="normal")
        self.progress_text.delete(1.0, tk.END)
        self.progress_text.insert(tk.END, self.t("starting") + "\n\n")
        self.progress_text.config(state="disabled")

        thread = threading.Thread(target=self._generation_thread, daemon=True)
        thread.start()

    def _generation_thread(self):
        """Background thread for running generation."""
        try:
            from crammer.core.generator import AssessmentGenerator
            from crammer.data.json_store import JsonQuestionRepository, JsonTemplateRepository
            from crammer.data.csv_store import CsvStudentRepository
            from crammer.utils.paths import get_data_path, get_resources_path
            import json

            template_path = Path(self.selected_template_path.get())
            templates_dir = get_data_path() / "templates"
            template_repo = JsonTemplateRepository(templates_dir)

            if template_path.suffix == ".py":
                template = template_repo.load_from_py_file(template_path)
            else:
                template = template_repo.get_by_name(template_path.stem)

            if not template:
                raise Exception("Failed to load template")

            classes_dir = get_data_path() / "classes"
            student_repo = CsvStudentRepository(classes_dir)
            student_csv = classes_dir / template.csv_path
            students = student_repo.load_from_file(student_csv)

            questions_dir = get_data_path() / "questions"
            question_repo = JsonQuestionRepository(questions_dir)
            all_questions = question_repo.get_all()

            output_dir = get_data_path() / "output"
            template_file = get_resources_path() / "templates" / "default.tex"

            generator = AssessmentGenerator(
                template=template,
                students=students,
                all_questions=all_questions,
                output_dir=output_dir,
                template_path=template_file,
            )

            for progress in generator.generate():
                self._update_progress(progress.message + "\n")

                if progress.stage == "loading" and "Output will be saved" in progress.message:
                    self.last_output_folder = str(generator.get_pdf_directory())

            if self.last_output_folder:
                self.after(0, self._show_results_button)

            self._update_progress(self.t("process_finished") + "\n")

        except Exception as e:
            error_msg = self.t("critical_error", error=str(e))
            self._update_progress(error_msg + "\n")

        finally:
            self.after(0, lambda: self.generate_button.config(state="normal"))

    def _update_progress(self, text: str):
        """
        Update progress text widget.

        Args:
            text: Text to append
        """

        def update():
            self.progress_text.config(state="normal")
            self.progress_text.insert(tk.END, text)
            self.progress_text.see(tk.END)
            self.progress_text.config(state="disabled")

        self.after(0, update)

    def _show_results_button(self):
        """Show the results button."""
        self.results_button.grid(row=2, column=0, pady=10, padx=10, sticky="ew")

    def _open_output_folder(self):
        """Open the output folder in file manager."""
        if not self.last_output_folder or not os.path.isdir(self.last_output_folder):
            self._update_progress(
                self.t("results_folder_not_found", folder=self.last_output_folder) + "\n"
            )
            return

        if sys.platform == "win32":
            os.startfile(self.last_output_folder)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", self.last_output_folder])
        else:
            subprocess.Popen(["xdg-open", self.last_output_folder])
