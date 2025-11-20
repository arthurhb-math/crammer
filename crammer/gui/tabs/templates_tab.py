"""
Manage Templates tab.

Provides interface for creating and editing assessment templates.
"""

import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path

from crammer.i18n import get_translator
from crammer.core.models import Template, SelectionBlock, Difficulty
from crammer.core.validator import validate_template, ValidationError
from crammer.data.json_store import JsonTemplateRepository
from crammer.data.csv_store import CsvStudentRepository
from crammer.utils.paths import get_data_path
from crammer.gui.dialogs import show_error, show_info, show_warning, ask_yes_no, ask_string


class TemplatesTab(ttk.Frame):
    """Tab for managing assessment templates."""

    def __init__(self, parent, app):
        """
        Initialize the Templates tab.

        Args:
            parent: Parent notebook widget
            app: Main application instance
        """
        super().__init__(parent)
        self.app = app
        self.t = get_translator()

        templates_dir = get_data_path() / "templates"
        self.template_repo = JsonTemplateRepository(templates_dir)

        classes_dir = get_data_path() / "classes"
        self.student_repo = CsvStudentRepository(classes_dir)

        self.current_template = None

        self._build_ui()
        self._load_template_list()

    def _build_ui(self):
        """Build the tab UI."""
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_template_list(main_pane)

        self._build_template_editor(main_pane)

    def _build_template_list(self, parent):
        """Build the template list panel."""
        list_frame = ttk.LabelFrame(parent, text=self.t("templates_frame"))
        parent.add(list_frame, weight=2)

        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(
            button_frame, text=self.t("new_template_button"), command=self._new_template
        ).pack(fill="x", pady=2)

        ttk.Button(
            button_frame, text=self.t("delete_template_button"), command=self._delete_template
        ).pack(fill="x", pady=2)

        self.template_listbox = tk.Listbox(list_frame)
        self.template_listbox.pack(fill="both", expand=True, side="left", padx=5, pady=5)
        self.template_listbox.bind("<<ListboxSelect>>", self._on_template_select)

        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.template_listbox.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.template_listbox.config(yscrollcommand=scrollbar.set)

    def _build_template_editor(self, parent):
        """Build the template editor panel."""
        editor_frame = ttk.LabelFrame(parent, text=self.t("template_editor_frame"))
        parent.add(editor_frame, weight=5)

        self.editor_notebook = ttk.Notebook(editor_frame)
        self.editor_notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self._build_general_info_tab()

        self._build_blocks_tab()

        ttk.Button(
            editor_frame, text=self.t("save_template_button"), command=self._save_template
        ).pack(fill="x", padx=5, pady=5)

    def _build_general_info_tab(self):
        """Build the general information tab."""
        tab = ttk.Frame(self.editor_notebook)
        self.editor_notebook.add(tab, text=self.t("general_info_tab"))

        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        doc_frame = ttk.LabelFrame(
            scrollable_frame, text=self.t("doc_settings_frame"), padding="10"
        )
        doc_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(doc_frame, text=self.t("doc_title_label")).grid(
            row=0, column=0, sticky="w", padx=5, pady=2
        )
        self.doc_title_entry = ttk.Entry(doc_frame)
        self.doc_title_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(doc_frame, text=self.t("file_prefix_label")).grid(
            row=1, column=0, sticky="w", padx=5, pady=2
        )
        self.file_prefix_entry = ttk.Entry(doc_frame)
        self.file_prefix_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        doc_frame.columnconfigure(1, weight=1)

        course_frame = ttk.LabelFrame(
            scrollable_frame, text=self.t("course_info_frame"), padding="10"
        )
        course_frame.pack(fill="x", padx=5, pady=5)

        course_fields = [
            ("institution_label", "institution_entry"),
            ("center_label", "center_entry"),
            ("program_label", "program_entry"),
            ("course_name_label", "course_name_entry"),
            ("professor_name_label", "professor_entry"),
        ]

        for i, (label_key, entry_attr) in enumerate(course_fields):
            ttk.Label(course_frame, text=self.t(label_key)).grid(
                row=i, column=0, sticky="w", padx=5, pady=2
            )
            entry = ttk.Entry(course_frame)
            entry.grid(row=i, column=1, sticky="ew", padx=5, pady=2)
            setattr(self, entry_attr, entry)

        course_frame.columnconfigure(1, weight=1)

        ttk.Label(course_frame, text=self.t("logo_path_label")).grid(
            row=len(course_fields), column=0, sticky="w", padx=5, pady=2
        )
        logo_frame = ttk.Frame(course_frame)
        logo_frame.grid(row=len(course_fields), column=1, sticky="ew", padx=5, pady=2)

        self.logo_entry = ttk.Entry(logo_frame)
        self.logo_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ttk.Button(logo_frame, text="...", width=3, command=self._select_logo).pack(side="right")

        class_frame = ttk.LabelFrame(scrollable_frame, text=self.t("class_frame"), padding="10")
        class_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(class_frame, text=self.t("class_file_label")).grid(
            row=0, column=0, sticky="w", padx=5, pady=2
        )

        available_classes = self.student_repo.get_available_rosters()
        self.class_combobox = ttk.Combobox(class_frame, values=available_classes, state="readonly")
        self.class_combobox.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        class_frame.columnconfigure(1, weight=1)

    def _build_blocks_tab(self):
        """Build the question blocks tab."""
        tab = ttk.Frame(self.editor_notebook)
        self.editor_notebook.add(tab, text=self.t("question_blocks_tab"))

        list_frame = ttk.Frame(tab)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.blocks_tree = ttk.Treeview(
            list_frame, columns=("method", "details"), show="headings", selectmode="browse"
        )
        self.blocks_tree.heading("method", text=self.t("method_header"))
        self.blocks_tree.heading("details", text=self.t("details_header"))
        self.blocks_tree.column("method", width=200)
        self.blocks_tree.column("details", width=400)
        self.blocks_tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.blocks_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.blocks_tree.config(yscrollcommand=scrollbar.set)

        button_frame = ttk.Frame(tab)
        button_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(button_frame, text=self.t("add_block_button"), command=self._add_block).pack(
            side="left", padx=5
        )

        ttk.Button(button_frame, text=self.t("edit_block_button"), command=self._edit_block).pack(
            side="left", padx=5
        )

        ttk.Button(
            button_frame, text=self.t("remove_block_button"), command=self._remove_block
        ).pack(side="left", padx=5)

    def _select_logo(self):
        """Open file dialog to select logo."""
        filepath = filedialog.askopenfilename(
            title=self.t("logo_path_label"),
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.svg"), ("All files", "*.*")],
        )

        if filepath:
            self.logo_entry.delete(0, tk.END)
            self.logo_entry.insert(0, filepath)

    def _load_template_list(self):
        """Load list of available templates."""
        templates = self.template_repo.get_all()

        self.template_listbox.delete(0, tk.END)
        for template_name in templates:
            self.template_listbox.insert(tk.END, template_name)

    def _on_template_select(self, event):
        """Handle template selection from list."""
        selection = self.template_listbox.curselection()
        if not selection:
            return

        template_name = self.template_listbox.get(selection[0])
        self._load_template(template_name)

    def _load_template(self, template_name: str):
        """Load a template from repository."""
        try:
            template = self.template_repo.get_by_name(template_name)
            if template:
                self.current_template = template
                self._load_template_to_form(template)
        except Exception as e:
            show_error(
                self,
                self.t("load_template_error_title"),
                self.t("load_template_error_message", e=str(e)),
            )

    def _load_template_to_form(self, template: Template):
        """Load template data into form."""
        self.doc_title_entry.delete(0, tk.END)
        self.doc_title_entry.insert(0, template.document_title)

        self.file_prefix_entry.delete(0, tk.END)
        self.file_prefix_entry.insert(0, template.filename_prefix)

        course_info = template.course_info

        self.institution_entry.delete(0, tk.END)
        self.institution_entry.insert(0, course_info.get("institution", ""))

        self.center_entry.delete(0, tk.END)
        self.center_entry.insert(0, course_info.get("center", ""))

        self.program_entry.delete(0, tk.END)
        self.program_entry.insert(0, course_info.get("program", ""))

        self.course_name_entry.delete(0, tk.END)
        self.course_name_entry.insert(0, course_info.get("course_name", ""))

        self.professor_entry.delete(0, tk.END)
        self.professor_entry.insert(0, course_info.get("professor_name", ""))

        self.logo_entry.delete(0, tk.END)
        if template.logo_path:
            self.logo_entry.insert(0, template.logo_path)

        if template.csv_path:
            self.class_combobox.set(template.csv_path)

        self._update_blocks_tree()

    def _update_blocks_tree(self):
        """Update the blocks treeview with current template's blocks."""
        for item in self.blocks_tree.get_children():
            self.blocks_tree.delete(item)

        if self.current_template:
            for block in self.current_template.selection_blocks:
                method_text = self._get_method_display_text(block.method)
                details_text = self._get_block_details_text(block)

                self.blocks_tree.insert("", tk.END, values=(method_text, details_text))

    def _get_method_display_text(self, method: str) -> str:
        """Get display text for a selection method."""
        method_map = {
            "manual": self.t("method_manual"),
            "random_all": self.t("method_random_all"),
            "random_topic": self.t("method_random_topic"),
            "random_difficulty": self.t("method_random_difficulty"),
        }
        return method_map.get(method, method)

    def _get_block_details_text(self, block: SelectionBlock) -> str:
        """Get details text for a block."""
        if block.method == "manual":
            ids_str = ", ".join(block.question_ids[:3])
            if len(block.question_ids) > 3:
                ids_str += "..."
            return self.t("manual_method_details", ids=ids_str)

        elif block.method == "random_all":
            return self.t("random_all_method_details", qty=block.quantity)

        elif block.method == "random_topic":
            return self.t("random_topic_method_details", topic=block.topic, qty=block.quantity)

        elif block.method == "random_difficulty":
            diff_str = block.difficulty.value if block.difficulty else ""
            return self.t(
                "random_difficulty_method_details", difficulty=diff_str, qty=block.quantity
            )

        elif block.method == "random_type":
            return self.t(
                "random_type_method_details", type=block.question_type, qty=block.quantity
            )

        return ""

    def _add_block(self):
        """Add a new question block."""
        if not self.current_template:
            show_warning(
                self, self.t("no_selection_warning"), self.t("no_template_for_block_warning")
            )
            return

        block = self._show_block_dialog()
        if block:
            self.current_template.selection_blocks.append(block)
            self._update_blocks_tree()

    def _edit_block(self):
        """Edit the selected block."""
        selection = self.blocks_tree.selection()
        if not selection:
            show_warning(
                self, self.t("no_selection_warning"), self.t("edit_block_selection_warning")
            )
            return

        item = selection[0]
        index = self.blocks_tree.index(item)

        block = self.current_template.selection_blocks[index]
        edited_block = self._show_block_dialog(block)

        if edited_block:
            self.current_template.selection_blocks[index] = edited_block
            self._update_blocks_tree()

    def _remove_block(self):
        """Remove the selected block."""
        selection = self.blocks_tree.selection()
        if not selection:
            show_warning(
                self, self.t("no_selection_warning"), self.t("remove_block_selection_warning")
            )
            return

        if not ask_yes_no(
            self, self.t("confirm_deletion_title"), self.t("confirm_remove_block_message")
        ):
            return

        item = selection[0]
        index = self.blocks_tree.index(item)
        del self.current_template.selection_blocks[index]

        self._update_blocks_tree()

    def _show_block_dialog(self, block: SelectionBlock = None) -> SelectionBlock:
        """
        Show dialog for adding/editing a block.

        Args:
            block: Existing block to edit, or None for new block

        Returns:
            New/edited SelectionBlock, or None if cancelled
        """
        dialog = BlockDialog(self, block)
        return dialog.result

    def _save_template(self):
        """Save the current template."""
        if not self.current_template:
            show_warning(
                self, self.t("no_selection_warning"), self.t("no_template_selected_warning_message")
            )
            return

        try:
            self._update_template_from_form()
        except ValueError as e:
            show_error(self, self.t("invalid_type_warning"), str(e))
            return

        try:
            validate_template(self.current_template)
        except ValidationError as e:
            show_error(self, self.t("invalid_id_warning"), str(e))
            return

        try:
            self.template_repo.save(self.current_template)
            show_info(
                self,
                self.t("success_title"),
                self.t("template_saved_message", name=self.current_template.name),
            )
        except Exception as e:
            show_error(
                self, self.t("save_error_title"), self.t("template_save_error_message", e=str(e))
            )

    def _update_template_from_form(self):
        """Update current template with form data."""
        self.current_template.document_title = self.doc_title_entry.get().strip()
        self.current_template.filename_prefix = self.file_prefix_entry.get().strip()

        self.current_template.course_info = {
            "institution": self.institution_entry.get().strip(),
            "center": self.center_entry.get().strip(),
            "program": self.program_entry.get().strip(),
            "course_name": self.course_name_entry.get().strip(),
            "professor_name": self.professor_entry.get().strip(),
        }

        logo = self.logo_entry.get().strip()
        self.current_template.logo_path = logo if logo else None

        csv_path = self.class_combobox.get()
        if not csv_path:
            raise ValueError(self.t("no_class_warning_message"))
        self.current_template.csv_path = csv_path

    def _new_template(self):
        """Create a new template."""
        name = ask_string(
            self, self.t("new_template_dialog_title"), self.t("new_template_dialog_prompt")
        )

        if not name:
            return

        if name in self.template_repo.get_all():
            show_warning(
                self, self.t("file_exists_warning_title"), self.t("template_exists_warning_message")
            )
            return

        self.current_template = Template(
            name=name,
            document_title="",
            filename_prefix="assessment",
            course_info={},
            selection_blocks=[],
            csv_path=None,
        )

        self._load_template_to_form(self.current_template)

        show_info(self, self.t("success_title"), self.t("new_template_success_message", name=name))

    def _delete_template(self):
        """Delete the selected template."""
        selection = self.template_listbox.curselection()
        if not selection:
            show_warning(
                self, self.t("no_selection_warning"), self.t("delete_template_selection_warning")
            )
            return

        template_name = self.template_listbox.get(selection[0])

        if not ask_yes_no(
            self,
            self.t("confirm_deletion_title"),
            self.t("confirm_delete_template_message", name=template_name),
        ):
            return

        try:
            self.template_repo.delete(template_name)
            show_info(
                self,
                self.t("success_title"),
                self.t("question_deleted_message", q_id=template_name),
            )
            self._load_template_list()
            self.current_template = None
        except Exception as e:
            show_error(
                self, self.t("save_error_title"), self.t("delete_template_error_message", e=str(e))
            )

    def refresh_class_list(self):
        """Recarrega a lista de turmas disponíveis do repositório."""
        try:
            available_classes = self.student_repo.get_available_rosters()
            current_value = self.class_combobox.get()

            self.class_combobox["values"] = available_classes

            if current_value in available_classes:
                self.class_combobox.set(current_value)
            else:
                self.class_combobox.set("")
        except Exception as e:
            print(f"Não foi possível atualizar a lista de turmas: {e}")


class BlockDialog:
    """Dialog for adding/editing a question block."""

    def __init__(self, parent, block: SelectionBlock = None):
        """
        Create block dialog.

        Args:
            parent: Parent window
            block: Existing block to edit, or None for new
        """
        self.parent = parent
        self.t = get_translator()
        self.result = None
        self.editing_block = block

        self.window = tk.Toplevel(parent)
        self.window.title(
            self.t("edit_block_dialog_title") if block else self.t("add_block_dialog_title")
        )
        self.window.geometry("500x400")
        self.window.resizable(False, False)

        self._center_on_parent()

        self.window.transient(parent)
        self.window.grab_set()

        self._build_ui()

        if block:
            self._load_block_to_form(block)

        parent.wait_window(self.window)

    def _center_on_parent(self):
        """Center dialog on parent."""
        self.parent.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 250
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - 200
        self.window.geometry(f"+{x}+{y}")

    def _build_ui(self):
        """Build dialog UI."""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text=self.t("block_title_label")).grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.title_entry = ttk.Entry(main_frame)
        self.title_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(main_frame, text=self.t("selection_method_label")).grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.method_combobox = ttk.Combobox(
            main_frame,
            values=[
                self.t("method_manual"),
                self.t("method_random_all"),
                self.t("method_random_topic"),
                self.t("method_random_difficulty"),
            ],
            state="readonly",
        )
        self.method_combobox.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.method_combobox.bind("<<ComboboxSelected>>", self._on_method_change)

        self.fields_frame = ttk.Frame(main_frame)
        self.fields_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        ttk.Button(button_frame, text=self.t("save_question_button"), command=self._save).pack(
            side="right", padx=5
        )

        ttk.Button(button_frame, text=self.t("cancel"), command=self.window.destroy).pack(
            side="right", padx=5
        )

    def _on_method_change(self, event=None):
        """Handle method selection change."""
        for widget in self.fields_frame.winfo_children():
            widget.destroy()

        method = self.method_combobox.get()

        if method == self.t("method_manual"):
            self._build_manual_fields()
        elif method == self.t("method_random_all"):
            self._build_random_all_fields()
        elif method == self.t("method_random_topic"):
            self._build_random_topic_fields()
        elif method == self.t("method_random_difficulty"):
            self._build_random_difficulty_fields()

    def _build_manual_fields(self):
        """Build fields for manual selection."""
        ttk.Label(self.fields_frame, text=self.t("question_ids_label")).pack(
            anchor="w", pady=(0, 5)
        )
        self.ids_text = tk.Text(self.fields_frame, height=10, wrap=tk.WORD)
        self.ids_text.pack(fill="both", expand=True)

    def _build_random_all_fields(self):
        """Build fields for random all selection."""
        ttk.Label(self.fields_frame, text=self.t("quantity_label")).pack(anchor="w", pady=(0, 5))
        self.quantity_spinbox = ttk.Spinbox(self.fields_frame, from_=1, to=100, width=10)
        self.quantity_spinbox.pack(anchor="w")
        self.quantity_spinbox.set("5")

    def _build_random_topic_fields(self):
        """Build fields for random topic selection."""
        ttk.Label(self.fields_frame, text=self.t("topic_label")).pack(anchor="w", pady=(0, 5))

        from crammer.data.json_store import JsonQuestionRepository

        questions_dir = get_data_path() / "questions"
        question_repo = JsonQuestionRepository(questions_dir)
        topics = question_repo.get_all_topics()

        self.topic_combobox = ttk.Combobox(self.fields_frame, values=topics)
        self.topic_combobox.pack(fill="x", pady=(0, 10))

        ttk.Label(self.fields_frame, text=self.t("quantity_label")).pack(anchor="w", pady=(0, 5))
        self.quantity_spinbox = ttk.Spinbox(self.fields_frame, from_=1, to=100, width=10)
        self.quantity_spinbox.pack(anchor="w")
        self.quantity_spinbox.set("5")

    def _build_random_difficulty_fields(self):
        """Build fields for random difficulty selection."""
        ttk.Label(self.fields_frame, text=self.t("difficulty_label")).pack(anchor="w", pady=(0, 5))
        self.difficulty_combobox = ttk.Combobox(
            self.fields_frame, values=["easy", "medium", "hard"], state="readonly"
        )
        self.difficulty_combobox.pack(fill="x", pady=(0, 10))

        ttk.Label(self.fields_frame, text=self.t("quantity_label")).pack(anchor="w", pady=(0, 5))
        self.quantity_spinbox = ttk.Spinbox(self.fields_frame, from_=1, to=100, width=10)
        self.quantity_spinbox.pack(anchor="w")
        self.quantity_spinbox.set("5")

    def _load_block_to_form(self, block: SelectionBlock):
        """Load existing block to form."""
        self.title_entry.insert(0, block.title)

        method_map = {
            "manual": self.t("method_manual"),
            "random_all": self.t("method_random_all"),
            "random_topic": self.t("method_random_topic"),
            "random_difficulty": self.t("method_random_difficulty"),
        }
        self.method_combobox.set(method_map.get(block.method, ""))
        self._on_method_change()

        if block.method == "manual":
            self.ids_text.insert("1.0", ", ".join(block.question_ids))
        elif block.method == "random_all":
            self.quantity_spinbox.set(str(block.quantity))
        elif block.method == "random_topic":
            self.topic_combobox.set(block.topic or "")
            self.quantity_spinbox.set(str(block.quantity))
        elif block.method == "random_difficulty":
            if block.difficulty:
                self.difficulty_combobox.set(block.difficulty.value)
            self.quantity_spinbox.set(str(block.quantity))
        elif block.method == "random_type":
            pass

    def _save(self):
        """Save the block and close dialog."""
        title = self.title_entry.get().strip()
        if not title:
            show_warning(self.window, self.t("invalid_id_warning"), self.t("block_title_label"))
            return

        method_text = self.method_combobox.get()
        method_reverse = {
            self.t("method_manual"): "manual",
            self.t("method_random_all"): "random_all",
            self.t("method_random_topic"): "random_topic",
            self.t("method_random_difficulty"): "random_difficulty",
        }
        method = method_reverse.get(method_text)

        if not method:
            show_warning(
                self.window, self.t("invalid_type_warning"), self.t("selection_method_label")
            )
            return

        try:
            if method == "manual":
                ids_text = self.ids_text.get("1.0", tk.END).strip()
                question_ids = [qid.strip() for qid in ids_text.split(",") if qid.strip()]

                if not question_ids:
                    show_warning(
                        self.window,
                        self.t("invalid_id_warning"),
                        self.t("manual_selection_warning_message"),
                    )
                    return

                block = SelectionBlock(title=title, method=method, question_ids=question_ids)

            elif method == "random_all":
                quantity = int(self.quantity_spinbox.get())
                block = SelectionBlock(title=title, method=method, quantity=quantity)

            elif method == "random_topic":
                topic = self.topic_combobox.get().strip()
                quantity = int(self.quantity_spinbox.get())

                if not topic:
                    show_warning(self.window, self.t("invalid_id_warning"), self.t("topic_label"))
                    return

                block = SelectionBlock(title=title, method=method, topic=topic, quantity=quantity)

            elif method == "random_difficulty":
                difficulty_str = self.difficulty_combobox.get()
                quantity = int(self.quantity_spinbox.get())

                if not difficulty_str:
                    show_warning(
                        self.window, self.t("invalid_id_warning"), self.t("difficulty_label")
                    )
                    return

                block = SelectionBlock(
                    title=title,
                    method=method,
                    difficulty=Difficulty.from_string(difficulty_str),
                    quantity=quantity,
                )

            elif method == "random_type":
                prompt_text = self.type_combobox.get().strip()
                quantity = int(self.quantity_spinbox.get())

                if not prompt_text:
                    show_warning(
                        self.window,
                        self.t("invalid_id_warning"),
                        self.t("prompt_type_label_selection"),
                    )
                    return

                block = SelectionBlock(title=title, method=method, quantity=quantity)

            self.result = block
            self.window.destroy()

        except ValueError as e:
            show_error(self.window, self.t("invalid_id_warning"), str(e))
