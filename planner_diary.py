import json
import os
import uuid
import threading
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import simpledialog, messagebox, ttk

# External dependencies (must be installed via pip)
# schedule: lightweight job scheduler
# plyer: cross‑platform notification library
import schedule
from plyer import notification

# ---------------------------------------------------------------------------
# Security considerations
# ---------------------------------------------------------------------------
# * All external data (user input) is validated before being written to disk.
# * JSON file is written atomically to avoid corruption.
# * No eval/exec is used.
# * Paths are confined to the application directory.
# ---------------------------------------------------------------------------

APP_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_FILE = os.path.join(APP_DIR, "events.json")


def load_events():
    """Load events from the JSON file. Returns a list of dicts."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Error] Failed to load events: {e}")
        return []


def save_events(events):
    """Save events atomically to the JSON file."""
    temp_path = DATA_FILE + ".tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, DATA_FILE)
    except Exception as e:
        print(f"[Error] Failed to save events: {e}")


def add_event(title, start_dt, repeat=None, description=""):
    """Create a new event and persist it.
    repeat: None, 'daily', 'weekly', 'monthly'
    """
    events = load_events()
    event = {
        "id": str(uuid.uuid4()),
        "title": title,
        "start": start_dt.isoformat(),
        "repeat": repeat,
        "description": description,
    }
    events.append(event)
    save_events(events)
    return event


def delete_event(event_id):
    events = load_events()
    events = [e for e in events if e["id"] != event_id]
    save_events(events)


def get_due_events(now=None):
    """Return events that should trigger a notification at *now*.
    Handles repeating logic.
    """
    if now is None:
        now = datetime.now()
    due = []
    for ev in load_events():
        start = datetime.fromisoformat(ev["start"])
        repeat = ev.get("repeat")
        # Compute the next occurrence based on repeat interval
        if repeat == "daily":
            # Align to same time each day
            next_occ = start.replace(year=now.year, month=now.month, day=now.day)
            if next_occ < now:
                next_occ += timedelta(days=1)
        elif repeat == "weekly":
            # Same weekday and time each week
            days_ahead = (start.weekday() - now.weekday()) % 7
            next_occ = now + timedelta(days=days_ahead)
            next_occ = next_occ.replace(hour=start.hour, minute=start.minute, second=start.second, microsecond=0)
            if next_occ < now:
                next_occ += timedelta(weeks=1)
        elif repeat == "monthly":
            # Same day-of-month and time
            try:
                next_occ = now.replace(day=start.day, hour=start.hour, minute=start.minute, second=start.second, microsecond=0)
            except ValueError:
                # Invalid day (e.g., Feb 30) – skip this month
                continue
            if next_occ < now:
                # move to next month safely
                month = now.month + 1 if now.month < 12 else 1
                year = now.year if now.month < 12 else now.year + 1
                try:
                    next_occ = next_occ.replace(year=year, month=month)
                except ValueError:
                    continue
        else:
            # Non‑repeating event
            next_occ = start
        # Notify if the occurrence is within the next minute
        if 0 <= (next_occ - now).total_seconds() < 60:
            due.append((ev, next_occ))
    return due


def notify(event, occ_time):
    """Show a desktop notification for *event* using plyer."""
    title = f"일정 알림: {event['title']}"
    msg = f"시간: {occ_time.strftime('%Y-%m-%d %H:%M')}"
    if event.get("description"):
        msg += f"\n{event['description']}"
    try:
        notification.notify(title=title, message=msg, timeout=10)
    except Exception as e:
        print(f"[Error] Notification failed: {e}")


def scheduler_loop():
    """Background thread that runs pending schedule jobs every second."""
    while True:
        schedule.run_pending()
        threading.Event().wait(1)


def check_and_notify():
    now = datetime.now()
    for ev, occ in get_due_events(now):
        notify(ev, occ)

# Schedule the check to run every minute
schedule.every(1).minutes.do(check_and_notify)

# Start scheduler in a daemon thread
threading.Thread(target=scheduler_loop, daemon=True).start()

# ---------------------------------------------------------------------------
# Tkinter UI
# ---------------------------------------------------------------------------
class PlannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("플래너 & 다이어리")
        self.geometry("600x400")
        self.create_widgets()
        self.refresh_list()

    def create_widgets(self):
        self.tree = ttk.Treeview(self, columns=("title", "start", "repeat"), show="headings")
        self.tree.heading("title", text="제목")
        self.tree.heading("start", text="시작 시간")
        self.tree.heading("repeat", text="반복")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10)
        tk.Button(btn_frame, text="추가", command=self.add_event_dialog).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="삭제", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="새로고침", command=self.refresh_list).pack(side=tk.LEFT, padx=5)

    def refresh_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for ev in load_events():
            start = datetime.fromisoformat(ev["start"]).strftime("%Y-%m-%d %H:%M")
            repeat = ev.get("repeat") or "없음"
            self.tree.insert("", tk.END, iid=ev["id"], values=(ev["title"], start, repeat))

    def add_event_dialog(self):
        dialog = EventDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            title, dt_str, repeat, description = dialog.result
            try:
                start_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                add_event(title, start_dt, repeat, description)
                self.refresh_list()
            except ValueError:
                messagebox.showerror("입력 오류", "날짜 형식은 YYYY-MM-DD HH:MM 이어야 합니다.")

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        for iid in sel:
            delete_event(iid)
        self.refresh_list()

class EventDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("새 일정")
        self.result = None
        self.create_widgets()
        self.grab_set()

    def create_widgets(self):
        tk.Label(self, text="제목:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.title_entry = tk.Entry(self, width=30)
        self.title_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self, text="시작 (YYYY-MM-DD HH:MM):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.start_entry = tk.Entry(self, width=30)
        self.start_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self, text="반복:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.repeat_var = tk.StringVar(value="none")
        repeat_options = ["none", "daily", "weekly", "monthly"]
        ttk.Combobox(self, textvariable=self.repeat_var, values=repeat_options, state="readonly").grid(row=2, column=1, padx=5, pady=5)

        tk.Label(self, text="설명:").grid(row=3, column=0, sticky="ne", padx=5, pady=5)
        self.desc_text = tk.Text(self, width=30, height=5)
        self.desc_text.grid(row=3, column=1, padx=5, pady=5)

        btn_frame = tk.Frame(self)
        btn_frame.grid(row=4, columnspan=2, pady=10)
        tk.Button(btn_frame, text="확인", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="취소", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def on_ok(self):
        title = self.title_entry.get().strip()
        start = self.start_entry.get().strip()
        repeat = self.repeat_var.get()
        description = self.desc_text.get("1.0", tk.END).strip()
        if not title or not start:
            messagebox.showerror("입력 오류", "제목과 시작 시간은 필수입니다.")
            return
        repeat_val = None if repeat == "none" else repeat
        self.result = (title, start, repeat_val, description)
        self.destroy()

if __name__ == "__main__":
    app = PlannerApp()
    app.mainloop()
