import csv
from pathlib import Path
from typing import List

from crammer.core.models import Student
from crammer.utils.logger import get_logger
from .repositories import StudentRepository

logger = get_logger(__name__)


class CsvStudentRepository(StudentRepository):
    """CSV file-based student repository."""

    def __init__(self, rosters_dir: Path):
        """
        Initialize repository with rosters directory.

        Args:
            rosters_dir: Directory containing CSV roster files
        """
        self.rosters_dir = Path(rosters_dir)
        self.rosters_dir.mkdir(parents=True, exist_ok=True)

    def load_from_file(self, file_path: Path) -> List[Student]:
        """
        Load students from a CSV file.

        Expected CSV format:
        student_name,student_id
        João Silva,2023001
        Maria Santos,2023002

        Args:
            file_path: Path to CSV file

        Returns:
            List of Student objects
        """
        students = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    try:
                        student = Student(
                            student_name=row["student_name"], student_id=row["student_id"]
                        )
                        students.append(student)
                    except KeyError as e:
                        logger.warning(f"Missing field in CSV row: {e}")
                    except Exception as e:
                        logger.warning(f"Failed to parse student row: {e}")

            logger.info(f"Loaded {len(students)} students from {file_path.name}")

        except FileNotFoundError:
            logger.error(f"CSV file not found: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {e}")
            raise

        return students

    def save_to_file(self, students: List[Student], file_path: Path) -> None:
        """
        Save students to a CSV file.

        Args:
            students: List of students to save
            file_path: Path to save CSV file
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["student_name", "student_id"])
                writer.writeheader()

                for student in students:
                    writer.writerow(student.to_dict())

            logger.info(f"Saved {len(students)} students to {file_path.name}")

        except Exception as e:
            logger.error(f"Error writing CSV file {file_path}: {e}")
            raise

    def get_available_rosters(self) -> List[str]:
        """
        Get list of available roster files in the rosters directory.

        Returns:
            List of CSV filenames (without path)
        """
        if not self.rosters_dir.exists():
            return []

        rosters = []
        for csv_file in self.rosters_dir.glob("*.csv"):
            rosters.append(csv_file.name)

        return sorted(rosters)

    def delete(self, name: str) -> bool:
        """Delete a roster CSV file by name."""
        file_path = self.rosters_dir / name

        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Deleted class {name}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete class {name}: {e}")
                raise

        return False
