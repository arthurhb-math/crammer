import tkinter as tk
from tkinter import ttk
from pathlib import Path

from crammer.i18n import get_translator
from crammer.core.models import Student
from crammer.core.validator import validate_student, validate_roster, ValidationError
from crammer.data.csv_store import CsvStudentRepository
from crammer.utils.paths import get_data_path
from crammer.gui.dialogs import show_error, show_info, show_warning, ask_yes_no, ask_string


class ClassesTab(ttk.Frame):
    """Tab for managing student rosters (classes)."""

    def __init__(self, parent, app):
        """
        Initialize the Classes tab.

        Args:
            parent: Parent notebook widget
            app: Main application instance
        """
        super().__init__(parent)
        self.app = app
        self.t = get_translator()

        classes_dir = get_data_path() / "classes"
        self.student_repo = CsvStudentRepository(classes_dir)

        self.current_class_file = None
        self.students = []
        self.templates_tab = None

        self._build_ui()
        self._load_class_list()

    def _build_ui(self):
        """Build the tab UI."""
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_class_list(main_pane)

        self._build_student_editor(main_pane)

    def _build_class_list(self, parent):
        """Build the class list panel."""
        list_frame = ttk.LabelFrame(parent, text=self.t("saved_classes_frame"))
        parent.add(list_frame, weight=2)

        ttk.Button(list_frame, text=self.t("new_class_button"), command=self._new_class).pack(
            fill="x", padx=5, pady=5
        )

        ttk.Button(list_frame, text=self.t("delete_class_button"), command=self._delete_class).pack(
            fill="x", padx=5, pady=(0, 5)
        )

        self.class_listbox = tk.Listbox(list_frame)
        self.class_listbox.pack(fill="both", expand=True, side="left", padx=5, pady=5)
        self.class_listbox.bind("<<ListboxSelect>>", self._on_class_select)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.class_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.class_listbox.config(yscrollcommand=scrollbar.set)

    def _build_student_editor(self, parent):
        """Build the student editor panel."""
        editor_frame = ttk.LabelFrame(parent, text=self.t("class_students_frame"))
        parent.add(editor_frame, weight=5)

        tree_frame = ttk.Frame(editor_frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.student_tree = ttk.Treeview(
            tree_frame,
            columns=("student_name", "student_id"),
            show="headings",
            selectmode="extended",
        )
        self.student_tree.heading("student_name", text=self.t("student_name_header"))
        self.student_tree.heading("student_id", text=self.t("student_id_header"))
        self.student_tree.column("student_name", width=300)
        self.student_tree.column("student_id", width=150)
        self.student_tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.student_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.student_tree.config(yscrollcommand=scrollbar.set)

        input_frame = ttk.Frame(editor_frame)
        input_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(input_frame, text=self.t("name_label")).grid(
            row=0, column=0, sticky="w", padx=5, pady=2
        )
        self.name_entry = ttk.Entry(input_frame)
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        ttk.Label(input_frame, text=self.t("id_label")).grid(
            row=1, column=0, sticky="w", padx=5, pady=2
        )
        self.id_entry = ttk.Entry(input_frame)
        self.id_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        input_frame.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(editor_frame)
        button_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(button_frame, text=self.t("add_student_button"), command=self._add_student).pack(
            side="left", padx=5
        )

        ttk.Button(
            button_frame, text=self.t("remove_student_button"), command=self._remove_student
        ).pack(side="left", padx=5)

        ttk.Button(button_frame, text=self.t("save_class_button"), command=self._save_class).pack(
            side="right", padx=5
        )

    def _load_class_list(self):
        """Load list of available classes."""
        rosters = self.student_repo.get_available_rosters()

        self.class_listbox.delete(0, tk.END)
        for roster in rosters:
            self.class_listbox.insert(tk.END, roster)

    def _on_class_select(self, event):
        """Handle class selection from list."""
        selection = self.class_listbox.curselection()
        if not selection:
            return

        class_file = self.class_listbox.get(selection[0])
        self._load_class(class_file)

    def _load_class(self, class_file: str):
        """Load a class from file."""
        self.current_class_file = class_file

        try:
            classes_dir = get_data_path() / "classes"
            file_path = classes_dir / class_file
            self.students = self.student_repo.load_from_file(file_path)
            self._update_student_tree()
        except Exception as e:
            show_error(self, self.t("read_error_title"), self.t("read_error_message", e=str(e)))

    def _update_student_tree(self):
        """Update the student treeview with current students."""
        for item in self.student_tree.get_children():
            self.student_tree.delete(item)

        for student in self.students:
            self.student_tree.insert("", tk.END, values=(student.student_name, student.student_id))

    def _clear_student_view(self):
        """Clear the student tree and reset state."""
        self.current_class_file = None
        self.students = []

        for item in self.student_tree.get_children():
            self.student_tree.delete(item)

        self.name_entry.delete(0, tk.END)
        self.id_entry.delete(0, tk.END)

    def _add_student(self):
        """Add a new student to the current class."""
        name = self.name_entry.get().strip()
        student_id = self.id_entry.get().strip()

        if not name or not student_id:
            show_warning(
                self, self.t("empty_fields_warning_title"), self.t("empty_fields_warning_message")
            )
            return

        student = Student(student_name=name, student_id=student_id)

        try:
            validate_student(student)
        except ValidationError as e:
            show_error(self, self.t("invalid_id_warning"), str(e))
            return

        if any(s.student_id == student_id for s in self.students):
            show_warning(self, self.t("id_exists_warning"), self.t("id_exists_message"))
            return

        self.students.append(student)
        self._update_student_tree()

        self.name_entry.delete(0, tk.END)
        self.id_entry.delete(0, tk.END)

    def _remove_student(self):
        """Remove selected students from the current class."""
        selection = self.student_tree.selection()

        if not selection:
            show_warning(
                self, self.t("no_selection_warning"), self.t("no_student_selection_warning_message")
            )
            return

        if not ask_yes_no(self, self.t("confirm_removal_title"), self.t("confirm_removal_message")):
            return

        indices_to_remove = []
        for item in selection:
            values = self.student_tree.item(item)["values"]
            for i, student in enumerate(self.students):
                if student.student_id == values[1]:
                    indices_to_remove.append(i)
                    break

        for i in sorted(indices_to_remove, reverse=True):
            del self.students[i]

        self._update_student_tree()

    def _save_class(self):
        """Save the current class to file."""
        if not self.current_class_file:
            show_warning(self, self.t("no_class_warning_title"), self.t("no_class_warning_message"))
            return

        try:
            validate_roster(self.students)
        except ValidationError as e:
            show_error(self, self.t("invalid_id_warning"), str(e))
            return

        try:
            classes_dir = get_data_path() / "classes"
            file_path = classes_dir / self.current_class_file
            self.student_repo.save_to_file(self.students, file_path)

            show_info(
                self,
                self.t("success_title"),
                self.t("save_success_message", name=self.current_class_file),
            )
        except Exception as e:
            show_error(self, self.t("save_error_title"), self.t("save_error_message", e=str(e)))

    def _delete_class(self):
        """Delete the selected class."""
        selection = self.class_listbox.curselection()
        if not selection:
            show_warning(
                self, self.t("no_selection_warning"), self.t("delete_class_selection_warning")
            )
            return

        class_name = self.class_listbox.get(selection[0])

        if not ask_yes_no(
            self,
            self.t("confirm_deletion_title"),
            self.t("confirm_delete_class_message", name=class_name),
        ):
            return

        try:
            self.student_repo.delete(class_name)
            show_info(
                self, self.t("success_title"), self.t("class_deleted_message", name=class_name)
            )

            self._load_class_list()
            self._clear_student_view()

            if self.templates_tab and hasattr(self.templates_tab, "refresh_class_list"):
                self.templates_tab.refresh_class_list()

        except Exception as e:
            show_error(self, self.t("save_error_title"), self.t("delete_error_message", e=str(e)))

    def _new_class(self):
        """Create a new class file."""
        filename = ask_string(
            self, self.t("new_class_dialog_title"), self.t("new_class_dialog_prompt")
        )

        if not filename:
            return

        if not filename.endswith(".csv"):
            filename += ".csv"

        classes_dir = get_data_path() / "classes"
        file_path = classes_dir / filename

        if file_path.exists():
            show_warning(
                self, self.t("file_exists_warning_title"), self.t("file_exists_warning_message")
            )
            return

        try:
            self.student_repo.save_to_file([], file_path)

            show_info(
                self, self.t("success_title"), self.t("create_success_message", name=filename)
            )

            self._load_class_list()

            if self.templates_tab and hasattr(self.templates_tab, "refresh_class_list"):
                self.templates_tab.refresh_class_list()

            for i in range(self.class_listbox.size()):
                if self.class_listbox.get(i) == filename:
                    self.class_listbox.selection_clear(0, tk.END)
                    self.class_listbox.selection_set(i)
                    self.class_listbox.see(i)
                    self._load_class(filename)
                    break

        except Exception as e:
            show_error(self, self.t("create_error_title"), self.t("create_error_message", e=str(e)))
