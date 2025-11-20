import random
from typing import List, Set
from .models import Question, SelectionBlock, Difficulty


class QuestionSelector:
    """Handles question selection based on various criteria."""

    def __init__(self, all_questions: List[Question]):
        """
        Initialize the selector with a question bank.

        Args:
            all_questions: Complete list of available questions
        """
        self.all_questions = all_questions
        self._questions_by_id = {q.question_id: q for q in all_questions}

    def select_for_block(self, block: SelectionBlock, used_ids: Set[str]) -> List[Question]:
        """
        Select questions for a selection block.

        Args:
            block: SelectionBlock defining selection criteria
            used_ids: Set of question IDs already used (to avoid duplicates)

        Returns:
            List of selected questions
        """
        if block.method == "manual":
            return self._select_manual(block.question_ids, used_ids)

        elif block.method == "random_all":
            return self._select_random_all(block.quantity, used_ids)

        elif block.method == "random_topic":
            return self._select_random_topic(block.topic, block.quantity, used_ids)

        elif block.method == "random_difficulty":
            return self._select_random_difficulty(block.difficulty, block.quantity, used_ids)

        else:
            return []

    def _select_manual(self, question_ids: List[str], used_ids: Set[str]) -> List[Question]:
        """
        Select questions by explicit IDs.

        Args:
            question_ids: List of question IDs to select
            used_ids: Set of already used IDs

        Returns:
            List of selected questions (only those not already used and that exist)
        """
        selected = []
        for qid in question_ids:
            if qid not in used_ids and qid in self._questions_by_id:
                selected.append(self._questions_by_id[qid])
        return selected

    def _select_random_all(self, quantity: int, used_ids: Set[str]) -> List[Question]:
        """
        Select random questions from entire database.

        Args:
            quantity: Number of questions to select
            used_ids: Set of already used IDs

        Returns:
            List of randomly selected questions
        """
        available = [q for q in self.all_questions if q.question_id not in used_ids]

        if not available:
            return []

        sample_size = min(quantity, len(available))
        return random.sample(available, sample_size)

    def _select_random_topic(self, topic: str, quantity: int, used_ids: Set[str]) -> List[Question]:
        """
        Select random questions filtered by topic.

        Args:
            topic: Topic to filter by
            quantity: Number of questions to select
            used_ids: Set of already used IDs

        Returns:
            List of randomly selected questions with the specified topic
        """
        available = [
            q for q in self.all_questions if q.question_id not in used_ids and q.has_topic(topic)
        ]

        if not available:
            return []

        sample_size = min(quantity, len(available))
        return random.sample(available, sample_size)

    def _select_random_difficulty(
        self, difficulty: Difficulty, quantity: int, used_ids: Set[str]
    ) -> List[Question]:
        """
        Select random questions filtered by difficulty.

        Args:
            difficulty: Difficulty level to filter by
            quantity: Number of questions to select
            used_ids: Set of already used IDs

        Returns:
            List of randomly selected questions with the specified difficulty
        """
        available = [
            q
            for q in self.all_questions
            if q.question_id not in used_ids and q.matches_difficulty(difficulty)
        ]

        if not available:
            return []

        sample_size = min(quantity, len(available))
        return random.sample(available, sample_size)

    def get_available_topics(self) -> List[str]:
        """
        Get list of all unique topics in the question bank.

        Returns:
            Sorted list of unique topics
        """
        topics = set()
        for question in self.all_questions:
            topics.update(question.topics)
        return sorted(topics)

    def get_available_types(self) -> List[str]:
        """
        Get list of all unique question types in the question bank.

        Returns:
            Sorted list of unique question types
        """
        types = {q.question_type for q in self.all_questions}
        return sorted(types)

    def get_questions_by_topic(self, topic: str) -> List[Question]:
        """
        Get all questions with a specific topic.

        Args:
            topic: Topic to filter by

        Returns:
            List of questions with the specified topic
        """
        return [q for q in self.all_questions if q.has_topic(topic)]

    def get_questions_by_difficulty(self, difficulty: Difficulty) -> List[Question]:
        """
        Get all questions with a specific difficulty.

        Args:
            difficulty: Difficulty level to filter by

        Returns:
            List of questions with the specified difficulty
        """
        return [q for q in self.all_questions if q.matches_difficulty(difficulty)]


def select_questions_for_template(
    all_questions: List[Question], selection_blocks: List[SelectionBlock]
) -> List[dict]:
    """
    Select questions for all blocks in a template.

    Args:
        all_questions: Complete question bank
        selection_blocks: List of selection blocks from template

    Returns:
        List of dicts with 'title' and 'questions' keys for each block
    """
    selector = QuestionSelector(all_questions)
    used_ids: Set[str] = set()

    result = []

    for block in selection_blocks:
        selected_questions = selector.select_for_block(block, used_ids)

        for q in selected_questions:
            used_ids.add(q.question_id)

        result.append({"title": block.title, "questions": selected_questions})

    return result
