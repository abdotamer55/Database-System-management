"""
Payments Management Page
=========================
No fake/dummy data — every value comes from a real CRUD call against MySQL.

CRUD contracts relied on (see crud.py):
    get_students_filtered(is_active=True) -> list[Student]
    get_payments_filtered(search="", student_id=None, status=None, month=None) -> list[Payment]
    get_payment(payment_id) -> Payment | None        (eager-loads student)
    get_payment_months() -> list[str]
    get_payment_stats() -> {"paid": float, "unpaid": float, "pending_count": int}
    add_payment(student_id, payment_for_month, amount, payment_date, status) -> Payment
    update_payment(payment_id, **fields) -> bool
    delete_payment(payment_id) -> bool

add_payment() already existed in crud.py; get_payments_filtered,
get_payment, get_payment_months, get_payment_stats, update_payment and
delete_payment were added following the existing session/eager-loading
pattern.
"""

import streamlit as st
import pandas as pd
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import DetachedInstanceError

from sidebar import show_sidebar

from crud import (
    get_students_filtered,
    get_payments_filtered,
    get_payment,
    get_payment_months,
    get_payment_stats,
    add_payment,
    update_payment,
    delete_payment,
)

st.set_page_config(page_title="Payments", page_icon="💰", layout="wide")
show_sidebar()

st.title("💰 Payments Management")
st.divider()


# ===============================
# SESSION STATE DEFAULTS
# ===============================

for key, default in {
    "show_add_payment_dialog": False,
    "view_payment_id": None,
    "edit_payment_id": None,
    "confirm_delete_payment_id": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ===============================
# HELPERS
# ===============================

def safe_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs), None
    except IntegrityError:
        return None, "This operation conflicts with existing data (duplicate or invalid reference)."
    except OperationalError:
        return None, "Could not reach the database. Please check your connection and try again."
    except DetachedInstanceError:
        return None, "That record went stale before it could be read. Please refresh."
    except Exception as e:
        return None, f"Unexpected error: {e}"


def payment_to_row(p):
    return {
        "ID": p.payment_id,
        "Student": p.student.full_name if p.student else "—",
        "Month": p.payment_for_month,
        "Amount": float(p.amount) if p.amount is not None else 0.0,
        "Date": p.payment_date,
        "Status": "🟢 Paid" if p.status == "Paid" else "🔴 Unpaid",
    }


def validate_payment_form(student, payment_for_month, amount, payment_date):
    if student is None:
        return "Please select a student."
    if not payment_for_month or not payment_for_month.strip():
        return "Please specify which month this payment is for."
    if amount is None or amount <= 0:
        return "Amount must be greater than 0."
    if payment_date is None:
        return "Please choose a payment date."
    return None


# ===============================
# FILTERS
# ===============================

active_students, students_error = safe_call(get_students_filtered, is_active=True)
if students_error:
    st.error(students_error)
    active_students = []

months, months_error = safe_call(get_payment_months)
if months_error:
    months = []

c1, c2, c3, c4 = st.columns([3, 2, 2, 1.3])

with c1:
    search = st.text_input("🔍 Search Student", placeholder="Type a name...")

with c2:
    status_filter = st.selectbox("Status", ["All", "Paid", "Unpaid"])

with c3:
    month_filter = st.selectbox("Month", ["All"] + sorted(m for m in months if m))

with c4:
    st.write("")
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

st.divider()


# ===============================
# ADD BUTTON
# ===============================

left, right = st.columns([8, 2])
with right:
    if st.button("➕ Add Payment", use_container_width=True, type="primary"):
        st.session_state.show_add_payment_dialog = True


# ===============================
# ADD PAYMENT DIALOG
# ===============================

@st.dialog("➕ Add Payment")
def add_payment_dialog():
    dialog_students = get_students_filtered(is_active=True)

    if not dialog_students:
        st.info("There are no active students to record a payment for.")
        return

    with st.form("add_payment_form"):
        student = st.selectbox("Student *", dialog_students, format_func=lambda s: s.full_name)
        payment_for_month = st.text_input("Payment For Month *", placeholder="e.g. January 2026")

        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input("Amount *", min_value=0.0, step=50.0)
        with col2:
            payment_date = st.date_input("Payment Date *")

        status = st.selectbox("Status *", ["Paid", "Unpaid"])

        st.divider()
        save = st.form_submit_button("💾 Save", use_container_width=True, type="primary")

        if save:
            error = validate_payment_form(student, payment_for_month, amount, payment_date)
            if error:
                st.error(error)
                return

            _, error = safe_call(
                add_payment,
                student_id=student.student_id,
                payment_for_month=payment_for_month.strip(),
                amount=amount,
                payment_date=payment_date,
                status=status,
            )

            if error:
                st.error(error)
            else:
                st.success("Payment recorded successfully.")
                st.session_state.show_add_payment_dialog = False
                st.rerun()


if st.session_state.show_add_payment_dialog:
    add_payment_dialog()


# ===============================
# VIEW PAYMENT DIALOG
# ===============================

@st.dialog("📖 Payment Details")
def view_payment_dialog(payment_id):
    payment, error = safe_call(get_payment, payment_id)
    if error or payment is None:
        st.error(error or "Payment not found.")
        return

    st.subheader(payment.student.full_name if payment.student else "—")
    st.caption(f"Payment ID: {payment.payment_id}")
    st.divider()

    a1, a2 = st.columns(2)
    a1.metric("Amount", f"{float(payment.amount or 0):,.0f} EGP")
    a2.metric("Month", payment.payment_for_month or "—")

    st.write(f"**Payment Date:** {payment.payment_date.strftime('%d/%m/%Y') if payment.payment_date else '—'}")

    st.divider()
    if payment.status == "Paid":
        st.success("🟢 Paid")
    else:
        st.error("🔴 Unpaid")

    st.divider()
    if st.button("Close", use_container_width=True):
        st.session_state.view_payment_id = None
        st.rerun()


if st.session_state.view_payment_id is not None:
    view_payment_dialog(st.session_state.view_payment_id)


# ===============================
# EDIT PAYMENT DIALOG
# ===============================

@st.dialog("✏ Edit Payment")
def edit_payment_dialog(payment_id):
    payment, error = safe_call(get_payment, payment_id)
    if error or payment is None:
        st.error(error or "Payment not found.")
        return

    with st.form("edit_payment_form"):
        st.write(f"**Student:** {payment.student.full_name if payment.student else '—'}")

        payment_for_month = st.text_input("Payment For Month *", value=payment.payment_for_month or "")

        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input(
                "Amount *", min_value=0.0, step=50.0, value=float(payment.amount or 0)
            )
        with col2:
            payment_date = st.date_input("Payment Date *", value=payment.payment_date)

        status = st.selectbox("Status *", ["Paid", "Unpaid"], index=0 if payment.status == "Paid" else 1)

        st.divider()
        save = st.form_submit_button("💾 Update", use_container_width=True, type="primary")

        if save:
            if not payment_for_month or not payment_for_month.strip():
                st.error("Please specify which month this payment is for.")
                return
            if amount <= 0:
                st.error("Amount must be greater than 0.")
                return

            updated, error = safe_call(
                update_payment,
                payment_id,
                payment_for_month=payment_for_month.strip(),
                amount=amount,
                payment_date=payment_date,
                status=status,
            )

            if error:
                st.error(error)
            elif not updated:
                st.error("Payment not found. It may have been deleted by someone else.")
            else:
                st.success("Payment updated successfully.")
                st.session_state.edit_payment_id = None
                st.rerun()


if st.session_state.edit_payment_id is not None:
    edit_payment_dialog(st.session_state.edit_payment_id)


# ===============================
# DELETE CONFIRMATION DIALOG
# ===============================

@st.dialog("🗑 Confirm Delete")
def confirm_delete_payment_dialog(payment_id):
    payment, error = safe_call(get_payment, payment_id)
    label = (
        f"{payment.student.full_name} — {payment.payment_for_month}"
        if payment and payment.student else f"#{payment_id}"
    )

    st.warning(f"Are you sure you want to delete the payment record for **{label}**?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", use_container_width=True):
            st.session_state.confirm_delete_payment_id = None
            st.rerun()
    with col2:
        if st.button("🗑 Delete", use_container_width=True, type="primary"):
            success, error = safe_call(delete_payment, payment_id)
            if error:
                st.error(error)
            elif success:
                st.success("Payment deleted successfully.")
                st.session_state.confirm_delete_payment_id = None
                st.rerun()
            else:
                st.error("Delete failed — record may already be gone.")


if st.session_state.confirm_delete_payment_id is not None:
    confirm_delete_payment_dialog(st.session_state.confirm_delete_payment_id)


# ===============================
# LOAD DATA
# ===============================

selected_status = status_filter if status_filter != "All" else None
selected_month = month_filter if month_filter != "All" else None

payments, load_error = safe_call(
    get_payments_filtered,
    search=search,
    status=selected_status,
    month=selected_month,
)

if load_error:
    st.error(load_error)
    payments = []

df = pd.DataFrame(
    [payment_to_row(p) for p in payments],
    columns=["ID", "Student", "Month", "Amount", "Date", "Status"],
)


# ===============================
# TABLE
# ===============================

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    height=450,
    column_config={
        "ID": st.column_config.NumberColumn(width="small"),
        "Student": st.column_config.TextColumn(width="large"),
        "Month": st.column_config.TextColumn(width="medium"),
        "Amount": st.column_config.NumberColumn(format="%.0f EGP"),
        "Date": st.column_config.DateColumn(format="DD/MM/YYYY"),
    }
)


# ===============================
# METRIC CARDS
# ===============================

st.divider()

stats, stats_error = safe_call(get_payment_stats)
if stats_error:
    st.warning(stats_error)
    stats = {"paid": 0, "unpaid": 0, "pending_count": 0}

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Paid", f"{stats['paid']:,.0f} EGP")
with c2:
    st.metric("Total Unpaid", f"{stats['unpaid']:,.0f} EGP")
with c3:
    st.metric("Pending Payments", stats["pending_count"])
with c4:
    st.metric("Records in Current View", len(df))

st.caption(
    "Total Paid / Unpaid / Pending reflect the whole database. "
    "Records in Current View reflects the table above."
)

st.divider()


# ===============================
# ACTIONS
# ===============================

st.subheader("Payment Actions")

if df.empty:
    st.info("No payment records found for the current filters.")
else:
    payment_id = st.selectbox(
        "Select Payment",
        df["ID"],
        format_func=lambda pid: f"{pid} — {df.loc[df['ID'] == pid, 'Student'].values[0]} ({df.loc[df['ID'] == pid, 'Month'].values[0]})",
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("👁 View", use_container_width=True):
            st.session_state.view_payment_id = payment_id
            st.rerun()

    with c2:
        if st.button("✏ Edit", use_container_width=True):
            st.session_state.edit_payment_id = payment_id
            st.rerun()

    with c3:
        if st.button("🗑 Delete", use_container_width=True):
            st.session_state.confirm_delete_payment_id = payment_id
            st.rerun()