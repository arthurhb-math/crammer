import sys
import os
from pathlib import Path
from typing import Optional


def get_base_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    else:
        return Path(__file__).parent.parent.parent


def get_resources_path() -> Path:
    return get_base_path() / "resources"


def get_data_path() -> Path:
    if getattr(sys, "frozen", False):
        data_path = Path.home() / ".crammer"
    else:
        data_path = get_base_path() / "data"

    data_path.mkdir(parents=True, exist_ok=True)

    return data_path


def ensure_data_structure() -> None:
    data_path = get_data_path()

    subdirs = ["questions", "classes", "templates", "output"]

    for subdir in subdirs:
        subdir_path = data_path / subdir
        subdir_path.mkdir(parents=True, exist_ok=True)


def get_output_path(run_id: Optional[str] = None) -> Path:
    output_base = get_data_path() / "output"

    if run_id:
        return output_base / run_id

    return output_base


def resource_path(relative_path: str) -> str:
    base = get_base_path()
    return str(base / relative_path)
