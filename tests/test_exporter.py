from datetime import datetime, timedelta
from core.exporter import export_to_ics
from core.scheduler import StudyBlock


def test_export_to_ics(tmp_path):
    start = datetime.now() + timedelta(days=1)
    end = start + timedelta(minutes=30)
    b = StudyBlock("C", start, end)
    fname = tmp_path / "out.ics"
    res = export_to_ics([b], str(fname))
    assert str(fname) == res
    assert fname.exists()
    content = fname.read_text(encoding="utf-8")
    assert "BEGIN:VCALENDAR" in content or "BEGIN:VEVENT" in content
