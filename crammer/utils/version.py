from typing import Dict
import crammer


def get_version_info() -> Dict[str, str]:
    return {
        "version": crammer.__version__,
        "version_name": crammer.__version_name__,
        "build_number": crammer.__build_number__,
        "author": crammer.__author__,
        "email": crammer.__email__,
        "license": crammer.__license__,
    }


def get_version_string() -> str:
    return f'v{crammer.__version__} "{crammer.__version_name__}"'


def get_full_version_string() -> str:
    return f'v{crammer.__version__} "{crammer.__version_name__}" (build {crammer.__build_number__})'
