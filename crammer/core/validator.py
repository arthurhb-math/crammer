from typing import List, Tuple, Optional
from .models import Question, Student, Template, SelectionBlock


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


class QuestionValidator:
    """Validator for Question objects."""

    @staticmethod
    def validate(question: Question) -> Tuple[bool, Optional[str]]:
        """
        Validate a question.

        Args:
            question: Question to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not question.question_id or not question.question_id.strip():
            return False, "Question ID cannot be empty"

        if not question.topics:
            return False, "Question must have at least one topic"

        if not question.prompt or not question.prompt.strip():
            return False, "Question prompt cannot be empty"

        if question.image:
            if not question.image.path or not question.image.path.strip():
                return False, "Image path cannot be empty"

            if question.image.width_cm <= 0:
                return False, "Image width must be positive"

            valid_positions = ["above", "below", "left", "right"]
            if question.image.position not in valid_positions:
                return False, f"Image position must be one of: {', '.join(valid_positions)}"

        return True, None

    @staticmethod
    def validate_unique_id(question_id: str, existing_ids: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate that question ID is unique.

        Args:
            question_id: ID to check
            existing_ids: List of existing question IDs

        Returns:
            Tuple of (is_valid, error_message)
        """
        if question_id in existing_ids:
            return False, f"Question ID '{question_id}' already exists"

        return True, None


class StudentValidator:
    """Validator for Student objects."""

    @staticmethod
    def validate(student: Student) -> Tuple[bool, Optional[str]]:
        """
        Validate a student.

        Args:
            student: Student to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not student.student_name or not student.student_name.strip():
            return False, "Student name cannot be empty"

        if not student.student_id or not student.student_id.strip():
            return False, "Student registration number cannot be empty"

        return True, None

    @staticmethod
    def validate_roster(students: List[Student]) -> Tuple[bool, Optional[str]]:
        """
        Validate a list of students (class roster).

        Args:
            students: List of students to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not students:
            return False, "Class roster cannot be empty"

        student_ids = [s.student_id for s in students]
        if len(student_ids) != len(set(student_ids)):
            return False, "Duplicate registration numbers found in roster"

        for student in students:
            is_valid, error = StudentValidator.validate(student)
            if not is_valid:
                return False, f"Invalid student '{student.student_name}': {error}"

        return True, None


class SelectionBlockValidator:
    """Validator for SelectionBlock objects."""

    @staticmethod
    def validate(block: SelectionBlock) -> Tuple[bool, Optional[str]]:
        """
        Validate a selection block.

        Args:
            block: SelectionBlock to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not block.title or not block.title.strip():
            return False, "Block title cannot be empty"

        if block.method == "manual":
            if not block.question_ids:
                return False, "Manual selection requires at least one question ID"

        elif block.method == "random_all":
            if block.quantity is None or block.quantity <= 0:
                return False, "Random selection requires a positive quantity"

        elif block.method == "random_topic":
            if block.quantity is None or block.quantity <= 0:
                return False, "Random topic selection requires a positive quantity"
            if not block.topic or not block.topic.strip():
                return False, "Random topic selection requires a topic"

        elif block.method == "random_difficulty":
            if block.quantity is None or block.quantity <= 0:
                return False, "Random difficulty selection requires a positive quantity"
            if block.difficulty is None:
                return False, "Random difficulty selection requires a difficulty level"

        elif block.method == "random_type":
            pass

        else:
            return False, f"Unknown selection method: {block.method}"

        return True, None


class TemplateValidator:
    """Validator for Template objects."""

    @staticmethod
    def validate(template: Template) -> Tuple[bool, Optional[str]]:
        """
        Validate a template.

        Args:
            template: Template to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not template.name or not template.name.strip():
            return False, "Template name cannot be empty"

        if not template.document_title or not template.document_title.strip():
            return False, "Document title cannot be empty"

        if not template.filename_prefix or not template.filename_prefix.strip():
            return False, "Filename prefix cannot be empty"

        if not template.csv_path or not template.csv_path.strip():
            return False, "Class roster (CSV path) must be specified"

        if not template.selection_blocks:
            return False, "Template must have at least one question selection block"

        for i, block in enumerate(template.selection_blocks):
            is_valid, error = SelectionBlockValidator.validate(block)
            if not is_valid:
                return False, f"Block {i+1} ('{block.title}'): {error}"

        return True, None


def validate_question(question: Question, existing_ids: Optional[List[str]] = None) -> None:
    """
    Validate a question and raise ValidationError if invalid.

    Args:
        question: Question to validate
        existing_ids: Optional list of existing question IDs to check uniqueness

    Raises:
        ValidationError: If validation fails
    """
    is_valid, error = QuestionValidator.validate(question)
    if not is_valid:
        raise ValidationError(error)

    if existing_ids is not None:
        is_valid, error = QuestionValidator.validate_unique_id(question.question_id, existing_ids)
        if not is_valid:
            raise ValidationError(error)


def validate_student(student: Student) -> None:
    """
    Validate a student and raise ValidationError if invalid.

    Args:
        student: Student to validate

    Raises:
        ValidationError: If validation fails
    """
    is_valid, error = StudentValidator.validate(student)
    if not is_valid:
        raise ValidationError(error)


def validate_roster(students: List[Student]) -> None:
    """
    Validate a class roster and raise ValidationError if invalid.

    Args:
        students: List of students to validate

    Raises:
        ValidationError: If validation fails
    """
    is_valid, error = StudentValidator.validate_roster(students)
    if not is_valid:
        raise ValidationError(error)


def validate_selection_block(block: SelectionBlock) -> None:
    """
    Validate a selection block and raise ValidationError if invalid.

    Args:
        block: SelectionBlock to validate

    Raises:
        ValidationError: If validation fails
    """
    is_valid, error = SelectionBlockValidator.validate(block)
    if not is_valid:
        raise ValidationError(error)


def validate_template(template: Template) -> None:
    """
    Validate a template and raise ValidationError if invalid.

    Args:
        template: Template to validate

    Raises:
        ValidationError: If validation fails
    """
    is_valid, error = TemplateValidator.validate(template)
    if not is_valid:
        raise ValidationError(error)
