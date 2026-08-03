"""
Exams Management Page
=========================
No fake/dummy data — every value comes from a real CRUD call against MySQL.

CRUD contracts relied on (see crud.py):
    get_grades() -> list[Grade]
    get_academic_years() -> list[AcademicYear]
    get_lessons_filtered(grade_id=None, academic_year_id=None) -> list[Lesson]
    get_students_filtered(grade_id=None, is_active=True) -> list[Student]
    get_exams_filtered(search="", grade_id=None, academic_year_id=None, lesson_id=None) -> list[Exam]
    get_exam(exam_id) -> Exam | None                (eager-loads student + lesson + grade)
    add_exam(student_id, lesson_id, exam_name, score, total_score, exam_date) -> Exam
    update_exam(exam_id, **fields) -> bool
    delete_exam(exam_id) -> bool

add_exam() already existed in crud.py; get_exams_filtered, get_exam,
update_exam and delete_exam were added following the existing
session/eager-loading pattern.
"""

import streamlit as st
import pandas as pd
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import DetachedInstanceError

from sidebar import show_sidebar

from crud import (
    get_grades,
    get_academic_years,
    get_lessons_filtered,
    get_students_filtered,
    get_exams_filtered,
    get_exam,
    add_exam,
    update_exam,
    delete_exam,
)

st.set_page_config(page_title="Exams", page_icon="📝", layout="wide")
show_sidebar()

st.title("📝 Exams Management")
st.divider()


# ===============================
# SESSION STATE DEFAULTS
# ===============================

for key, default in {
    "show_add_exam_dialog": False,
    "view_exam_id": None,
    "edit_exam_id": None,
    "confirm_delete_exam_id": None,
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


def exam_to_row(e):
    score = float(e.score) if e.score is not None else 0.0
    total = float(e.total_score) if e.total_score is not None else 0.0
    pct = (score / total * 100) if total else 0.0
    return {
        "ID": e.exam_id,
        "Student": e.student.full_name if e.student else "—",
        "Grade": e.lesson.grade.grade_name if e.lesson and e.lesson.grade else "—",
        "Lesson": e.lesson.lesson_title if e.lesson else "—",
        "Exam": e.exam_name,
        "Score": score,
        "Out of": total,
        "Percentage": round(pct, 1),
        "Date": e.exam_date,
    }


def validate_exam_form(student, lesson, exam_name, score, total_score, exam_date):
    if student is None:
        return "Please select a student."
    if lesson is None:
        return "Please select a lesson."
    if not exam_name or not exam_name.strip():
        return "Exam name is required."
    if total_score is None or total_score <= 0:
        return "Total score must be greater than 0."
    if score is None or score < 0:
        return "Score cannot be negative."
    if score > total_score:
        return "Score cannot be greater than the total score."
    if exam_date is None:
        return "Please choose an exam date."
    return None


# ===============================
# FILTERS
# ===============================

grades = get_grades()
years = get_academic_years()

c1, c2, c3, c4 = st.columns([3, 2, 2, 1.3])

with c1:
    search = st.text_input("🔍 Search by Student", placeholder="Type a student name...")

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
    if st.button("➕ Add Exam Score", use_container_width=True, type="primary"):
        st.session_state.show_add_exam_dialog = True


# ===============================
# ADD EXAM DIALOG
# ===============================

@st.dialog("➕ Add Exam Score")
def add_exam_dialog():
    dialog_grades = get_grades()

    grade_choice = st.selectbox(
        "Grade *", dialog_grades, format_func=lambda g: g.grade_name, key="add_exam_grade"
    )

    dialog_lessons = []
    dialog_students = []
    if grade_choice:
        dialog_lessons, _ = safe_call(get_lessons_filtered, grade_id=grade_choice.grade_id)
        dialog_students, _ = safe_call(
            get_students_filtered, grade_id=grade_choice.grade_id, is_active=True
        )

    if not dialog_lessons or not dialog_students:
        st.info("This grade needs at least one lesson and one active student before an exam score can be added.")
        return

    with st.form("add_exam_form"):
        student = st.selectbox("Student *", dialog_students, format_func=lambda s: s.full_name)
        lesson = st.selectbox(
            "Lesson *", dialog_lessons,
            format_func=lambda l: f"#{l.lesson_number} — {l.lesson_title}"
        )
        exam_name = st.text_input("Exam Name *", placeholder="e.g. Midterm, Quiz 1")

        col1, col2 = st.columns(2)
        with col1:
            score = st.number_input("Score *", min_value=0.0, step=1.0)
        with col2:
            total_score = st.number_input("Out of *", min_value=0.0, step=1.0, value=100.0)

        exam_date = st.date_input("Exam Date *")

        st.divider()
        save = st.form_submit_button("💾 Save", use_container_width=True, type="primary")

        if save:
            error = validate_exam_form(student, lesson, exam_name, score, total_score, exam_date)
            if error:
                st.error(error)
                return

            _, error = safe_call(
                add_exam,
                student_id=student.student_id,
                lesson_id=lesson.lesson_id,
                exam_name=exam_name.strip(),
                score=score,
                total_score=total_score,
                exam_date=exam_date,
            )

            if error:
                st.error(error)
            else:
                st.success("Exam score added successfully.")
                st.session_state.show_add_exam_dialog = False
                st.rerun()


if st.session_state.show_add_exam_dialog:
    add_exam_dialog()


# ===============================
# VIEW EXAM DIALOG
# ===============================

@st.dialog("📖 Exam Details")
def view_exam_dialog(exam_id):
    exam, error = safe_call(get_exam, exam_id)
    if error or exam is None:
        st.error(error or "Exam not found.")
        return

    st.subheader(exam.exam_name)
    st.caption(f"Exam ID: {exam.exam_id}")
    st.divider()

    st.write(f"**Student:** {exam.student.full_name if exam.student else '—'}")
    st.write(f"**Grade:** {exam.lesson.grade.grade_name if exam.lesson and exam.lesson.grade else '—'}")
    st.write(f"**Lesson:** {exam.lesson.lesson_title if exam.lesson else '—'}")
    st.write(f"**Date:** {exam.exam_date.strftime('%d/%m/%Y') if exam.exam_date else '—'}")

    st.divider()
    score = float(exam.score) if exam.score is not None else 0.0
    total = float(exam.total_score) if exam.total_score is not None else 0.0
    pct = (score / total * 100) if total else 0.0

    s1, s2, s3 = st.columns(3)
    s1.metric("Score", f"{score:g}")
    s2.metric("Out of", f"{total:g}")
    s3.metric("Percentage", f"{pct:.1f}%")

    st.divider()
    if st.button("Close", use_container_width=True):
        st.session_state.view_exam_id = None
        st.rerun()


if st.session_state.view_exam_id is not None:
    view_exam_dialog(st.session_state.view_exam_id)


# ===============================
# EDIT EXAM DIALOG
# ===============================

@st.dialog("✏ Edit Exam Score")
def edit_exam_dialog(exam_id):
    exam, error = safe_call(get_exam, exam_id)
    if error or exam is None:
        st.error(error or "Exam not found.")
        return

    with st.form("edit_exam_form"):
        st.write(f"**Student:** {exam.student.full_name if exam.student else '—'}")
        st.write(f"**Lesson:** {exam.lesson.lesson_title if exam.lesson else '—'}")

        exam_name = st.text_input("Exam Name *", value=exam.exam_name)

        col1, col2 = st.columns(2)
        with col1:
            score = st.number_input(
                "Score *", min_value=0.0, step=1.0, value=float(exam.score or 0)
            )
        with col2:
            total_score = st.number_input(
                "Out of *", min_value=0.0, step=1.0, value=float(exam.total_score or 100)
            )

        exam_date = st.date_input("Exam Date *", value=exam.exam_date)

        st.divider()
        save = st.form_submit_button("💾 Update", use_container_width=True, type="primary")

        if save:
            if not exam_name or not exam_name.strip():
                st.error("Exam name is required.")
                return
            if total_score <= 0:
                st.error("Total score must be greater than 0.")
                return
            if score > total_score:
                st.error("Score cannot be greater than the total score.")
                return

            updated, error = safe_call(
                update_exam,
                exam_id,
                exam_name=exam_name.strip(),
                score=score,
                total_score=total_score,
                exam_date=exam_date,
            )

            if error:
                st.error(error)
            elif not updated:
                st.error("Exam not found. It may have been deleted by someone else.")
            else:
                st.success("Exam score updated successfully.")
                st.session_state.edit_exam_id = None
                st.rerun()


if st.session_state.edit_exam_id is not None:
    edit_exam_dialog(st.session_state.edit_exam_id)


# ===============================
# DELETE CONFIRMATION DIALOG
# ===============================

@st.dialog("🗑 Confirm Delete")
def confirm_delete_exam_dialog(exam_id):
    exam, error = safe_call(get_exam, exam_id)
    label = f"{exam.exam_name} — {exam.student.full_name}" if exam and exam.student else f"#{exam_id}"

    st.warning(f"Are you sure you want to delete **{label}**?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", use_container_width=True):
            st.session_state.confirm_delete_exam_id = None
            st.rerun()
    with col2:
        if st.button("🗑 Delete", use_container_width=True, type="primary"):
            success, error = safe_call(delete_exam, exam_id)
            if error:
                st.error(error)
            elif success:
                st.success("Exam score deleted successfully.")
                st.session_state.confirm_delete_exam_id = None
                st.rerun()
            else:
                st.error("Delete failed — record may already be gone.")


if st.session_state.confirm_delete_exam_id is not None:
    confirm_delete_exam_dialog(st.session_state.confirm_delete_exam_id)


# ===============================
# LOAD DATA
# ===============================

exams, load_error = safe_call(
    get_exams_filtered,
    search=search,
    grade_id=selected_grade_id,
    academic_year_id=selected_year_id,
)

if load_error:
    st.error(load_error)
    exams = []

df = pd.DataFrame(
    [exam_to_row(e) for e in exams],
    columns=["ID", "Student", "Grade", "Lesson", "Exam", "Score", "Out of", "Percentage", "Date"],
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
        "Grade": st.column_config.TextColumn(width="medium"),
        "Lesson": st.column_config.TextColumn(width="large"),
        "Exam": st.column_config.TextColumn(width="medium"),
        "Score": st.column_config.NumberColumn(format="%.1f"),
        "Out of": st.column_config.NumberColumn(format="%.1f"),
        "Percentage": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
        "Date": st.column_config.DateColumn(format="DD/MM/YYYY"),
    }
)


# ===============================
# METRIC CARDS
# ===============================

st.divider()

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Exams in Current View", len(df))
with c2:
    st.metric("Average Percentage", f"{df['Percentage'].mean():.1f}%" if not df.empty else "—")
with c3:
    st.metric("Highest Percentage", f"{df['Percentage'].max():.1f}%" if not df.empty else "—")

st.divider()


# ===============================
# ACTIONS
# ===============================

st.subheader("Exam Actions")

if df.empty:
    st.info("No exam scores found for the current filters.")
else:
    exam_id = st.selectbox(
        "Select Exam Record",
        df["ID"],
        format_func=lambda eid: f"{eid} — {df.loc[df['ID'] == eid, 'Student'].values[0]} ({df.loc[df['ID'] == eid, 'Exam'].values[0]})",
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("👁 View", use_container_width=True):
            st.session_state.view_exam_id = exam_id
            st.rerun()

    with c2:
        if st.button("✏ Edit", use_container_width=True):
            st.session_state.edit_exam_id = exam_id
            st.rerun()

    with c3:
        if st.button("🗑 Delete", use_container_width=True):
            st.session_state.confirm_delete_exam_id = exam_id
            st.rerun()