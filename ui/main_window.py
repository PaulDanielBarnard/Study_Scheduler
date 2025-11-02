# study_planner/ui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime, time
from pathlib import Path

from core.scheduler import SmartScheduler, StudyBlock
from core.exporter import export_to_ics
from core.storage import save_schedule, load_schedule

class StudyPlannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Study Planner")
        self.geometry("900x620")
        self.minsize(850, 600)

        self.blocks = []
        self._build_ui()
        self._load_if_exists()

    def _build_ui(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        # Left: Inputs
        left = ttk.Frame(frm)
        left.pack(side="left", fill="y", padx=(0,12))

        ttk.Label(left, text="Exam Date:").pack(anchor="w")
        self.exam_date = DateEntry(left, date_pattern="yyyy-mm-dd")
        self.exam_date.pack(fill="x", pady=3)

        ttk.Label(left, text="Exam Time (HH:MM, 24h):").pack(anchor="w")
        self.exam_time = ttk.Entry(left)
        self.exam_time.insert(0, "09:00")
        self.exam_time.pack(fill="x", pady=3)

        ttk.Label(left, text="Study block length (minutes):").pack(anchor="w")
        self.block_len = ttk.Entry(left)
        self.block_len.insert(0, "45")
        self.block_len.pack(fill="x", pady=3)

        ttk.Label(left, text="Daily base limit (blocks/day):").pack(anchor="w")
        self.daily_limit = ttk.Entry(left)
        self.daily_limit.insert(0, "4")
        self.daily_limit.pack(fill="x", pady=3)

        ttk.Label(left, text="Break length (minutes):").pack(anchor="w")
        self.break_len = ttk.Entry(left)
        self.break_len.insert(0, "10")
        self.break_len.pack(fill="x", pady=3)

        ttk.Label(left, text="Ramp factor (0.0 - 1.0):").pack(anchor="w")
        self.ramp_factor = ttk.Entry(left)
        self.ramp_factor.insert(0, "0.5")
        self.ramp_factor.pack(fill="x", pady=3)

        ttk.Label(left, text="Day start hour (0-23):").pack(anchor="w")
        self.day_start_hour = ttk.Entry(left)
        self.day_start_hour.insert(0, "9")
        self.day_start_hour.pack(fill="x", pady=3)

        ttk.Label(left, text="Chapters (one per line):").pack(anchor="w", pady=(10,0))
        self.chapters_text = tk.Text(left, width=30, height=12)
        self.chapters_text.pack(fill="both", pady=3)

        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill="x", pady=(8,0))
        ttk.Button(btn_frame, text="Generate Schedule", command=self.on_generate).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Save Schedule", command=self.on_save).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Load Schedule", command=self.on_load).pack(side="left", padx=2)

        # Right: Table and actions
        right = ttk.Frame(frm)
        right.pack(side="left", fill="both", expand=True)

        toolbar = ttk.Frame(right)
        toolbar.pack(fill="x", pady=(0,6))
        ttk.Button(toolbar, text="Export to .ics", command=self.on_export).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Mark Selected Completed", command=self.on_mark_completed).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Clear Completed Flags", command=self.on_clear_completed).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Remove Selected", command=self.on_remove_selected).pack(side="left", padx=4)

        # Treeview for schedule
        cols = ("chapter", "start", "end", "mode", "done")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
        self.tree.column("chapter", width=300)
        self.tree.column("start", width=150)
        self.tree.column("end", width=90)
        self.tree.column("mode", width=90)
        self.tree.column("done", width=60, anchor="center")
        self.tree.pack(fill="both", expand=True)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w")
        status.pack(fill="x", side="bottom")

    def _load_if_exists(self):
        p = Path("study_schedule.json")
        if p.exists():
            try:
                self.blocks = load_schedule()
                self._refresh_tree()
                self.status_var.set("Loaded existing schedule from study_schedule.json")
            except Exception:
                self.status_var.set("No valid saved schedule to load.")

    def on_generate(self):
        try:
            chapters = [ln.strip() for ln in self.chapters_text.get("1.0", "end").splitlines() if ln.strip()]
            if not chapters:
                messagebox.show.error = messagebox.showerror
                messagebox.showerror("Error", "Please enter one or more chapter titles.")
                return

            exam_date = self.exam_date.get_date()
            try:
                hour, minute = map(int, self.exam_time.get().split(":"))
            except Exception:
                messagebox.showerror("Error", "Invalid exam time. Use HH:MM 24-hour format.")
                return
            exam_dt = datetime.combine(exam_date, time(hour, minute))

            block_len = int(self.block_len.get())
            daily_limit = int(self.daily_limit.get())
            break_len = int(self.break_len.get())
            ramp = float(self.ramp_factor.get())
            day_start = int(self.day_start_hour.get())

            scheduler = SmartScheduler(
                chapter_titles=chapters,
                block_minutes=block_len,
                exam_datetime=exam_dt,
                daily_limit=daily_limit,
                break_minutes=break_len,
                ramp_factor=ramp,
                day_start_hour=day_start
            )

            self.blocks = scheduler.generate_schedule()
            save_schedule(self.blocks)  # persist default
            self._refresh_tree()
            self.status_var.set(f"Generated schedule with {len(self.blocks)} blocks.")
            messagebox.showinfo("Schedule Generated", f"Generated {len(self.blocks)} blocks. Saved to study_schedule.json")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _refresh_tree(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        for b in self.blocks:
            start_s = b.start_time.strftime("%Y-%m-%d %H:%M")
            end_s = b.end_time.strftime("%H:%M")
            done = "✓" if getattr(b, "completed", False) else ""
            self.tree.insert("", "end", values=(b.chapter, start_s, end_s, b.mode, done))

    def on_export(self):
        if not self.blocks:
            messagebox.showwarning("Empty", "Generate a schedule first.")
            return
        fname = filedialog.asksaveasfilename(defaultextension=".ics",
                                             filetypes=[("iCalendar file", "*.ics")],
                                             initialfile="study_schedule.ics")
        if not fname:
            return
        try:
            export_to_ics(self.blocks, fname)
            self.status_var.set(f"Exported schedule to {fname}")
            messagebox.showinfo("Exported", f"Schedule exported to {fname}")
        except Exception as e:
            messagebox.showerror("Export error", str(e))

    def on_save(self):
        try:
            fname = filedialog.asksaveasfilename(defaultextension=".json",
                                                 filetypes=[("JSON file", "*.json")],
                                                 initialfile="study_schedule.json")
            if not fname:
                return
            save_schedule(self.blocks, fname)
            self.status_var.set(f"Saved schedule to {fname}")
            messagebox.showinfo("Saved", f"Saved schedule to {fname}")
        except Exception as e:
            messagebox.showerror("Save error", str(e))

    def on_load(self):
        try:
            fname = filedialog.askopenfilename(filetypes=[("JSON file", "*.json")], initialdir=".")
            if not fname:
                return
            self.blocks = load_schedule(fname)
            self._refresh_tree()
            self.status_var.set(f"Loaded schedule from {fname}")
            messagebox.showinfo("Loaded", f"Loaded schedule from {fname}")
        except Exception as e:
            messagebox.showerror("Load error", str(e))

    def on_mark_completed(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a block in the table first.")
            return
        vals = self.tree.item(sel[0], "values")
        chapter = vals[0]
        # Mark the first matching block for that chapter as completed (prefer earliest pending)
        for b in self.blocks:
            if b.chapter == chapter and not b.completed:
                b.completed = True
                break
        save_schedule(self.blocks)
        self._refresh_tree()
        self.status_var.set(f"Marked '{chapter}' completed (first pending block).")

    def on_clear_completed(self):
        for b in self.blocks:
            b.completed = False
        save_schedule(self.blocks)
        self._refresh_tree()
        self.status_var.set("Cleared completed flags.")

    def on_remove_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a block in the table first.")
            return
        vals = self.tree.item(sel[0], "values")
        chapter = vals[0]
        # remove the selected exact datetime block
        start = vals[1]
        # find block matching chapter and start string
        removed = False
        for b in list(self.blocks):
            if b.chapter == chapter and b.start_time.strftime("%Y-%m-%d %H:%M") == start:
                self.blocks.remove(b)
                removed = True
                break
        if removed:
            save_schedule(self.blocks)
            self._refresh_tree()
            self.status_var.set(f"Removed selected block '{chapter}' at {start}.")
        else:
            messagebox.showwarning("Not found", "Could not find selected block to remove.")
