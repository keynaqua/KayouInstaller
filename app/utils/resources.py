import sys
from pathlib import Path


def resource_path(path: str) -> Path:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).parents[2]))
    return root / path
