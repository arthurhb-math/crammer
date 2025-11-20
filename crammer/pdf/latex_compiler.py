import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from crammer.utils.logger import get_logger

logger = get_logger(__name__)


def _find_pdflatex_path() -> str:
    """Encontra o pdflatex, priorizando uma versão portátil agrupada."""

    if getattr(sys, "frozen", False):
        base_path = Path(sys.executable).parent

        portable_paths = [
            base_path / "miktex/texmfs/install/miktex/bin/x64/pdflatex.exe",
            base_path / "miktex/texmfs/install/miktex/bin/pdflatex.exe",
        ]

        for path in portable_paths:
            if path.exists():
                logger.info(f"Usando pdflatex portátil encontrado em: {path}")
                return str(path)

    logger.info("Usando 'pdflatex' do PATH do sistema.")
    return "pdflatex"


class LaTeXCompiler:
    """Compiles LaTeX documents to PDF."""

    def __init__(self, compiler: str = "pdflatex", passes: int = 2):
        """
        Initialize compiler.

        Args:
            compiler: LaTeX compiler command (default: pdflatex)
            passes: Number of compilation passes (default: 2 for references)
        """
        if compiler == "pdflatex":
            self.compiler = _find_pdflatex_path()
        else:
            self.compiler = compiler
        self.passes = passes

    def compile(
        self, tex_content: str, output_path: Path, working_dir: Optional[Path] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Compile LaTeX content to PDF.

        Args:
            tex_content: LaTeX source code
            output_path: Path for output PDF (without extension)
            working_dir: Working directory for compilation (for asset resolution)

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        output_path = Path(output_path)
        tex_file = output_path.with_suffix(".tex")
        pdf_file = output_path.with_suffix(".pdf")
        log_file = output_path.with_suffix(".log")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(tex_file, "w", encoding="utf-8") as f:
                f.write(tex_content)
            logger.debug(f"Wrote LaTeX file: {tex_file}")
        except Exception as e:
            error_msg = f"Failed to write LaTeX file: {e}"
            logger.error(error_msg)
            return False, error_msg

        env = os.environ.copy()

        if working_dir:
            texinputs_path = str(working_dir.absolute()) + os.pathsep
            env["TEXINPUTS"] = texinputs_path + env.get("TEXINPUTS", "")

        try:
            for pass_num in range(1, self.passes + 1):
                logger.debug(f"Compilation pass {pass_num}/{self.passes}")

                process = subprocess.run(
                    [
                        self.compiler,
                        "-interaction=nonstopmode",
                        f"-output-directory={output_path.parent}",
                        str(tex_file),
                    ],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=60,
                )

            if pdf_file.exists():
                logger.info(f"Successfully compiled PDF: {pdf_file}")
                self._cleanup_auxiliary_files(output_path)
                return True, None
            else:
                error_msg = f"PDF not created. Check log: {log_file}"
                logger.error(error_msg)

                self._save_compilation_log(output_path, process)

                return False, error_msg

        except subprocess.TimeoutExpired:
            error_msg = "LaTeX compilation timed out"
            logger.error(error_msg)
            return False, error_msg

        except FileNotFoundError:
            error_msg = f"LaTeX compiler '{self.compiler}' not found"
            logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Compilation error: {e}"
            logger.error(error_msg)
            return False, error_msg

    def _cleanup_auxiliary_files(self, output_path: Path) -> None:
        """
        Remove auxiliary LaTeX files.

        Args:
            output_path: Base path (without extension)
        """
        aux_extensions = [".aux", ".log", ".out", ".fdb_latexmk", ".fls", ".synctex.gz"]

        for ext in aux_extensions:
            aux_file = output_path.with_suffix(ext)
            if aux_file.exists():
                try:
                    aux_file.unlink()
                    logger.debug(f"Removed auxiliary file: {aux_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove {aux_file}: {e}")

    def _save_compilation_log(
        self, output_path: Path, process: subprocess.CompletedProcess
    ) -> None:
        """
        Save compilation log for debugging.

        Args:
            output_path: Base path for log file
            process: Completed subprocess
        """
        log_file = output_path.parent / f"{output_path.stem}_compilation.log"

        try:
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"--- LaTeX Compilation Log ---\n")
                f.write(f"Compiler: {self.compiler}\n")
                f.write(f"Passes: {self.passes}\n\n")
                f.write("--- stdout ---\n")
                f.write(process.stdout)
                f.write("\n--- stderr ---\n")
                f.write(process.stderr)

            logger.info(f"Saved compilation log: {log_file}")
        except Exception as e:
            logger.error(f"Failed to save compilation log: {e}")

    def check_available(self) -> bool:
        """
        Check if LaTeX compiler is available.

        Returns:
            True if compiler is available, False otherwise
        """
        try:
            result = subprocess.run(
                [self.compiler, "--version"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
