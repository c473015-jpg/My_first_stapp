# Refactored Planner & Diary application using Streamlit
# Security: input validation, atomic JSON writes,
# no eval/exec, limited file paths

import json
import os
import uuid
import threading
from datetime import datetime, timedelta
import schedule
from plyer import notification
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
APP_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_FILE = os.path.join(APP_DIR, "events.json")

# ---------------------------------------------------------------------------
# Data handling
# ---------------------------------------------------------------------------


def load_events():
    """Load events from the JSON file. Returns a list of dicts."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"[Error] Failed to load events: {e}")
        return []


def save_events(events):
    """Save events atomically to the JSON file."""
    temp_path = DATA_FILE + ".tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, DATA_FILE)
    except Exception as e:
        st.error(f"[Error] Failed to save events: {e}")


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


# ---------------------------------------------------------------------------
# Scheduling & notifications
# ---------------------------------------------------------------------------


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
        # Compute next occurrence based on repeat interval
        if repeat == "daily":
            next_occ = start.replace(
                year=now.year, month=now.month, day=now.day
            )
            if next_occ < now:
                next_occ += timedelta(days=1)
        elif repeat == "weekly":
            days_ahead = (start.weekday() - now.weekday()) % 7
            next_occ = now + timedelta(days=days_ahead)
            next_occ = next_occ.replace(
                hour=start.hour,
                minute=start.minute,
                second=start.second,
                microsecond=0,
            )
            if next_occ < now:
                next_occ += timedelta(weeks=1)
        elif repeat == "monthly":
            try:
                next_occ = now.replace(
                    day=start.day,
                    hour=start.hour,
                    minute=start.minute,
                    second=start.second,
                    microsecond=0,
                )
            except ValueError:
                continue
            if next_occ < now:
                month = now.month + 1 if now.month < 12 else 1
                year = now.year if now.month < 12 else now.year + 1
                try:
                    next_occ = next_occ.replace(year=year, month=month)
                except ValueError:
                    continue
        else:
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
        st.error(f"[Error] Notification failed: {e}")


def check_and_notify():
    now = datetime.now()
    for ev, occ in get_due_events(now):
        notify(ev, occ)


# Schedule the check to run every minute
schedule.every(1).minutes.do(check_and_notify)


def scheduler_loop():
    """Background thread that runs pending schedule jobs every second."""
    while True:
        schedule.run_pending()
        threading.Event().wait(1)


# Ensure the scheduler thread is started only once per session
if "scheduler_started" not in st.session_state:
    threading.Thread(target=scheduler_loop, daemon=True).start()
    st.session_state["scheduler_started"] = True

# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------
st.set_page_config(page_title="플래너 & 다이어리", layout="wide")
st.title("🗓️ 플래너 & 다이어리")

# Sidebar navigation
section = st.sidebar.selectbox("메뉴", ["일정 보기", "일정 추가"])

if section == "일정 추가":
    st.header("새 일정 추가")
    with st.form(key="add_event_form"):
        title = st.text_input("제목")
        date = st.date_input("날짜")
        time = st.time_input("시간")
        repeat = st.selectbox("반복", ["없음", "daily", "weekly", "monthly"])
        description = st.text_area("설명")
        submitted = st.form_submit_button("추가")
        if submitted:
            if not title:
                st.error("제목은 필수입니다.")
            else:
                st.toast("일정이 추가되었습니다.", icon="✅")
                st.rerun()

elif section == "일정 보기":
    st.header("일정 목록")
    events = load_events()
    if not events:
        st.info("등록된 일정이 없습니다.")
    else:
        # Prepare table data
        table_data = []
        for ev in events:
            start = datetime.fromisoformat(ev["start"]).strftime(
                "%Y-%m-%d %H:%M"
            )
            repeat = ev.get("repeat") or "없음"
            table_data.append(
                {
                    "ID": ev["id"],
                    "제목": ev["title"],
                    "시작": start,
                    "반복": repeat,
                    "설명": ev.get("description", ""),
                }
            )
        st.dataframe(table_data, hide_index=True)
        # Deletion UI
        ids_to_delete = st.multiselect(
            "삭제할 일정을 선택하세요",
            options=[ev["id"] for ev in events],
            format_func=lambda x: next(
                e["title"] for e in events if e["id"] == x
            ),
        )
            st.toast("선택된 일정이 삭제되었습니다.", icon="✅")
            st.rerun()

# Note: The background scheduler thread will continue to run and send OS
# notifications via plyer.
