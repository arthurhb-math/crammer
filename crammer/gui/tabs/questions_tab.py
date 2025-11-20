import tkinter as tk
from tkinter import ttk, filedialog
import os
from pathlib import Path

from crammer.i18n import get_translator
from crammer.core.models import Question, QuestionImage, Difficulty
from crammer.core.validator import validate_question, ValidationError
from crammer.data.json_store import JsonQuestionRepository
from crammer.utils.paths import get_data_path, get_resources_path
from crammer.gui.dialogs import show_error, show_info, show_warning, ask_yes_no
import json


class QuestionsTab(ttk.Frame):
    """Tab for managing the question bank."""

    def __init__(self, parent, app):
        """
        Initialize the Questions tab.

        Args:
            parent: Parent notebook widget
            app: Main application instance
        """
        super().__init__(parent)
        self.app = app
        self.t = get_translator()

        questions_dir = get_data_path() / "questions"
        self.question_repo = JsonQuestionRepository(questions_dir)

        self.current_question_id = None
        self.current_topics_text = ""
        self.image_path = tk.StringVar()

        self._build_ui()
        self._load_questions()

    def _build_ui(self):
        """Build the tab UI."""
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_question_list(main_pane)

        self._build_question_editor(main_pane)

    def _build_question_list(self, parent):
        """Build the question list panel."""
        list_frame = ttk.LabelFrame(parent, text=self.t("saved_questions_frame"))
        parent.add(list_frame, weight=2)

        self.question_listbox = tk.Listbox(list_frame)
        self.question_listbox.pack(fill="both", expand=True, side="left")
        self.question_listbox.bind("<<ListboxSelect>>", self._on_question_select)

        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.question_listbox.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.question_listbox.config(yscrollcommand=scrollbar.set)

    def _build_question_editor(self, parent):
        """Build the question editor panel."""
        editor_frame = ttk.LabelFrame(parent, text=self.t("question_editor_frame"))
        parent.add(editor_frame, weight=5)

        editor_frame.columnconfigure(1, weight=1)

        required_keys = ["question_id_label", "prompt_label"]
        required_labels = [self.t(key) for key in required_keys]

        fields = {
            self.t("question_id_label"): "id_entry",
            self.t("topics_label"): "topics_combobox",
            self.t("difficulty_label"): "difficulty_combobox",
            self.t("prompt_label"): "prompt_text",
            self.t("notes_label"): "notes_text",
        }

        for i, (label_text, widget_name) in enumerate(fields.items()):
            label_frame = ttk.Frame(editor_frame)
            label_frame.grid(row=i, column=0, sticky="w", padx=5, pady=2)

            main_label = ttk.Label(label_frame, text=label_text)
            main_label.pack(side="left")

            if label_text in required_labels:
                asterisk_label = ttk.Label(label_frame, text="*", foreground="red")
                asterisk_label.pack(side="left")

            widget = None
            if widget_name == "id_entry":
                self.id_entry = ttk.Entry(editor_frame)
                widget = self.id_entry
            elif widget_name.endswith("_combobox"):
                combobox = ttk.Combobox(editor_frame)
                setattr(self, widget_name, combobox)
                widget = combobox
            elif widget_name.endswith("_text"):
                height = 8 if "prompt" in widget_name else 3
                text_widget = tk.Text(
                    editor_frame,
                    height=height,
                    wrap=tk.WORD,
                    undo=True,
                    relief=tk.SOLID,
                    borderwidth=1,
                )
                setattr(self, widget_name, text_widget)
                widget = text_widget

            if widget:
                if isinstance(widget, tk.Text):
                    widget.grid(row=i, column=1, sticky="nsew", padx=5, pady=2)
                    editor_frame.rowconfigure(i, weight=1)
                else:
                    widget.grid(row=i, column=1, sticky="ew", padx=5, pady=2)

        self.topics_combobox.bind("<<ComboboxSelected>>", self._on_topic_select)
        self.topics_combobox.bind("<KeyRelease>", self._on_topic_key_release)

        self.difficulty_combobox["values"] = ["easy", "medium", "hard"]
        self.difficulty_combobox["state"] = "readonly"

        self._build_image_options(editor_frame, len(fields))

        button_frame = ttk.Frame(editor_frame)
        button_frame.grid(row=len(fields) + 1, column=0, columnspan=2, sticky="ew", padx=5, pady=10)

        ttk.Button(button_frame, text=self.t("new_button"), command=self._clear_form).pack(
            side="left", padx=5
        )

        ttk.Button(
            button_frame, text=self.t("save_question_button"), command=self._save_question
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame, text=self.t("delete_selected_button"), command=self._delete_question
        ).pack(side="right", padx=5)

    def _build_image_options(self, parent, row):
        """Build image options section."""
        image_frame = ttk.LabelFrame(parent, text=self.t("image_options_frame"), padding="5")
        image_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=(10, 5))

        select_frame = ttk.Frame(image_frame)
        select_frame.pack(fill="x", expand=True)

        ttk.Button(
            select_frame, text=self.t("select_image_button"), command=self._select_image
        ).pack(side="left", padx=(0, 5))

        self.image_label = ttk.Label(
            select_frame, text=self.t("no_image_selected"), width=50, anchor="w"
        )
        self.image_label.pack(side="left", fill="x", expand=True)

        settings_frame = ttk.Frame(image_frame)
        settings_frame.pack(fill="x", expand=True, pady=(5, 0))

        ttk.Label(settings_frame, text=self.t("image_width_label"), width=15).pack(side="left")
        self.image_width_spinbox = ttk.Spinbox(settings_frame, from_=1, to=20, width=5)
        self.image_width_spinbox.pack(side="left", padx=5)
        self.image_width_spinbox.set("10")

        ttk.Label(settings_frame, text=self.t("image_position_label"), width=15).pack(side="left")
        self.image_pos_combobox = ttk.Combobox(
            settings_frame,
            values=[
                self.t("position_left"),
                self.t("position_right"),
                self.t("position_above"),
                self.t("position_below"),
            ],
            state="readonly",
            width=10,
        )
        self.image_pos_combobox.pack(side="left", padx=5)
        self.image_pos_combobox.set(self.t("position_above"))

        desc_frame = ttk.Frame(image_frame)
        desc_frame.pack(fill="x", expand=True, pady=(5, 0))

        ttk.Label(desc_frame, text=self.t("image_description_label"), width=28).pack(side="left")
        self.image_description_entry = ttk.Entry(desc_frame)
        self.image_description_entry.pack(side="left", fill="x", expand=True)

    def _load_questions(self):
        """Load questions from repository and update UI."""
        questions = self.question_repo.get_all()

        self.question_listbox.delete(0, tk.END)
        for question in sorted(questions, key=lambda q: q.question_id):
            self.question_listbox.insert(tk.END, question.question_id)

        self._update_combobox_options()

    def _update_combobox_options(self):
        """Update combobox options from current question bank."""
        all_topics = self.question_repo.get_all_topics()
        self.topics_combobox["values"] = all_topics

    def _on_question_select(self, event):
        """Handle question selection from list."""
        selection = self.question_listbox.curselection()
        if not selection:
            return

        selected_id = self.question_listbox.get(selection[0])
        question = self.question_repo.get_by_id(selected_id)

        if question:
            self._load_question_to_form(question)

    def _load_question_to_form(self, question: Question):
        """Load a question into the edit form."""
        self._clear_form(clear_id=False)

        self.id_entry.config(state="normal")
        self.id_entry.delete(0, tk.END)
        self.id_entry.insert(0, question.question_id)
        self.id_entry.config(state="disabled")
        self.current_question_id = question.question_id

        topics_str = ", ".join(question.topics)
        self.topics_combobox.set(topics_str)
        self.current_topics_text = topics_str

        if question.difficulty:
            self.difficulty_combobox.set(question.difficulty.value)

        self.prompt_text.insert("1.0", question.prompt)

        if question.notes:
            self.notes_text.insert("1.0", question.notes)

        if question.image:
            self._load_image_to_form(question.image)
        else:
            self._clear_image_form()

    def _load_image_to_form(self, image: QuestionImage):
        """Load image information to form."""
        self.image_path.set(image.path)
        self.image_label.config(text=os.path.basename(image.path))
        self.image_width_spinbox.set(str(image.width_cm))

        pos_map = {
            "left": self.t("position_left"),
            "right": self.t("position_right"),
            "above": self.t("position_above"),
            "below": self.t("position_below"),
        }
        self.image_pos_combobox.set(pos_map.get(image.position, self.t("position_above")))

        if image.description:
            self.image_description_entry.delete(0, tk.END)
            self.image_description_entry.insert(0, image.description)

    def _clear_image_form(self):
        """Clear image form fields."""
        self.image_path.set("")
        self.image_label.config(text=self.t("no_image_selected"))
        self.image_width_spinbox.set("10")
        self.image_pos_combobox.set(self.t("position_above"))
        self.image_description_entry.delete(0, tk.END)

    def _on_topic_key_release(self, event=None):
        """Handle key release in topics combobox."""
        self.current_topics_text = self.topics_combobox.get()

    def _on_topic_select(self, event=None):
        """Handle topic selection from combobox."""
        selected_topic = self.topics_combobox.get()
        topic_list = [t.strip() for t in self.current_topics_text.split(",") if t.strip()]

        if selected_topic and selected_topic not in topic_list:
            new_text = (
                f"{self.current_topics_text}, {selected_topic}"
                if self.current_topics_text.strip()
                else selected_topic
            )
            self.topics_combobox.set(new_text)
            self.current_topics_text = new_text

    def _clear_form(self, clear_id=True):
        """Clear the question form."""
        self.id_entry.config(state="normal")
        if clear_id:
            self.id_entry.delete(0, tk.END)
            self.current_question_id = None
            self.question_listbox.selection_clear(0, tk.END)

        self.topics_combobox.set("")
        self.current_topics_text = ""
        self.difficulty_combobox.set("")
        self.prompt_text.delete("1.0", tk.END)
        self.notes_text.delete("1.0", tk.END)

        self._clear_image_form()

    def _select_image(self):
        """Open file dialog to select an image."""
        filepath = filedialog.askopenfilename(
            title=self.t("select_image_button"),
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.svg"), ("All files", "*.*")],
        )

        if filepath:
            self.image_path.set(filepath)
            self.image_label.config(text=os.path.basename(filepath))

    def _save_question(self):
        """Save the current question."""
        try:
            question = self._build_question_from_form()
        except ValueError as e:
            show_error(self, self.t("invalid_type_warning"), str(e))
            return

        existing_ids = [q.question_id for q in self.question_repo.get_all()]
        if self.current_question_id:
            existing_ids = [qid for qid in existing_ids if qid != self.current_question_id]

        try:
            validate_question(question, existing_ids)
        except ValidationError as e:
            show_error(self, self.t("invalid_id_warning"), str(e))
            return

        try:
            self.question_repo.save(question)
            show_info(
                self,
                self.t("success_title"),
                self.t("question_saved_message", q_id=question.question_id),
            )
            self._load_questions()
            self._clear_form()
        except Exception as e:
            show_error(self, self.t("save_error_title"), str(e))

    def _build_question_from_form(self) -> Question:
        """Build a Question object from form data."""
        question_id = self.id_entry.get().strip()

        topics_str = self.topics_combobox.get()
        topics = [t.strip() for t in topics_str.split(",") if t.strip()]

        difficulty_str = self.difficulty_combobox.get()
        difficulty = Difficulty.from_string(difficulty_str) if difficulty_str else None

        prompt = self.prompt_text.get("1.0", tk.END).strip()
        notes = self.notes_text.get("1.0", tk.END).strip() or None

        image = None
        if self.image_path.get():
            pos_reverse = {
                self.t("position_left"): "left",
                self.t("position_right"): "right",
                self.t("position_above"): "above",
                self.t("position_below"): "below",
            }
            position = pos_reverse.get(self.image_pos_combobox.get(), "above")

            image = QuestionImage(
                path=self.image_path.get(),
                width_cm=float(self.image_width_spinbox.get()),
                position=position,
                description=self.image_description_entry.get().strip() or None,
            )

        return Question(
            question_id=question_id,
            topics=topics,
            prompt=prompt,
            difficulty=difficulty,
            notes=notes,
            image=image,
        )

    def _delete_question(self):
        """Delete the selected question."""
        if not self.current_question_id:
            show_warning(
                self, self.t("no_selection_warning"), self.t("select_question_to_delete_message")
            )
            return

        if not ask_yes_no(
            self,
            self.t("confirm_deletion_title"),
            self.t("confirm_deletion_message", q_id=self.current_question_id),
        ):
            return

        try:
            self.question_repo.delete(self.current_question_id)
            show_info(
                self,
                self.t("success_title"),
                self.t("question_deleted_message", q_id=self.current_question_id),
            )
            self._load_questions()
            self._clear_form()
        except Exception as e:
            show_error(self, self.t("save_error_title"), str(e))
