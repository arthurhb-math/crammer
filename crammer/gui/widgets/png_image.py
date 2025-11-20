import tkinter as tk
from pathlib import Path
from typing import Optional, Tuple, TYPE_CHECKING
from crammer.utils.logger import get_logger

try:
    from PIL import Image, ImageTk

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

if TYPE_CHECKING:
    from tkinter import PhotoImage

logger = get_logger(__name__)


def load_png(path: str, size: Optional[Tuple[int, int]] = None) -> "Optional[PhotoImage]":
    """
    Safely loads a PNG file as a PhotoImage using tkinter.

    !! IMPORTANT (Tkinter Garbage Collection) !!
    The caller MUST keep a persistent reference to the returned
    PhotoImage object.

    Example:
        my_label.config(image=photo)
        my_label.image = photo
    """

    image_path = Path(path)

    if not image_path.exists():
        logger.warning(f"Failed to load image: File not found at {image_path}")
        return None

    try:
        if size and PIL_AVAILABLE:
            with Image.open(image_path) as img:
                img.thumbnail(size, Image.Resampling.LANCZOS)
                photo_image = ImageTk.PhotoImage(img)
                return photo_image

        elif size:
            logger.warning(
                f"Image resizing requested but Pillow is not installed. Loading original size."
            )

        photo_image = tk.PhotoImage(file=str(image_path))
        return photo_image

    except tk.TclError as e:
        logger.error(f"Failed to load image {image_path}: {e} - File may be corrupt or not a PNG.")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading image {image_path}: {e}")
        return None
