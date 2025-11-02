# study_planner/core/exporter.py
from ics import Calendar, Event

def export_to_ics(blocks, filename="study_schedule.ics"):
    """
    Export list of StudyBlock objects to an .ics calendar file.
    """
    cal = Calendar()
    for b in blocks:
        e = Event()
        e.name = f"{b.mode}: {b.chapter}"
        e.begin = b.start_time
        e.end = b.end_time
        status = "Completed" if getattr(b, "completed", False) else "Pending"
        e.description = f"{b.mode} session for {b.chapter}\nStatus: {status}"
        cal.events.add(e)

    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(cal)
    return filename
