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
from streamlit_calendar import calendar

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
if "section" not in st.session_state:
    st.session_state.section = "일정 보기"
# Handle pending navigation change
if "go_to_section" in st.session_state:
    st.session_state.section = st.session_state.go_to_section
    del st.session_state.go_to_section
section = st.sidebar.selectbox("메뉴", ["일정 보기", "일정 추가"], key="section")

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
                # 반드시 이벤트를 저장하고 UI를 전환합니다
                start_dt = datetime.combine(date, time)
                repeat_val = None if repeat == "없음" else repeat
                new_event = add_event(title, start_dt, repeat_val, description)
                st.success(f"이벤트가 저장되었습니다. ID: {new_event['id']}")
                # Set navigation flag for next run
                st.session_state.go_to_section = "일정 보기"
                st.toast("일정이 추가되었습니다.", icon="✅")
                st.rerun()

elif section == "일정 보기":
    st.header("📅 월간 달력")
    # Load events and convert to FullCalendar format
    events = load_events()
    calendar_events = [
        {"id": ev["id"], "title": ev["title"], "start": ev["start"]} for ev in events
    ]

    # Calendar options
    calendar_options = {
        "initialView": "dayGridMonth",
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
                        "right": "dayGridMonth,timeGridWeek",
      "StartLine": 215
        },
        "selectable": True,
        "eventClick": True,
    }

    # Render calendar component
    cal_state = calendar(events=calendar_events, options=calendar_options)

    # Determine selected date
    selected_date = None
    if cal_state and "date" in cal_state and cal_state["date"]:
        selected_date = datetime.fromisoformat(cal_state["date"]).date()
    else:
        selected_date = datetime.now().date()

    # Filter events for the selected date
    filtered_events = [
        ev for ev in events if datetime.fromisoformat(ev["start"]).date() == selected_date
    ]

    if not filtered_events:
        st.info(f"선택한 날짜({selected_date})에 일정이 없습니다.")
    else:
        st.subheader(f"{selected_date} 일정")
        table_data = []
        for ev in filtered_events:
            start = datetime.fromisoformat(ev["start"]).strftime("%Y-%m-%d %H:%M")
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

        # Deletion UI for filtered events
        ids_to_delete = st.multiselect(
            "삭제할 일정을 선택하세요",
            options=[ev["id"] for ev in filtered_events],
            format_func=lambda x: next(
                e["title"] for e in filtered_events if e["id"] == x
            ),
        )
        if st.button("선택된 일정 삭제"):
            for eid in ids_to_delete:
                delete_event(eid)
            st.toast("선택된 일정이 삭제되었습니다.", icon="✅")
            st.rerun()


# Note: The background scheduler thread will continue to run and send OS
# notifications via plyer.
