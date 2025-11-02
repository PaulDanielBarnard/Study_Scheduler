# study_planner/core/scheduler.py
import math
import random
from datetime import datetime, timedelta, time

class StudyBlock:
    def __init__(self, chapter, start_time, end_time, mode="Study"):
        self.chapter = chapter
        self.start_time = start_time
        self.end_time = end_time
        self.mode = mode  # "Study" or "Revision"
        self.completed = False

    def to_dict(self):
        return {
            "chapter": self.chapter,
            "start": self.start_time.isoformat(),
            "end": self.end_time.isoformat(),
            "mode": self.mode,
            "completed": self.completed,
        }

    @staticmethod
    def from_dict(d):
        sb = StudyBlock(
            d["chapter"],
            datetime.fromisoformat(d["start"]),
            datetime.fromisoformat(d["end"]),
            d.get("mode", "Study")
        )
        sb.completed = d.get("completed", False)
        return sb


class SmartScheduler:
    """
    Scheduler that:
      - Uses exam_datetime (goal date) and works backward from today forward to exam.
      - Ensures every chapter gets at least one study block before exam.
      - Ramps up session density nearer exam using ramp_factor (0.0 - 1.0).
      - Automatically estimates difficulty/length heuristics from titles.
      - After each chapter has been scheduled once, remaining slots are revisions.
    """

    def __init__(self,
                 chapter_titles,
                 block_minutes,
                 exam_datetime,
                 daily_limit=4,
                 break_minutes=10,
                 ramp_factor=0.5,
                 day_start_hour=9,
                 random_seed=None):
        if exam_datetime <= datetime.now():
            raise ValueError("Exam datetime must be in the future.")

        if random_seed is not None:
            random.seed(random_seed)

        self.chapter_titles = list(chapter_titles)
        if not self.chapter_titles:
            raise ValueError("At least one chapter required.")

        self.block_minutes = int(block_minutes)
        self.exam_datetime = exam_datetime
        self.daily_limit = max(1, int(daily_limit))
        self.break_minutes = max(0, int(break_minutes))
        self.ramp_factor = float(ramp_factor)
        self.day_start_hour = int(day_start_hour)

        # meta: (title, difficulty 1-5, length_score 1-5)
        self.chapters_meta = [
            (t, self._estimate_difficulty(t), self._estimate_length(t))
            for t in self.chapter_titles
        ]

        self.blocks = []

    @staticmethod
    def _estimate_difficulty(title):
        # Heuristic: longer titles and more words -> slightly higher difficulty
        words = len(title.split())
        chars = len(title)
        base = 1 + min(4, chars // 15 + words // 6)
        tweak = random.choice([0, 0, 1, -1])
        return max(1, min(5, base + tweak))

    @staticmethod
    def _estimate_length(title):
        # Heuristic: number of words -> length score
        words = len(title.split())
        base = 1 + min(4, words // 4)
        tweak = random.choice([0, 0, 1, -1])
        return max(1, min(5, base + tweak))

    def _compute_daily_slots(self, total_days, base_daily_limit):
        """
        Return a list (len total_days) with number of blocks each day.
        Ramp increases nearer exam. We model ramp as increasing multiplier with day index.
        """
        slots = []
        for day_index in range(total_days):
            # day_index 0 is today, day_index total_days-1 is last day before exam
            progress = (day_index + 1) / max(1, total_days)  # 0..1
            ramp_multiplier = 1 + self.ramp_factor * progress
            day_slots = max(1, int(math.ceil(base_daily_limit * ramp_multiplier)))
            slots.append(day_slots)
        return slots

    def _make_time_slots(self, slots_per_day):
        """
        Convert slots_per_day -> list of datetime start times for candidate blocks.
        Only returns slots that start/end before exam and are not in the past.
        """
        candidate_times = []
        now = datetime.now().replace(second=0, microsecond=0)
        today = now.date()
        for offset, slots in enumerate(slots_per_day):
            current_day = today + timedelta(days=offset)
            # Start scheduling at day_start_hour for every day
            start_dt = datetime.combine(current_day, time(self.day_start_hour, 0))
            t = start_dt
            for _ in range(slots):
                end_t = t + timedelta(minutes=self.block_minutes)
                # Stop if block would end at/after exam
                if end_t >= self.exam_datetime:
                    break
                # Skip slots in the past (today only)
                if t >= now and end_t <= self.exam_datetime:
                    candidate_times.append(t)
                t = end_t + timedelta(minutes=self.break_minutes)
        return candidate_times

    def generate_schedule(self):
        """
        Main routine:
          - Compute number of days available.
          - Find slots_per_day such that total candidate slots >= number of chapters.
            If not enough, increase base daily_limit iteratively.
          - Assign each chapter to one slot (Study). After each chapter assigned once,
            remaining slots become Revision cycling through chapters.
          - Return list[StudyBlock] sorted by start time, all ending before exam.
        """
        now = datetime.now().replace(second=0, microsecond=0)
        total_days = (self.exam_datetime.date() - now.date()).days
        if total_days < 1:
            raise ValueError("Not enough days until the exam (must be at least tomorrow).")

        base_limit = max(1, self.daily_limit)
        max_attempts = 30
        for attempt in range(max_attempts):
            slots_per_day = self._compute_daily_slots(total_days, base_limit)
            candidate_times = self._make_time_slots(slots_per_day)
            if len(candidate_times) >= len(self.chapter_titles):
                break
            base_limit += 1  # increase capacity and retry
        else:
            # If still insufficient, attempt a fallback: allow scheduling earlier in day by reducing day_start_hour
            raise RuntimeError("Unable to fit all chapters before exam with given constraints.")

        # Assign chapters to times
        blocks = []
        # ensure deterministic order: schedule harder/longer first for study (optional)
        # We'll sort chapters by (difficulty+length) desc so tougher chapters appear earlier in schedule
        sorted_chapters = sorted(
            self.chapters_meta,
            key=lambda tup: (tup[1] + tup[2]),
            reverse=True
        )
        chapter_queue = [t[0] for t in sorted_chapters]

        # Fill first len(chapters) slots with unique chapters (Study)
        # Remaining slots become revision cycles
        total_slots = len(candidate_times)
        for idx, slot_start in enumerate(candidate_times):
            if idx < len(chapter_queue):
                chapter = chapter_queue[idx]
                mode = "Study"
            else:
                # revision cycles through original order (keep grouping useful)
                chapter = chapter_queue[(idx - len(chapter_queue)) % len(chapter_queue)]
                mode = "Revision"
            block = StudyBlock(chapter, slot_start, slot_start + timedelta(minutes=self.block_minutes), mode)
            blocks.append(block)

        # store and return blocks sorted by time (they already are)
        self.blocks = blocks
        return blocks

    def mark_completed(self, chapter_title):
        for b in self.blocks:
            if b.chapter == chapter_title:
                b.completed = True
