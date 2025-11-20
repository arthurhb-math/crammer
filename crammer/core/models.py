from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class Difficulty(Enum):
    """Question difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

    @classmethod
    def from_string(cls, value: Optional[str]) -> Optional["Difficulty"]:
        """Convert string to Difficulty enum, return None if invalid."""
        if not value:
            return None
        try:
            return cls(value.lower())
        except (ValueError, AttributeError):
            return None


@dataclass
class QuestionImage:
    """Image attached to a question."""

    path: str
    width_cm: float = 10.0
    position: str = "above"
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "path": self.path,
            "width_cm": self.width_cm,
            "position": self.position,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuestionImage":
        """Create from dictionary."""
        return cls(
            path=data["path"],
            width_cm=data.get("width_cm", 10.0),
            position=data.get("position", "above"),
            description=data.get("description"),
        )


@dataclass
class Question:
    """A question in the question bank."""

    question_id: str
    prompt: str
    topics: List[str]
    difficulty: Optional[Difficulty] = None
    notes: Optional[str] = None
    image: Optional[QuestionImage] = None

    def __post_init__(self):
        """Post-initialization processing."""
        if isinstance(self.topics, str):
            self.topics = [t.strip() for t in self.topics.split(",") if t.strip()]

        if isinstance(self.difficulty, str):
            self.difficulty = Difficulty.from_string(self.difficulty)

    def has_topic(self, topic: str) -> bool:
        """Check if question has a specific topic."""
        return topic.lower() in [t.lower() for t in self.topics]

    def matches_difficulty(self, difficulty: Difficulty) -> bool:
        """Check if question matches specified difficulty."""
        return self.difficulty == difficulty

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            "question_id": self.question_id,
            "prompt": self.prompt,
            "topics": self.topics,
        }

        if self.difficulty:
            data["difficulty"] = self.difficulty.value

        if self.notes:
            data["notes"] = self.notes

        if self.image:
            data["image"] = self.image.to_dict()

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Question":
        """Create Question from dictionary."""
        image_data = data.get("image")
        image = QuestionImage.from_dict(image_data) if image_data else None

        return cls(
            question_id=data["question_id"],
            prompt=data["prompt"],
            topics=data["topics"],
            difficulty=Difficulty.from_string(data.get("difficulty")),
            notes=data.get("notes"),
            image=image,
        )


@dataclass
class Student:
    """A student in a class roster."""

    student_name: str
    student_id: str

    @property
    def sanitized_name(self) -> str:
        """Get sanitized name suitable for filenames."""
        return self.student_name.replace(" ", "_").lower()

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for serialization."""
        return {
            "student_name": self.student_name,
            "student_id": self.student_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Student":
        """Create Student from dictionary."""
        return cls(
            student_name=data["student_name"],
            student_id=data["student_id"],
        )


@dataclass
class SelectionBlock:
    """A block of questions to be selected for an assessment."""

    title: str
    method: str
    quantity: Optional[int] = None
    topic: Optional[str] = None
    difficulty: Optional[Difficulty] = None
    question_ids: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Post-initialization processing."""
        if isinstance(self.difficulty, str):
            self.difficulty = Difficulty.from_string(self.difficulty)

        if isinstance(self.question_ids, str):
            self.question_ids = [qid.strip() for qid in self.question_ids.split(",") if qid.strip()]

    def validate(self) -> bool:
        """Validate that the selection block has required fields for its method."""
        if self.method == "manual":
            return len(self.question_ids) > 0
        elif self.method == "random_all":
            return self.quantity is not None and self.quantity > 0
        elif self.method == "random_topic":
            return self.quantity is not None and self.quantity > 0 and self.topic is not None
        elif self.method == "random_difficulty":
            return self.quantity is not None and self.quantity > 0 and self.difficulty is not None
        elif self.method == "random_type":
            return False
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            "title": self.title,
            "method": self.method,
        }

        if self.quantity is not None:
            data["quantity"] = self.quantity

        if self.topic:
            data["topic"] = self.topic

        if self.difficulty:
            data["difficulty"] = self.difficulty.value

        if self.question_ids:
            data["question_ids"] = self.question_ids

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SelectionBlock":
        """Create SelectionBlock from dictionary."""
        return cls(
            title=data["title"],
            method=data["method"],
            quantity=data.get("quantity"),
            topic=data.get("topic"),
            difficulty=Difficulty.from_string(data.get("difficulty")),
            question_ids=data.get("question_ids", []),
        )


@dataclass
class Template:
    """An assessment template configuration."""

    name: str
    document_title: str
    filename_prefix: str
    course_info: Dict[str, str]
    selection_blocks: List[SelectionBlock]
    logo_path: Optional[str] = None
    csv_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "document_settings": {
                "document_title": self.document_title,
                "filename_prefix": self.filename_prefix,
            },
            "course_info": self.course_info,
            "student_info": {
                "csv_path": self.csv_path,
            },
            "question_selection": {
                "blocks": [block.to_dict() for block in self.selection_blocks],
            },
            "logo_path": self.logo_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Template":
        """Create Template from dictionary."""
        doc_settings = data.get("document_settings", {})
        student_info = data.get("student_info", {})
        question_selection = data.get("question_selection", {})

        blocks_data = question_selection.get("blocks", [])
        blocks = [SelectionBlock.from_dict(b) for b in blocks_data]

        return cls(
            name=data.get("name", "Unnamed Template"),
            document_title=doc_settings.get("document_title", ""),
            filename_prefix=doc_settings.get("filename_prefix", "assessment"),
            course_info=data.get("course_info", {}),
            selection_blocks=blocks,
            logo_path=data.get("logo_path"),
            csv_path=student_info.get("csv_path"),
        )
