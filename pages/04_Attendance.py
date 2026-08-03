"""
Attendance Management Page
=========================
No fake/dummy data — every value comes from a real CRUD call against MySQL.

CRUD contracts relied on (see crud.py):
    get_grades() -> list[Grade]
    get_academic_years() -> list[AcademicYear]
    get_lessons_filtered(grade_id=None, academic_year_id=None) -> list[Lesson]
    get_students_filtered(grade_id=None, is_active=True) -> list[Student]
    get_attendance_for_lesson(lesson_id) -> {student_id: status}
    save_attendance(student_id, lesson_id, status) -> bool          (upsert)
    get_attendance_filtered(lesson_id=None, grade_id=None,
                             academic_year_id=None, status=None, search="") -> list[Attendance]
    update_attendance_status(attendance_id, status) -> bool
    delete_attendance(attendance_id) -> bool
    get_lesson_attendance_stats(lesson_id) -> {"present": int, "absent": int}

Only add_attendance() already existed for this entity in crud.py; every
other function above (save_attendance, get_attendance_for_lesson,
get_attendance_filtered, update_attendance_status, delete_attendance,
get_lesson_attendance_stats) was added following the existing
session/eager-loading pattern. save_attendance() is used instead of the
old add_attendance() because it upserts — re-saving a lesson's sheet
never creates duplicate rows for the same student+lesson.
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
    get_attendance_for_lesson,
    save_attendance,
    get_attendance_filtered,
    update_attendance_status,
    delete_attendance,
    get_lesson_attendance_stats,
)

st.set_page_config(page_title="Attendance", page_icon="✅", layout="wide")
show_sidebar()

st.title("✅ Attendance Management")
st.divider()


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


def record_to_row(r):
    return {
        "ID": r.attendance_id,
        "Student": r.student.full_name if r.student else "—",
        "Lesson": r.lesson.lesson_title if r.lesson else "—",
        "Grade": r.lesson.grade.grade_name if r.lesson and r.lesson.grade else "—",
        "Date": r.lesson.lesson_date if r.lesson else None,
        "Status": "🟢 Present" if r.status == "Present" else "🔴 Absent",
    }


tab_take, tab_log = st.tabs(["📝 Take Attendance", "📋 Attendance Log"])


# =====================================================================
# TAB 1 — TAKE ATTENDANCE
# =====================================================================

with tab_take:

    grades = get_grades()
    years = get_academic_years()

    c1, c2 = st.columns(2)
    with c1:
        grade_choice = st.selectbox(
            "Grade *", grades, format_func=lambda g: g.grade_name, key="take_grade"
        )
    with c2:
        year_choice = st.selectbox(
            "Academic Year *", years, format_func=lambda y: y.academic_year, key="take_year"
        )

    lessons = []
    if grade_choice and year_choice:
        lessons, lessons_error = safe_call(
            get_lessons_filtered,
            grade_id=grade_choice.grade_id,
            academic_year_id=year_choice.academic_year_id,
        )
        if lessons_error:
            st.error(lessons_error)
            lessons = []

    if not lessons:
        st.info("No lessons found for this Grade + Academic Year. Add one on the Lessons page first.")
    else:
        lesson_choice = st.selectbox(
            "Lesson *",
            lessons,
            format_func=lambda l: f"#{l.lesson_number} — {l.lesson_title} ({l.lesson_date.strftime('%d/%m/%Y') if l.lesson_date else '—'})",
            key="take_lesson",
        )

        students, students_error = safe_call(
            get_students_filtered, grade_id=grade_choice.grade_id, is_active=True
        )
        if students_error:
            st.error(students_error)
            students = []

        if not students:
            st.info("No active students found in this grade.")
        else:
            existing, existing_error = safe_call(get_attendance_for_lesson, lesson_choice.lesson_id)
            if existing_error:
                st.error(existing_error)
                existing = {}

            st.divider()
            st.markdown(f"##### Marking attendance for **{lesson_choice.lesson_title}**")

            with st.form("take_attendance_form"):
                marks = {}
                for s in students:
                    current = existing.get(s.student_id, "Present")
                    marks[s.student_id] = st.radio(
                        s.full_name,
                        ["Present", "Absent"],
                        index=0 if current == "Present" else 1,
                        horizontal=True,
                        key=f"mark_{lesson_choice.lesson_id}_{s.student_id}",
                    )

                st.divider()
                submit = st.form_submit_button(
                    "💾 Save Attendance", use_container_width=True, type="primary"
                )

                if submit:
                    errors = []
                    for student_id, status in marks.items():
                        _, error = safe_call(save_attendance, student_id, lesson_choice.lesson_id, status)
                        if error:
                            errors.append(error)

                    if errors:
                        st.error(f"Some records failed to save: {errors[0]}")
                    else:
                        st.success(f"Attendance saved for {len(marks)} student(s).")
                        st.rerun()

            stats, stats_error = safe_call(get_lesson_attendance_stats, lesson_choice.lesson_id)
            if not stats_error:
                st.divider()
                s1, s2 = st.columns(2)
                s1.metric("🟢 Present", stats["present"])
                s2.metric("🔴 Absent", stats["absent"])


# =====================================================================
# TAB 2 — ATTENDANCE LOG
# =====================================================================

with tab_log:

    grades = get_grades()
    years = get_academic_years()

    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])

    with c1:
        log_search = st.text_input("🔍 Search Student", placeholder="Type a name...", key="log_search")

    with c2:
        log_grade_filter = st.selectbox(
            "Grade", ["All"] + [g.grade_name for g in grades], key="log_grade"
        )

    with c3:
        log_year_filter = st.selectbox(
            "Academic Year", ["All"] + [y.academic_year for y in years], key="log_year"
        )

    with c4:
        log_status_filter = st.selectbox("Status", ["All", "Present", "Absent"], key="log_status")

    log_grade_id = next(
        (g.grade_id for g in grades if g.grade_name == log_grade_filter), None
    ) if log_grade_filter != "All" else None

    log_year_id = next(
        (y.academic_year_id for y in years if y.academic_year == log_year_filter), None
    ) if log_year_filter != "All" else None

    records, records_error = safe_call(
        get_attendance_filtered,
        search=log_search,
        grade_id=log_grade_id,
        academic_year_id=log_year_id,
        status=log_status_filter,
    )

    if records_error:
        st.error(records_error)
        records = []

    log_df = pd.DataFrame(
        [record_to_row(r) for r in records],
        columns=["ID", "Student", "Lesson", "Grade", "Date", "Status"],
    )

    st.dataframe(
        log_df,
        use_container_width=True,
        hide_index=True,
        height=420,
        column_config={
            "ID": st.column_config.NumberColumn(width="small"),
            "Student": st.column_config.TextColumn(width="large"),
            "Lesson": st.column_config.TextColumn(width="large"),
            "Grade": st.column_config.TextColumn(width="medium"),
            "Date": st.column_config.DateColumn(format="DD/MM/YYYY"),
        }
    )

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Present (filtered)", int((log_df["Status"] == "🟢 Present").sum()) if not log_df.empty else 0)
    with c2:
        st.metric("Absent (filtered)", int((log_df["Status"] == "🔴 Absent").sum()) if not log_df.empty else 0)

    st.divider()
    st.subheader("Record Actions")

    if log_df.empty:
        st.info("No attendance records found for the current filters.")
    else:
        record_id = st.selectbox(
            "Select Record",
            log_df["ID"],
            format_func=lambda rid: f"{rid} — {log_df.loc[log_df['ID'] == rid, 'Student'].values[0]} ({log_df.loc[log_df['ID'] == rid, 'Lesson'].values[0]})",
            key="log_record_select",
        )
        current_status = log_df.loc[log_df["ID"] == record_id, "Status"].values[0]

        a1, a2 = st.columns(2)
        with a1:
            new_status = st.selectbox(
                "Change status to",
                ["Present", "Absent"],
                index=0 if current_status == "🟢 Present" else 1,
                key="log_status_change",
            )
            if st.button("💾 Update Status", use_container_width=True):
                updated, error = safe_call(update_attendance_status, record_id, new_status)
                if error:
                    st.error(error)
                elif updated:
                    st.success("Attendance record updated.")
                    st.rerun()
                else:
                    st.error("Record not found — it may already be deleted.")

        with a2:
            st.write("")
            st.write("")
            if st.button("🗑 Delete Record", use_container_width=True):
                deleted, error = safe_call(delete_attendance, record_id)
                if error:
                    st.error(error)
                elif deleted:
                    st.success("Attendance record deleted.")
                    st.rerun()
                else:
                    st.error("Record not found — it may already be deleted.")