"""
Students Management Page
=========================
Refactored against the real crud.py / models.py in this project. Nothing
here is fake, random, or hardcoded — every value comes from a CRUD call
that talks to MySQL.

CRUD contracts relied on (see crud.py):
    get_total_students() -> int
    get_active_students() -> int
    get_inactive_students() -> int
    get_students_filtered(search="", grade_id=None, academic_year_id=None,
                           student_group=None, is_active=None) -> list[Student]
    get_student_filters() -> (list[Grade], list[str])
    get_grades() -> list[Grade]
    get_academic_years() -> list[AcademicYear]
    get_student(student_id) -> Student | None      (eager-loads grade + academic_year)
    student_name_exists(full_name, exclude_id=None) -> bool
    add_student(full_name, grade_id, student_group, phone, parent_phone,
                monthly_fee, join_date, academic_year_id, is_active=True) -> Student
    update_student(student_id, **fields) -> bool   (False if student not found)
    delete_student(student_id) -> bool             (False if student not found)
    toggle_student_status(student_id) -> bool      (flips is_active, False if not found)

crud.py changes made to support this page
------------------------------------------
1. get_student() previously used session.get() with no eager loading, so
   student.grade / student.academic_year raised DetachedInstanceError
   once the session closed. It now eager-loads both relationships.
2. get_students_filtered() gained student_group and is_active parameters
   so Group and Status filters run in SQL instead of being narrowed down
   afterward in a DataFrame.
3. Added student_name_exists() for duplicate-name validation on Add.
4. Removed duplicate definitions of get_grades(), get_academic_years(),
   and get_student() that existed twice in the file (Python was silently
   using the second definition either way; this just removes the dead
   code so there's one source of truth per function).
No other CRUD functions were touched.
"""

import streamlit as st
import pandas as pd
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import DetachedInstanceError

from sidebar import show_sidebar

from crud import (
    get_total_students,
    get_active_students,
    get_inactive_students,
    get_students_filtered,
    get_student_filters,
    add_student,
    get_grades,
    get_academic_years,
    get_student,
    update_student,
    delete_student,
    toggle_student_status,
    student_name_exists,
)

st.set_page_config(
    page_title="Students",
    page_icon="👨‍🎓",
    layout="wide"
)

show_sidebar()

st.title("👨‍🎓 Students Management")
st.divider()


# ===============================
# SESSION STATE DEFAULTS
# ===============================

for key, default in {
    "show_add_dialog": False,
    "view_student_id": None,
    "edit_student_id": None,
    "confirm_delete_id": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ===============================
# HELPERS
# ===============================

def safe_call(fn, *args, **kwargs):
    """Run a CRUD call and turn any DB error into a friendly message
    instead of crashing the app. Returns (result, error_message)."""
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


def student_to_row(s):
    return {
        "ID": s.student_id,
        "Name": s.full_name,
        "Grade": s.grade.grade_name if s.grade else "—",
        "Group": s.student_group,
        "Phone": s.phone,
        "Parent Phone": s.parent_phone,
        "Monthly Fee": float(s.monthly_fee) if s.monthly_fee is not None else 0.0,
        "Join Date": s.join_date,
        "Status": "🟢 Active" if s.is_active else "🔴 Inactive",
    }


def validate_student_form(full_name, grade, academic_year, phone, parent_phone):
    """Shared validation for Add and Edit forms. Returns an error string
    or None if the form is valid."""
    if not full_name or not full_name.strip():
        return "Student name is required."
    if len(full_name.strip()) < 2:
        return "Student name must be at least 2 characters."
    if grade is None:
        return "Please select a grade."
    if academic_year is None:
        return "Please select an academic year."
    if phone and not phone.strip().replace("+", "").replace(" ", "").isdigit():
        return "Phone number should contain digits only."
    if parent_phone and not parent_phone.strip().replace("+", "").replace(" ", "").isdigit():
        return "Parent phone number should contain digits only."
    return None


# ===============================
# FILTERS
# ===============================

grades, groups = get_student_filters()
years = get_academic_years()

c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 2, 2, 2, 1.3])

with c1:
    search = st.text_input("🔍 Search Student", placeholder="Type a name...")

with c2:
    grade_filter = st.selectbox("Grade", ["All"] + [g.grade_name for g in grades])

with c3:
    group_filter = st.selectbox("Group", ["All"] + list(groups))

with c4:
    year_filter = st.selectbox("Academic Year", ["All"] + [y.academic_year for y in years])

with c5:
    status_filter = st.selectbox("Status", ["All", "Active", "Inactive"])

with c6:
    st.write("")
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

selected_grade_id = next(
    (g.grade_id for g in grades if g.grade_name == grade_filter), None
) if grade_filter != "All" else None

selected_year_id = next(
    (y.academic_year_id for y in years if y.academic_year == year_filter), None
) if year_filter != "All" else None

selected_group = group_filter if group_filter != "All" else None

selected_is_active = {"Active": True, "Inactive": False}.get(status_filter)

st.divider()


# ===============================
# ADD BUTTON
# ===============================

left, right = st.columns([8, 2])
with right:
    if st.button("➕ Add Student", use_container_width=True, type="primary"):
        st.session_state.show_add_dialog = True


# ===============================
# ADD STUDENT DIALOG
# ===============================

@st.dialog("➕ Add Student")
def add_student_dialog():
    dialog_grades = get_grades()
    dialog_years = get_academic_years()

    with st.form("add_student_form"):
        st.markdown("**Student Information**")
        col1, col2 = st.columns(2)

        with col1:
            full_name = st.text_input("Student Name *")
            grade = st.selectbox("Grade *", dialog_grades, format_func=lambda x: x.grade_name)
            student_group = st.text_input("Group")

        with col2:
            academic_year = st.selectbox(
                "Academic Year *", dialog_years, format_func=lambda x: x.academic_year
            )
            join_date = st.date_input("Join Date")
            monthly_fee = st.number_input("Monthly Fee", min_value=0.0, step=50.0)

        st.markdown("**Contact Information**")
        col3, col4 = st.columns(2)

        with col3:
            phone = st.text_input("Phone")

        with col4:
            parent_phone = st.text_input("Parent Phone")

        st.divider()
        save = st.form_submit_button("💾 Save", use_container_width=True, type="primary")

        if save:
            error = validate_student_form(full_name, grade, academic_year, phone, parent_phone)
            if error:
                st.error(error)
                return

            exists, dup_error = safe_call(student_name_exists, full_name.strip())
            if dup_error:
                st.error(dup_error)
                return
            if exists:
                st.warning(
                    f"A student named **{full_name.strip()}** already exists. "
                    "Double-check before adding a duplicate — submit again to proceed anyway."
                )
                return

            _, error = safe_call(
                add_student,
                full_name=full_name.strip(),
                grade_id=grade.grade_id,
                student_group=student_group.strip(),
                phone=phone.strip(),
                parent_phone=parent_phone.strip(),
                monthly_fee=monthly_fee,
                join_date=join_date,
                academic_year_id=academic_year.academic_year_id,
            )

            if error:
                st.error(error)
            else:
                st.success("Student added successfully.")
                st.session_state.show_add_dialog = False
                st.rerun()


if st.session_state.show_add_dialog:
    add_student_dialog()


# ===============================
# VIEW STUDENT DIALOG
# ===============================

@st.dialog("👁 Student Details")
def view_student_dialog(student_id):
    student, error = safe_call(get_student, student_id)
    if error or student is None:
        st.error(error or "Student not found.")
        return

    st.subheader(student.full_name)
    st.caption(f"Student ID: {student.student_id}")
    st.divider()

    st.markdown("##### 🎓 Academic Information")
    a1, a2 = st.columns(2)
    a1.metric("Grade", student.grade.grade_name if student.grade else "—")
    a2.metric(
        "Academic Year",
        student.academic_year.academic_year if student.academic_year else "—"
    )
    if student.student_group:
        st.write(f"**Group:** {student.student_group}")

    st.divider()
    st.markdown("##### 📞 Contact Information")
    c1, c2 = st.columns(2)
    c1.write(f"**Phone:** {student.phone or '—'}")
    c2.write(f"**Parent Phone:** {student.parent_phone or '—'}")

    st.divider()
    st.markdown("##### 💰 Financial Information")
    f1, f2 = st.columns(2)
    fee = float(student.monthly_fee) if student.monthly_fee is not None else 0.0
    f1.metric("Monthly Fee", f"{fee:,.0f} EGP")
    f2.write(f"**Join Date:** {student.join_date.strftime('%d/%m/%Y') if student.join_date else '—'}")

    st.divider()
    st.markdown("##### 📌 Status")
    if student.is_active:
        st.success("🟢 Active")
    else:
        st.error("🔴 Inactive")

    st.divider()
    if st.button("Close", use_container_width=True):
        st.session_state.view_student_id = None
        st.rerun()


if st.session_state.view_student_id is not None:
    view_student_dialog(st.session_state.view_student_id)


# ===============================
# EDIT STUDENT DIALOG
# ===============================

@st.dialog("✏ Edit Student")
def edit_student_dialog(student_id):
    student, error = safe_call(get_student, student_id)
    if error or student is None:
        st.error(error or "Student not found.")
        return

    dialog_grades = get_grades()
    dialog_years = get_academic_years()

    grade_index = next(
        (i for i, g in enumerate(dialog_grades) if g.grade_id == student.grade_id), 0
    )
    year_index = next(
        (i for i, y in enumerate(dialog_years) if y.academic_year_id == student.academic_year_id), 0
    )

    with st.form("edit_student_form"):
        st.markdown("**Student Information**")
        col1, col2 = st.columns(2)

        with col1:
            full_name = st.text_input("Student Name *", value=student.full_name)
            grade = st.selectbox(
                "Grade *", dialog_grades, index=grade_index, format_func=lambda x: x.grade_name
            )
            student_group = st.text_input("Group", value=student.student_group or "")

        with col2:
            academic_year = st.selectbox(
                "Academic Year *", dialog_years, index=year_index, format_func=lambda x: x.academic_year
            )
            join_date = st.date_input("Join Date", value=student.join_date)
            monthly_fee = st.number_input(
                "Monthly Fee", min_value=0.0, step=50.0, value=float(student.monthly_fee or 0)
            )

        st.markdown("**Contact Information**")
        col3, col4 = st.columns(2)

        with col3:
            phone = st.text_input("Phone", value=student.phone or "")

        with col4:
            parent_phone = st.text_input("Parent Phone", value=student.parent_phone or "")

        is_active = st.checkbox("Active", value=student.is_active)

        st.divider()
        save = st.form_submit_button("💾 Update", use_container_width=True, type="primary")

        if save:
            error = validate_student_form(full_name, grade, academic_year, phone, parent_phone)
            if error:
                st.error(error)
                return

            exists, dup_error = safe_call(
                student_name_exists, full_name.strip(), exclude_id=student_id
            )
            if dup_error:
                st.error(dup_error)
                return
            if exists:
                st.warning(
                    f"Another student named **{full_name.strip()}** already exists. "
                    "Double-check before saving — submit again to proceed anyway."
                )
                return

            updated, error = safe_call(
                update_student,
                student_id,
                full_name=full_name.strip(),
                grade_id=grade.grade_id,
                student_group=student_group.strip(),
                phone=phone.strip(),
                parent_phone=parent_phone.strip(),
                monthly_fee=monthly_fee,
                join_date=join_date,
                academic_year_id=academic_year.academic_year_id,
                is_active=is_active,
            )

            if error:
                st.error(error)
            elif not updated:
                st.error("Student not found. It may have been deleted by someone else.")
            else:
                st.success("Student updated successfully.")
                st.session_state.edit_student_id = None
                st.rerun()


if st.session_state.edit_student_id is not None:
    edit_student_dialog(st.session_state.edit_student_id)


# ===============================
# DELETE CONFIRMATION DIALOG
# ===============================

@st.dialog("🗑 Confirm Delete")
def confirm_delete_dialog(student_id):
    student, error = safe_call(get_student, student_id)
    name = student.full_name if student else f"#{student_id}"

    st.warning(f"Are you sure you want to permanently delete **{name}**?")
    st.caption(
        "This removes the student record entirely. If you just want to "
        "stop counting them as enrolled, use Deactivate instead — it "
        "keeps their history and can be reversed."
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", use_container_width=True):
            st.session_state.confirm_delete_id = None
            st.rerun()
    with col2:
        if st.button("🗑 Delete", use_container_width=True, type="primary"):
            success, error = safe_call(delete_student, student_id)
            if error:
                st.error(error)
            elif success:
                st.success("Student deleted successfully.")
                st.session_state.confirm_delete_id = None
                st.rerun()
            else:
                st.error("Delete failed — student may already be gone.")


if st.session_state.confirm_delete_id is not None:
    confirm_delete_dialog(st.session_state.confirm_delete_id)


# ===============================
# LOAD DATA (fully filtered in SQL)
# ===============================

students, load_error = safe_call(
    get_students_filtered,
    search=search,
    grade_id=selected_grade_id,
    academic_year_id=selected_year_id,
    student_group=selected_group,
    is_active=selected_is_active,
)

if load_error:
    st.error(load_error)
    students = []

df = pd.DataFrame(
    [student_to_row(s) for s in students],
    columns=["ID", "Name", "Grade", "Group", "Phone", "Parent Phone",
             "Monthly Fee", "Join Date", "Status"],
)


# ===============================
# TABLE
# ===============================

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    height=500,
    column_config={
        "ID": st.column_config.NumberColumn(width="small"),
        "Name": st.column_config.TextColumn(width="large"),
        "Grade": st.column_config.TextColumn(width="medium"),
        "Group": st.column_config.TextColumn(width="medium"),
        "Phone": st.column_config.TextColumn(width="medium"),
        "Parent Phone": st.column_config.TextColumn(width="medium"),
        "Monthly Fee": st.column_config.NumberColumn(format="%.0f EGP"),
        "Join Date": st.column_config.DateColumn(format="DD/MM/YYYY"),
    }
)


# ===============================
# METRIC CARDS
# ===============================

st.divider()

total_students, total_error = safe_call(get_total_students)
active_students, active_error = safe_call(get_active_students)
inactive_students, inactive_error = safe_call(get_inactive_students)

if total_error or active_error or inactive_error:
    st.warning("Some metrics could not be loaded from the database.")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Total Students", total_students if total_students is not None else "—")

with c2:
    st.metric("Active Students", active_students if active_students is not None else "—")

with c3:
    st.metric("Inactive Students", inactive_students if inactive_students is not None else "—")

with c4:
    income = df["Monthly Fee"].sum() if not df.empty else 0
    st.metric("Monthly Income (filtered view)", f"{income:,.0f} EGP")

st.caption(
    "Total / Active / Inactive reflect the whole database. "
    "Monthly Income reflects the students currently shown in the table above."
)

st.divider()


# ===============================
# ACTIONS
# ===============================

st.subheader("Student Actions")

if df.empty:
    st.info("No students found for the current filters.")
else:
    student_id = st.selectbox(
        "Select Student",
        df["ID"],
        format_func=lambda sid: f"{sid} — {df.loc[df['ID'] == sid, 'Name'].values[0]}",
    )

    selected_status = df.loc[df["ID"] == student_id, "Status"].values[0]
    is_currently_active = selected_status == "🟢 Active"

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if st.button("👁 View", use_container_width=True):
            st.session_state.view_student_id = student_id
            st.rerun()

    with c2:
        if st.button("✏ Edit", use_container_width=True):
            st.session_state.edit_student_id = student_id
            st.rerun()

    with c3:
        toggle_label = "⏸ Deactivate" if is_currently_active else "▶ Activate"
        if st.button(toggle_label, use_container_width=True):
            success, error = safe_call(toggle_student_status, student_id)
            if error:
                st.error(error)
            elif success:
                st.success(
                    "Student deactivated." if is_currently_active else "Student activated."
                )
                st.rerun()
            else:
                st.error("Could not update status — student may no longer exist.")

    with c4:
        if st.button("🗑 Delete", use_container_width=True):
            st.session_state.confirm_delete_id = student_id
            st.rerun()
