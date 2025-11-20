from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path

from crammer.core.models import Question, Student, Template, Difficulty


class QuestionRepository(ABC):
    """Abstract interface for question persistence."""

    @abstractmethod
    def get_all(self) -> List[Question]:
        """
        Get all questions from the repository.

        Returns:
            List of all Question objects
        """
        pass

    @abstractmethod
    def get_by_id(self, question_id: str) -> Optional[Question]:
        """
        Get a question by its ID.

        Args:
            question_id: Unique question identifier

        Returns:
            Question if found, None otherwise
        """
        pass

    @abstractmethod
    def save(self, question: Question) -> None:
        """
        Save a question (create or update).

        Args:
            question: Question to save
        """
        pass

    @abstractmethod
    def delete(self, question_id: str) -> bool:
        """
        Delete a question by ID.

        Args:
            question_id: ID of question to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def get_by_topic(self, topic: str) -> List[Question]:
        """
        Get all questions with a specific topic.

        Args:
            topic: Topic to filter by

        Returns:
            List of questions with the specified topic
        """
        pass

    @abstractmethod
    def get_by_difficulty(self, difficulty: Difficulty) -> List[Question]:
        """
        Get all questions with a specific difficulty.

        Args:
            difficulty: Difficulty level to filter by

        Returns:
            List of questions with the specified difficulty
        """
        pass

    @abstractmethod
    def get_by_type(self, question_type: str) -> List[Question]:
        """
        Get all questions with a specific type.

        Args:
            question_type: Question type to filter by

        Returns:
            List of questions with the specified type
        """
        pass

    @abstractmethod
    def get_all_topics(self) -> List[str]:
        """
        Get list of all unique topics.

        Returns:
            Sorted list of unique topics
        """
        pass

    @abstractmethod
    def get_all_types(self) -> List[str]:
        """
        Get list of all unique question types.

        Returns:
            Sorted list of unique question types
        """
        pass


class StudentRepository(ABC):
    """Abstract interface for student roster persistence."""

    @abstractmethod
    def load_from_file(self, file_path: Path) -> List[Student]:
        """
        Load students from a file.

        Args:
            file_path: Path to the student roster file

        Returns:
            List of Student objects
        """
        pass

    @abstractmethod
    def save_to_file(self, students: List[Student], file_path: Path) -> None:
        """
        Save students to a file.

        Args:
            students: List of students to save
            file_path: Path to save the file
        """
        pass

    @abstractmethod
    def get_available_rosters(self) -> List[str]:
        """
        Get list of available roster files.

        Returns:
            List of roster filenames
        """
        pass

    @abstractmethod
    def get_available_rosters(self) -> List[str]:
        """
        Get list of available roster files.

        Returns:
            List of roster filenames
        """
        pass

    @abstractmethod
    def delete(self, name: str) -> bool:
        """
        Delete a student roster by name.

        Args:
            name: Filename of the roster to delete

        Returns:
            True if deleted, False if not found
        """
        pass


class TemplateRepository(ABC):
    """Abstract interface for template persistence."""

    @abstractmethod
    def get_all(self) -> List[str]:
        """
        Get list of all template names.

        Returns:
            List of template names
        """
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Template]:
        """
        Get a template by name.

        Args:
            name: Template name

        Returns:
            Template if found, None otherwise
        """
        pass

    @abstractmethod
    def save(self, template: Template) -> None:
        """
        Save a template (create or update).

        Args:
            template: Template to save
        """
        pass

    @abstractmethod
    def delete(self, name: str) -> bool:
        """
        Delete a template by name.

        Args:
            name: Name of template to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def load_from_py_file(self, file_path: Path) -> Template:
        """
        Load a template from a Python config file (legacy format).

        Args:
            file_path: Path to Python config file

        Returns:
            Template object
        """
        pass
