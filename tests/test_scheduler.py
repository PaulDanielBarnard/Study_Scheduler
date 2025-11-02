import pytest
from datetime import datetime, timedelta

from core.scheduler import SmartScheduler, StudyBlock


def test_generate_schedule_basic():
    chapters = ["Chap 1", "Chap 2", "Chap 3"]
    exam = datetime.now() + timedelta(days=10)
    sched = SmartScheduler(chapter_titles=chapters, block_minutes=30, exam_datetime=exam, random_seed=42)
    blocks = sched.generate_schedule()
    assert len(blocks) >= len(chapters)
    assert all(isinstance(b, StudyBlock) for b in blocks)
    assert all(b.end_time <= exam for b in blocks)


def test_mark_completed():
    chapters = ["A"]
    exam = datetime.now() + timedelta(days=5)
    sched = SmartScheduler(chapter_titles=chapters, block_minutes=10, exam_datetime=exam, random_seed=1)
    blocks = sched.generate_schedule()
    assert not blocks[0].completed
    sched.mark_completed("A")
    assert any(b.completed for b in sched.blocks)
