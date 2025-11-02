# study_planner/core/storage.py
import json
from pathlib import Path
from .scheduler import StudyBlock

DEFAULT_SAVE = Path("study_schedule.json")

def save_schedule(blocks, filename=None):
    filename = filename or DEFAULT_SAVE
    data = [b.to_dict() for b in blocks]
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return filename

def load_schedule(filename=None):
    filename = filename or DEFAULT_SAVE
    p = Path(filename)
    if not p.exists():
        return []
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [StudyBlock.from_dict(d) for d in data]
