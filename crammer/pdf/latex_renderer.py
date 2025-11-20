import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from crammer.core.models import Student, Question, Template
from crammer.utils.logger import get_logger
from crammer.i18n.translator import get_translator

logger = get_logger(__name__)


class LaTeXRenderer:
    """Renders assessments to LaTeX using Jinja2 templates."""
    
    def __init__(self, template_path: Path):
        """
        Initialize renderer with template file.
        
        Args:
            template_path: Path to LaTeX template file
        """
        self.template_path = Path(template_path)
        
        template_dir = self.template_path.parent
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            block_start_string='\\block{',
            block_end_string='}',
            variable_start_string='\\var{',
            variable_end_string='}',
            comment_start_string='\\#{',
            comment_end_string='}',
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        try:
            self.template = self.env.get_template(self.template_path.name)
            logger.info(f"Loaded LaTeX template: {self.template_path.name}")
        except Exception as e:
            logger.error(f"Failed to load LaTeX template {self.template_path}: {e}")
            raise
    
    def render(
        self,
        student: Student,
        question_blocks: List[Dict[str, Any]],
        template_config: Template,
        generation_date: str = None,
        qr_data: str = None,
    ) -> str:
        """
        Render assessment for a student.
        
        Args:
            student: Student receiving the assessment
            question_blocks: List of question blocks with selected questions
            template_config: Template configuration
            generation_date: Optional generation date string
        
        Returns:
            Rendered LaTeX document as string
        """
        t = get_translator()
        lang = t.get_language()

        babel_lang = "brazilian" if lang == "pt_br" else "english"
        
        labels = {
            "course": t("pdf_course"),
            "professor": t("pdf_professor"),
            "student": t("pdf_student"),
            "id": t("pdf_id"),
            "date": t("pdf_date"),
            "question": t("pdf_question"),
            "page_of": t("pdf_page_of")
        }

        if generation_date is None:
            if lang == "pt_br":
                generation_date = datetime.now().strftime('%d de %B de %Y')
            else:
                generation_date = datetime.now().strftime('%B %d, %Y')
        
        context = {
            'document_settings': {
                'document_title': template_config.document_title,
                'filename_prefix': template_config.filename_prefix,
            },
            'course_info': template_config.course_info,
            'student': {
                'student_name': student.student_name,
                'student_id': student.student_id,
            },
            'question_blocks': question_blocks,
            'generation_date': generation_date,
            "qr_data": qr_data,
            "babel_lang": babel_lang,
            "labels": labels,
        }
        
        if template_config.logo_path:
            context['course_info']['logo_path'] = template_config.logo_path
        
        try:
            rendered = self.template.render(context)
            logger.debug(f"Rendered LaTeX for student {student.student_name}")
            return rendered
        except Exception as e:
            logger.error(f"Failed to render LaTeX for {student.student_name}: {e}")
            raise