"""
Lessons Management Page
=========================
No fake/dummy data — every value comes from a real CRUD call against MySQL.

CRUD contracts relied on (see crud.py):
    get_total_lessons() -> int
    get_lessons_filtered(search="", grade_id=None, academic_year_id=None) -> list[Lesson]
    get_lesson(lesson_id) -> Lesson | None       (eager-loads grade + academic_year)
    get_grades() -> list[Grade]
    get_academic_years() -> list[AcademicYear]
    add_lesson(grade_id, lesson_number, lesson_title, lesson_date, academic_year_id) -> Lesson
    update_lesson(lesson_id, **fields) -> bool
    delete_lesson(lesson_id) -> bool             (cascades to Attendance + Exam rows for this lesson)
    get_lesson_attendance_stats(lesson_id) -> {"present": int, "absent": int}

All of the above already existed in crud.py except get_lessons_filtered,
get_lesson, update_lesson, delete_lesson, get_total_lessons, and
get_lesson_attendance_stats, which were added following the exact same
session/eager-loading pattern as the rest of the file.
"""

import streamlit as st
import pandas as pd
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import DetachedInstanceError

from sidebar import show_sidebar

from crud import (
    get_total_lessons,
    get_lessons_filtered,
    get_lesson,
    get_grades,
    get_academic_years,
    add_lesson,
    update_lesson,
    delete_lesson,
    get_lesson_attendance_stats,
)

st.set_page_config(page_title="Lessons", page_icon="📚", layout="wide")
show_sidebar()

st.title("📚 Lessons Management")
st.divider()


# ===============================
# SESSION STATE DEFAULTS
# ===============================

for key, default in {
    "show_add_lesson_dialog": False,
    "view_lesson_id": None,
    "edit_lesson_id": None,
    "confirm_delete_lesson_id": None,
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


def lesson_to_row(l):
    return {
        "ID": l.lesson_id,
        "Title": l.lesson_title,
        "Lesson #": l.lesson_number,
        "Grade": l.grade.grade_name if l.grade else "—",
        "Academic Year": l.academic_year.academic_year if l.academic_year else "—",
        "Date": l.lesson_date,
    }


def validate_lesson_form(lesson_title, lesson_number, grade, academic_year, lesson_date):
    if not lesson_title or not lesson_title.strip():
        return "Lesson title is required."
    if grade is None:
        return "Please select a grade."
    if academic_year is None:
        return "Please select an academic year."
    if lesson_number is None or lesson_number < 1:
        return "Lesson number must be 1 or greater."
    if lesson_date is None:
        return "Please choose a lesson date."
    return None


# ===============================
# FILTERS
# ===============================

grades = get_grades()
years = get_academic_years()

c1, c2, c3, c4 = st.columns([3, 2, 2, 1.3])

with c1:
    search = st.text_input("🔍 Search by Title", placeholder="Type a lesson title...")

with c2:
    grade_filter = st.selectbox("Grade", ["All"] + [g.grade_name for g in grades])

with c3:
    year_filter = st.selectbox("Academic Year", ["All"] + [y.academic_year for y in years])

with c4:
    st.write("")
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

selected_grade_id = next(
    (g.grade_id for g in grades if g.grade_name == grade_filter), None
) if grade_filter != "All" else None

selected_year_id = next(
    (y.academic_year_id for y in years if y.academic_year == year_filter), None
) if year_filter != "All" else None

st.divider()


# ===============================
# ADD BUTTON
# ===============================

left, right = st.columns([8, 2])
with right:
    if st.button("➕ Add Lesson", use_container_width=True, type="primary"):
        st.session_state.show_add_lesson_dialog = True


# ===============================
# ADD LESSON DIALOG
# ===============================

@st.dialog("➕ Add Lesson")
def add_lesson_dialog():
    dialog_grades = get_grades()
    dialog_years = get_academic_years()

    with st.form("add_lesson_form"):
        lesson_title = st.text_input("Lesson Title *")

        col1, col2 = st.columns(2)
        with col1:
            grade = st.selectbox("Grade *", dialog_grades, format_func=lambda x: x.grade_name)
            lesson_number = st.number_input("Lesson Number *", min_value=1, step=1)

        with col2:
            academic_year = st.selectbox(
                "Academic Year *", dialog_years, format_func=lambda x: x.academic_year
            )
            lesson_date = st.date_input("Lesson Date *")

        st.divider()
        save = st.form_submit_button("💾 Save", use_container_width=True, type="primary")

        if save:
            error = validate_lesson_form(lesson_title, lesson_number, grade, academic_year, lesson_date)
            if error:
                st.error(error)
                return

            _, error = safe_call(
                add_lesson,
                grade_id=grade.grade_id,
                lesson_number=int(lesson_number),
                lesson_title=lesson_title.strip(),
                lesson_date=lesson_date,
                academic_year_id=academic_year.academic_year_id,
            )

            if error:
                st.error(error)
            else:
                st.success("Lesson added successfully.")
                st.session_state.show_add_lesson_dialog = False
                st.rerun()


if st.session_state.show_add_lesson_dialog:
    add_lesson_dialog()


# ===============================
# VIEW LESSON DIALOG
# ===============================

@st.dialog("📖 Lesson Details")
def view_lesson_dialog(lesson_id):
    lesson, error = safe_call(get_lesson, lesson_id)
    if error or lesson is None:
        st.error(error or "Lesson not found.")
        return

    st.subheader(lesson.lesson_title)
    st.caption(f"Lesson ID: {lesson.lesson_id}")
    st.divider()

    a1, a2, a3 = st.columns(3)
    a1.metric("Lesson #", lesson.lesson_number)
    a2.metric("Grade", lesson.grade.grade_name if lesson.grade else "—")
    a3.metric("Academic Year", lesson.academic_year.academic_year if lesson.academic_year else "—")

    st.write(f"**Date:** {lesson.lesson_date.strftime('%d/%m/%Y') if lesson.lesson_date else '—'}")

    st.divider()
    st.markdown("##### ✅ Attendance Summary")
    stats, stats_error = safe_call(get_lesson_attendance_stats, lesson_id)
    if stats_error:
        st.warning(stats_error)
    else:
        s1, s2 = st.columns(2)
        s1.metric("Present", stats["present"])
        s2.metric("Absent", stats["absent"])

    st.divider()
    if st.button("Close", use_container_width=True):
        st.session_state.view_lesson_id = None
        st.rerun()


if st.session_state.view_lesson_id is not None:
    view_lesson_dialog(st.session_state.view_lesson_id)


# ===============================
# EDIT LESSON DIALOG
# ===============================

@st.dialog("✏ Edit Lesson")
def edit_lesson_dialog(lesson_id):
    lesson, error = safe_call(get_lesson, lesson_id)
    if error or lesson is None:
        st.error(error or "Lesson not found.")
        return

    dialog_grades = get_grades()
    dialog_years = get_academic_years()

    grade_index = next(
        (i for i, g in enumerate(dialog_grades) if g.grade_id == lesson.grade_id), 0
    )
    year_index = next(
        (i for i, y in enumerate(dialog_years) if y.academic_year_id == lesson.academic_year_id), 0
    )

    with st.form("edit_lesson_form"):
        lesson_title = st.text_input("Lesson Title *", value=lesson.lesson_title)

        col1, col2 = st.columns(2)
        with col1:
            grade = st.selectbox(
                "Grade *", dialog_grades, index=grade_index, format_func=lambda x: x.grade_name
            )
            lesson_number = st.number_input(
                "Lesson Number *", min_value=1, step=1, value=int(lesson.lesson_number)
            )

        with col2:
            academic_year = st.selectbox(
                "Academic Year *", dialog_years, index=year_index, format_func=lambda x: x.academic_year
            )
            lesson_date = st.date_input("Lesson Date *", value=lesson.lesson_date)

        st.divider()
        save = st.form_submit_button("💾 Update", use_container_width=True, type="primary")

        if save:
            error = validate_lesson_form(lesson_title, lesson_number, grade, academic_year, lesson_date)
            if error:
                st.error(error)
                return

            updated, error = safe_call(
                update_lesson,
                lesson_id,
                lesson_title=lesson_title.strip(),
                grade_id=grade.grade_id,
                lesson_number=int(lesson_number),
                lesson_date=lesson_date,
                academic_year_id=academic_year.academic_year_id,
            )

            if error:
                st.error(error)
            elif not updated:
                st.error("Lesson not found. It may have been deleted by someone else.")
            else:
                st.success("Lesson updated successfully.")
                st.session_state.edit_lesson_id = None
                st.rerun()


if st.session_state.edit_lesson_id is not None:
    edit_lesson_dialog(st.session_state.edit_lesson_id)


# ===============================
# DELETE CONFIRMATION DIALOG
# ===============================

@st.dialog("🗑 Confirm Delete")
def confirm_delete_lesson_dialog(lesson_id):
    lesson, error = safe_call(get_lesson, lesson_id)
    title = lesson.lesson_title if lesson else f"#{lesson_id}"

    st.warning(f"Are you sure you want to delete **{title}**?")
    st.caption(
        "This also permanently deletes every attendance record and "
        "exam score linked to this lesson."
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", use_container_width=True):
            st.session_state.confirm_delete_lesson_id = None
            st.rerun()
    with col2:
        if st.button("🗑 Delete", use_container_width=True, type="primary"):
            success, error = safe_call(delete_lesson, lesson_id)
            if error:
                st.error(error)
            elif success:
                st.success("Lesson deleted successfully.")
                st.session_state.confirm_delete_lesson_id = None
                st.rerun()
            else:
                st.error("Delete failed — lesson may already be gone.")


if st.session_state.confirm_delete_lesson_id is not None:
    confirm_delete_lesson_dialog(st.session_state.confirm_delete_lesson_id)


# ===============================
# LOAD DATA
# ===============================

lessons, load_error = safe_call(
    get_lessons_filtered,
    search=search,
    grade_id=selected_grade_id,
    academic_year_id=selected_year_id,
)

if load_error:
    st.error(load_error)
    lessons = []

df = pd.DataFrame(
    [lesson_to_row(l) for l in lessons],
    columns=["ID", "Title", "Lesson #", "Grade", "Academic Year", "Date"],
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
        "Title": st.column_config.TextColumn(width="large"),
        "Lesson #": st.column_config.NumberColumn(width="small"),
        "Grade": st.column_config.TextColumn(width="medium"),
        "Academic Year": st.column_config.TextColumn(width="medium"),
        "Date": st.column_config.DateColumn(format="DD/MM/YYYY"),
    }
)


# ===============================
# METRIC CARDS
# ===============================

st.divider()

total_lessons, total_error = safe_call(get_total_lessons)
if total_error:
    st.warning(total_error)

c1, c2 = st.columns(2)
with c1:
    st.metric("Total Lessons", total_lessons if total_lessons is not None else "—")
with c2:
    st.metric("Lessons in Current View", len(df))

st.divider()


# ===============================
# ACTIONS
# ===============================

st.subheader("Lesson Actions")

if df.empty:
    st.info("No lessons found for the current filters.")
else:
    lesson_id = st.selectbox(
        "Select Lesson",
        df["ID"],
        format_func=lambda lid: f"{lid} — {df.loc[df['ID'] == lid, 'Title'].values[0]}",
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("👁 View", use_container_width=True):
            st.session_state.view_lesson_id = lesson_id
            st.rerun()

    with c2:
        if st.button("✏ Edit", use_container_width=True):
            st.session_state.edit_lesson_id = lesson_id
            st.rerun()

    with c3:
        if st.button("🗑 Delete", use_container_width=True):
            st.session_state.confirm_delete_lesson_id = lesson_id
            st.rerun()