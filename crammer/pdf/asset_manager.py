"""
Asset management for assessments.

Handles copying images and other resources to output directories.
"""

import shutil
from pathlib import Path
from typing import List, Optional

from crammer.core.models import Question
from crammer.utils.logger import get_logger

logger = get_logger(__name__)


class AssetManager:
    """Manages assets (images, logos) for assessment generation."""

    def __init__(self, assets_dir: Path):
        """
        Initialize asset manager.

        Args:
            assets_dir: Directory where assets will be copied
        """
        self.assets_dir = Path(assets_dir)
        self.assets_dir.mkdir(parents=True, exist_ok=True)

    def copy_question_images(self, questions: List[Question]) -> None:
        """
        Copy images for questions to assets directory.

        Updates question image paths to relative paths.

        Args:
            questions: List of questions that may have images
        """
        for question in questions:
            if question.image and question.image.path:
                self._copy_image(question.image.path, question)

    def copy_logo(self, logo_path: str) -> Optional[str]:
        """
        Copy logo file to assets directory.

        Args:
            logo_path: Path to logo file

        Returns:
            Relative path to copied logo, or None if copy failed
        """
        if not logo_path:
            return None

        source_path = Path(logo_path)

        if not source_path.exists():
            logger.warning(f"Logo file not found: {logo_path}")
            return None

        try:
            dest_path = self.assets_dir / source_path.name
            shutil.copy2(source_path, dest_path)
            logger.debug(f"Copied logo: {source_path.name}")
            return source_path.name

        except Exception as e:
            logger.error(f"Failed to copy logo {logo_path}: {e}")
            return None

    def _copy_image(self, image_path: str, question: Question) -> None:
        """
        Copy image file to assets directory.

        Updates the question's image path to relative path.

        Args:
            image_path: Path to image file
            question: Question object to update
        """
        source_path = Path(image_path)

        if not source_path.exists():
            logger.warning(f"Image file not found: {image_path}")
            return

        try:
            dest_path = self.assets_dir / source_path.name
            shutil.copy2(source_path, dest_path)

            if question.image:
                question.image.path = source_path.name

            logger.debug(f"Copied image for question {question.question_id}: {source_path.name}")

        except Exception as e:
            logger.error(f"Failed to copy image {image_path}: {e}")

    def get_asset_path(self, filename: str) -> Path:
        """
        Get full path to an asset file.

        Args:
            filename: Asset filename

        Returns:
            Full path to asset
        """
        return self.assets_dir / filename

    def clear_assets(self) -> None:
        """Remove all assets from the assets directory."""
        if self.assets_dir.exists():
            try:
                shutil.rmtree(self.assets_dir)
                self.assets_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Cleared assets directory: {self.assets_dir}")
            except Exception as e:
                logger.error(f"Failed to clear assets directory: {e}")
