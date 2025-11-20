import json
import os
from pathlib import Path
from typing import List, Optional

from crammer.core.models import Question, Template, Difficulty
from crammer.utils.logger import get_logger
from .repositories import QuestionRepository, TemplateRepository

logger = get_logger(__name__)


class JsonQuestionRepository(QuestionRepository):
    """JSON file-based question repository."""

    def __init__(self, questions_dir: Path):
        """
        Initialize repository with questions directory.

        Args:
            questions_dir: Directory containing question JSON files
        """
        self.questions_dir = Path(questions_dir)
        self.questions_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Optional[List[Question]] = None

    def _load_all_questions(self) -> List[Question]:
        """Load all questions from JSON files."""
        questions = []

        if not self.questions_dir.exists():
            return questions

        for json_file in self.questions_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    if isinstance(data, list):
                        for item in data:
                            try:
                                questions.append(Question.from_dict(item))
                            except Exception as e:
                                logger.warning(f"Failed to load question from {json_file}: {e}")
                    elif isinstance(data, dict) and "question_id" in data:
                        try:
                            questions.append(Question.from_dict(data))
                        except Exception as e:
                            logger.warning(f"Failed to load question from {json_file}: {e}")

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse {json_file}: {e}")
            except Exception as e:
                logger.error(f"Error reading {json_file}: {e}")

        return questions

    def _invalidate_cache(self) -> None:
        """Invalidate the cache."""
        self._cache = None

    def get_all(self) -> List[Question]:
        """Get all questions."""
        if self._cache is None:
            self._cache = self._load_all_questions()
        return self._cache.copy()

    def get_by_id(self, question_id: str) -> Optional[Question]:
        """Get a question by ID."""
        questions = self.get_all()
        for q in questions:
            if q.question_id == question_id:
                return q
        return None

    def save(self, question: Question) -> None:
        """
        Save a question to its own JSON file.

        File is named: {question_id}.json
        """
        file_path = self.questions_dir / f"{question.question_id}.json"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(question.to_dict(), f, indent=2, ensure_ascii=False)

            self._invalidate_cache()
            logger.info(f"Saved question {question.question_id}")

        except Exception as e:
            logger.error(f"Failed to save question {question.question_id}: {e}")
            raise

    def delete(self, question_id: str) -> bool:
        """Delete a question by ID."""
        file_path = self.questions_dir / f"{question_id}.json"

        if file_path.exists():
            try:
                file_path.unlink()
                self._invalidate_cache()
                logger.info(f"Deleted question {question_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete question {question_id}: {e}")
                raise

        return False

    def get_by_topic(self, topic: str) -> List[Question]:
        """Get questions by topic."""
        return [q for q in self.get_all() if q.has_topic(topic)]

    def get_by_difficulty(self, difficulty: Difficulty) -> List[Question]:
        """Get questions by difficulty."""
        return [q for q in self.get_all() if q.matches_difficulty(difficulty)]

    def get_by_type(self, question_type: str) -> List[Question]:
        """Get questions by type."""
        return [q for q in self.get_all() if q.question_type == question_type]

    def get_all_topics(self) -> List[str]:
        """Get all unique topics."""
        topics = set()
        for q in self.get_all():
            topics.update(q.topics)
        return sorted(topics)

    def get_all_types(self) -> List[str]:
        """Get all unique question types."""
        types = {q.question_type for q in self.get_all()}
        return sorted(types)


class JsonTemplateRepository(TemplateRepository):
    """JSON file-based template repository."""

    def __init__(self, templates_dir: Path):
        """
        Initialize repository with templates directory.

        Args:
            templates_dir: Directory containing template JSON files
        """
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def get_all(self) -> List[str]:
        """Get list of all template names."""
        if not self.templates_dir.exists():
            return []

        templates = []
        for json_file in self.templates_dir.glob("*.json"):
            templates.append(json_file.stem)

        return sorted(templates)

    def get_by_name(self, name: str) -> Optional[Template]:
        """Get a template by name."""
        file_path = self.templates_dir / f"{name}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                template = Template.from_dict(data)
                template.name = name
                return template

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse template {name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading template {name}: {e}")
            return None

    def save(self, template: Template) -> None:
        """Save a template to JSON file."""
        file_path = self.templates_dir / f"{template.name}.json"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(template.to_dict(), f, indent=2, ensure_ascii=False)

            logger.info(f"Saved template {template.name}")

        except Exception as e:
            logger.error(f"Failed to save template {template.name}: {e}")
            raise

    def delete(self, name: str) -> bool:
        """Delete a template by name."""
        file_path = self.templates_dir / f"{name}.json"

        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Deleted template {name}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete template {name}: {e}")
                raise

        return False

    def load_from_py_file(self, file_path: Path) -> Template:
        """
        Load template from legacy Python config file.

        Args:
            file_path: Path to .py config file

        Returns:
            Template object
        """
        import importlib.util

        try:
            spec = importlib.util.spec_from_file_location("config", file_path)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)

            config = {
                key: getattr(config_module, key)
                for key in dir(config_module)
                if not key.startswith("__")
            }

            name = file_path.stem

            template = Template.from_dict(config)
            template.name = name

            return template

        except Exception as e:
            logger.error(f"Failed to load Python config {file_path}: {e}")
            raise
