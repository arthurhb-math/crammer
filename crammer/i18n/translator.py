"""
Translation system for Crammer.

Provides automatic locale detection and translation loading.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional

from crammer.utils.logger import get_logger

logger = get_logger(__name__)

_translator: Optional["Translator"] = None


class Translator:
    """Handles translation of UI strings."""

    def __init__(self, lang: Optional[str] = None):
        """
        Initialize translator.

        Args:
            lang: Language code (e.g., 'en', 'pt_br'). If None, auto-detect.
        """
        if lang is None:
            lang = self._detect_locale()

        self.lang = lang
        self.translations = self._load_translations(lang)

        logger.info(f"Translator initialized with language: {lang}")

    def _detect_locale(self) -> str:
        """
        Detect system locale.

        Returns:
            Language code ('en' or 'pt_br')
        """
        for var in ["LC_ALL", "LC_MESSAGES", "LANG"]:
            lang_env = os.getenv(var, "")
            if lang_env:
                if lang_env.lower().startswith("pt"):
                    return "pt_br"
                else:
                    return "en"

        return "en"

    def _load_translations(self, lang: str) -> Dict[str, str]:
        """
        Load translations from JSON file.

        Args:
            lang: Language code

        Returns:
            Dictionary of translations
        """
        locale_dir = Path(__file__).parent / "locales"
        locale_file = locale_dir / f"{lang}.json"

        if not locale_file.exists():
            logger.warning(f"Locale file {lang}.json not found, falling back to en.json")
            locale_file = locale_dir / "en.json"

        try:
            with open(locale_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load translations from {locale_file}: {e}")
            return {}

    def translate(self, key: str, **kwargs) -> str:
        """
        Translate a key with optional formatting.

        Args:
            key: Translation key
            **kwargs: Format arguments

        Returns:
            Translated string
        """
        template = self.translations.get(key, key)

        if kwargs:
            try:
                return template.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing format argument for key '{key}': {e}")
                return template

        return template

    def __call__(self, key: str, **kwargs) -> str:
        """
        Shorthand for translate().

        Usage: t('welcome_message', name='João')
        """
        return self.translate(key, **kwargs)

    def get_language(self) -> str:
        """Get current language code."""
        return self.lang

    def set_language(self, lang: str) -> None:
        """
        Change current language.

        Args:
            lang: New language code
        """
        self.lang = lang
        self.translations = self._load_translations(lang)
        logger.info(f"Language changed to: {lang}")


def get_translator(lang: Optional[str] = None) -> Translator:
    """
    Get or create global translator instance.

    Args:
        lang: Language code. If None, use existing or auto-detect.

    Returns:
        Translator instance
    """
    global _translator

    if _translator is None or lang is not None:
        _translator = Translator(lang)

    return _translator
