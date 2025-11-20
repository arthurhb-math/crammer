import time
from pathlib import Path
from typing import Iterator, List, Dict, Any
from dataclasses import dataclass

from crammer.core.models import Template, Student, Question
from crammer.core.question_selector import select_questions_for_template
from crammer.pdf import LaTeXRenderer, LaTeXCompiler, AssetManager
from crammer.utils.logger import get_logger
from crammer.utils.paths import get_resources_path

logger = get_logger(__name__)


@dataclass
class GenerationProgress:
    """Progress update during assessment generation."""

    stage: str
    message: str
    student_name: str = None
    current: int = 0
    total: int = 0
    success: bool = True


class AssessmentGenerator:
    """Orchestrates the complete assessment generation process."""

    def __init__(
        self,
        template: Template,
        students: List[Student],
        all_questions: List[Question],
        output_dir: Path,
        template_path: Path,
        latex_compiler: str = "pdflatex",
    ):
        """
        Initialize generator.

        Args:
            template: Template configuration
            students: List of students to generate assessments for
            all_questions: Complete question bank
            output_dir: Base output directory
            template_path: Path to LaTeX template file
            latex_compiler: LaTeX compiler command
        """
        self.template = template
        self.students = students
        self.all_questions = all_questions
        self.output_dir = Path(output_dir)
        self.template_path = Path(template_path)
        self.latex_compiler = latex_compiler

        self.run_id = str(int(time.time()))
        self.run_dir = self.output_dir / self.run_id
        self.tex_dir = self.run_dir / "tex"
        self.pdf_dir = self.run_dir / "pdf"
        self.log_dir = self.run_dir / "log"
        self.assets_dir = self.tex_dir / "assets"

        for directory in [self.tex_dir, self.pdf_dir, self.log_dir, self.assets_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        self.renderer = LaTeXRenderer(self.template_path)
        self.compiler = LaTeXCompiler(compiler=self.latex_compiler, passes=2)
        self.asset_manager = AssetManager(self.assets_dir)

        self.overall_success = True

    def generate(self) -> Iterator[GenerationProgress]:
        """
        Generate assessments for all students.

        Yields progress updates as generation proceeds.

        Yields:
            GenerationProgress objects with status updates
        """
        yield GenerationProgress("loading", f"Output will be saved in: {self.run_dir}")

        if self.template.logo_path:
            relative_logo_path = self.asset_manager.copy_logo(
                get_resources_path() / "assets" / "logo.pdf"
            )
            if relative_logo_path:
                self.template.course_info["logo_path"] = relative_logo_path

        yield GenerationProgress(
            "loading", f"Loaded {len(self.all_questions)} questions from database"
        )

        yield GenerationProgress("loading", f"Found {len(self.students)} students")

        for i, student in enumerate(self.students, 1):
            yield GenerationProgress(
                "selecting",
                f"Processing: {student.student_name}",
                student_name=student.student_name,
                current=i,
                total=len(self.students),
            )

            try:
                question_blocks = select_questions_for_template(
                    self.all_questions, self.template.selection_blocks
                )

                for block in question_blocks:
                    self.asset_manager.copy_question_images(block["questions"])

            except Exception as e:
                error_msg = f"Failed to select questions for {student.student_name}: {e}"
                logger.error(error_msg)
                yield GenerationProgress(
                    "error",
                    error_msg,
                    student_name=student.student_name,
                    current=i,
                    total=len(self.students),
                    success=False,
                )
                self.overall_success = False
                continue

            blocks_summary = []
            for block_def, block_res in zip(self.template.selection_blocks, question_blocks):
                titulo = block_def.title.replace(":", "").replace(";", "").strip()
                
                metodo = block_def.method.replace("random_", "rnd_")
                
                if block_def.method == "manual":
                    qtd = len(block_res["questions"])
                else:
                    qtd = block_def.quantity
                
                blocks_summary.append(f"{titulo}:{metodo}:{qtd}")
            
            blocks_str = ";".join(blocks_summary)
            
            qr_data_string = f"S:{student.student_id}|R:{self.run_id}|B:{blocks_str}"

            yield GenerationProgress(
                "rendering",
                f"Rendering LaTeX for {student.student_name}",
                student_name=student.student_name,
                current=i,
                total=len(self.students),
            )

            try:
                tex_content = self.renderer.render(
                    student=student,
                    question_blocks=question_blocks,
                    template_config=self.template,
                    qr_data=qr_data_string,
                )

                filename_base = (
                    f"{self.template.filename_prefix}_"
                    f"{student.sanitized_name}_{student.student_id}"
                )
                tex_path = self.tex_dir / f"{filename_base}.tex"

                with open(tex_path, "w", encoding="utf-8") as f:
                    f.write(tex_content)

                yield GenerationProgress(
                    "rendering",
                    f"  -> .tex file saved to '{tex_path}'",
                    student_name=student.student_name,
                    current=i,
                    total=len(self.students),
                )

            except Exception as e:
                error_msg = f"Failed to render LaTeX for {student.student_name}: {e}"
                logger.error(error_msg)
                yield GenerationProgress(
                    "error",
                    error_msg,
                    student_name=student.student_name,
                    current=i,
                    total=len(self.students),
                    success=False,
                )
                self.overall_success = False
                continue

            yield GenerationProgress(
                "compiling",
                f"Compiling PDF for {student.student_name}",
                student_name=student.student_name,
                current=i,
                total=len(self.students),
            )

            try:
                output_path = self.pdf_dir / filename_base
                success, error = self.compiler.compile(
                    tex_content=tex_content, output_path=output_path, working_dir=self.tex_dir
                )

                if success:
                    yield GenerationProgress(
                        "compiling",
                        f"  -> PDF generated successfully using {self.latex_compiler}!",
                        student_name=student.student_name,
                        current=i,
                        total=len(self.students),
                    )
                else:
                    error_msg = f"  -> ERROR: PDF not created. {error}"
                    yield GenerationProgress(
                        "error",
                        error_msg,
                        student_name=student.student_name,
                        current=i,
                        total=len(self.students),
                        success=False,
                    )
                    self.overall_success = False

            except Exception as e:
                error_msg = f"Failed to compile PDF for {student.student_name}: {e}"
                logger.error(error_msg)
                yield GenerationProgress(
                    "error",
                    error_msg,
                    student_name=student.student_name,
                    current=i,
                    total=len(self.students),
                    success=False,
                )
                self.overall_success = False

        if self.overall_success:
            yield GenerationProgress(
                "complete",
                "\n--- PROCESS FINISHED ---\nAll PDFs were generated successfully!",
                success=True,
            )
        else:
            yield GenerationProgress(
                "complete",
                "\n--- PROCESS FINISHED ---\nCompleted with one or more errors.",
                success=False,
            )

    def get_pdf_directory(self) -> Path:
        """Get the directory containing generated PDFs."""
        return self.pdf_dir
