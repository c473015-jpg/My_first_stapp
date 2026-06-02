# my_st.py
"""
Streamlit app for household expense tracking.
Features:
- Add expense with category, amount, date, and description.
- View expenses in a table.
- Filter by date range and category.
- Data persisted to a local JSON file with input sanitization.
"""

import json
import os
from datetime import datetime, date
import streamlit as st

# ==================== Secure Coding Practices ====================
# - All user inputs are sanitized to remove control characters.
# - Data is written atomically to avoid corruption.
# - Streamlit escapes HTML by default, but we still strip non‑printable chars.
# - No external network calls or exec of user data.
# =================================================================

DATA_FILE = "expenses.json"

def load_expenses() -> list:
    """Load expenses from JSON file safely."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except (json.JSONDecodeError, OSError) as e:
        st.error(f"Failed to read expense data: {e}")
    return []

def save_expenses(expenses: list) -> None:
    """Write expenses to JSON file using an atomic temporary file."""
    tmp_path = DATA_FILE + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(expenses, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, DATA_FILE)
    except OSError as e:
        st.error(f"Failed to save expenses: {e}")

def sanitize_text(value: str) -> str:
    """Remove non‑printable characters to mitigate injection risks."""
    return "".join(ch for ch in value if ch.isprintable())

# ---------- Streamlit UI ----------
st.set_page_config(page_title="Household Expense Tracker", layout="centered")
st.title("🏠 Household Expense Tracker")

# Load current expenses
expenses = load_expenses()

# ---- Sidebar: Add expense ----
st.sidebar.header("Add New Expense")
with st.sidebar.form(key="add_expense_form"):
    category = st.selectbox("Category", ["Food", "Transport", "Utilities", "Entertainment", "Other"])
    amount_str = st.text_input("Amount (USD)", "0")
    expense_date = st.date_input("Date", date.today())
    description = st.text_area("Description")
    submit = st.form_submit_button("Add Expense")
    if submit:
        # Validate amount
        try:
            amount = float(amount_str)
            if amount <= 0:
                st.warning("Amount must be positive.")
                st.stop()
        except ValueError:
            st.warning("Please provide a valid numeric amount.")
            st.stop()
        new_entry = {
            "id": len(expenses) + 1,
            "category": sanitize_text(category),
            "amount": round(amount, 2),
            "date": expense_date.isoformat(),
            "description": sanitize_text(description),
        }
        expenses.append(new_entry)
        save_expenses(expenses)
        st.success("Expense added!")
        st.experimental_rerun()

# ---- Main view: Filter and list ----
st.subheader("Expenses")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start date", value=date.today().replace(day=1))
with col2:
    end_date = st.date_input("End date", value=date.today())
selected_categories = st.multiselect(
    "Category filter",
    options=["Food", "Transport", "Utilities", "Entertainment", "Other"],
    default=[],
)

# Apply filters
filtered = []
for exp in expenses:
    exp_dt = datetime.fromisoformat(exp["date"]).date()
    if exp_dt < start_date or exp_dt > end_date:
        continue
    if selected_categories and exp["category"] not in selected_categories:
        continue
    filtered.append(exp)

if filtered:
    # Use Streamlit's data editor for nice table view
    st.dataframe(filtered, use_container_width=True)
    total_spent = sum(item["amount"] for item in filtered)
    st.metric("Total", f"${total_spent:,.2f}")
else:
    st.info("No expenses match the selected filters.")
