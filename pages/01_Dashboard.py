import calendar

import pandas as pd
import plotly.express as px
import streamlit as st

from crud import (
    attendance_summary,
    get_academic_years,
    get_dashboard_stats,
    get_grades,
    get_groups,
    monthly_revenue,
    students_by_grade,
    top_students,
    unpaid_students,
)
from sidebar import show_sidebar

st.set_page_config(
    page_title="Dashboard",
    page_icon="📊",
    layout="wide",
)

show_sidebar()

st.title("📊 Center Dashboard")
st.caption("Educational Center Management System")

st.divider()

# =====================================================
# FILTERS
# =====================================================

c1, c2, c3, c4 = st.columns([2, 2, 2, 1])

with c1:
    years = get_academic_years()
    year_lookup = {year.academic_year: year for year in years}
    year_options = ["All"] + list(year_lookup.keys())

    academic_year_name = st.selectbox("Academic Year", year_options)
    selected_academic_year = year_lookup.get(academic_year_name)
    academic_year_id = (
        selected_academic_year.academic_year_id
        if selected_academic_year is not None
        else None
    )

with c2:
    grades = get_grades()
    grade_lookup = {grade.grade_name: grade for grade in grades}
    grade_options = ["All"] + list(grade_lookup.keys())

    grade_name = st.selectbox("Grade", grade_options)
    selected_grade = grade_lookup.get(grade_name)
    grade_id = selected_grade.grade_id if selected_grade is not None else None

with c3:
    groups = get_groups()
    group_options = ["All"] + groups

    group_name = st.selectbox("Group", group_options)
    student_group = group_name if group_name != "All" else None

with c4:
    st.write("")
    st.write("")
    st.button("🔄 Refresh", use_container_width=True)

st.divider()

# =====================================================
# DASHBOARD STATS
# =====================================================

stats = get_dashboard_stats(
    academic_year_id=academic_year_id,
    grade_id=grade_id,
    student_group=student_group,
)

students = stats["students"]
lessons = stats["lessons"]
revenue = stats["revenue"]
active = stats["active"]

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("👨‍🎓 Total Students", students)

with col2:
    st.metric("📚 Lessons", lessons)

with col3:
    st.metric("💰 Revenue", f"{revenue:,.0f} EGP")

with col4:
    st.metric("🟢 Active Students", active)

st.divider()

# =====================================================
# CHARTS
# =====================================================

left, right = st.columns(2)

with left:
    st.subheader("👨‍🎓 Students Per Grade")

    grade_data = students_by_grade(
        academic_year_id=academic_year_id,
        grade_id=grade_id,
        student_group=student_group,
    )

    grade_df = pd.DataFrame(grade_data, columns=["Grade", "Students"])

    if grade_df.empty or grade_df["Students"].sum() == 0:
        st.info("No student data matches the selected filters.")
    else:
        fig = px.bar(grade_df, x="Grade", y="Students", text="Students")
        fig.update_layout(height=450, xaxis_title="", yaxis_title="Students")
        st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("💰 Monthly Revenue")

    revenue_data = monthly_revenue(
        academic_year_id=academic_year_id,
        grade_id=grade_id,
        student_group=student_group,
    )

    revenue_df = pd.DataFrame(revenue_data, columns=["Month", "Revenue"])

    if revenue_df.empty or revenue_df["Revenue"].sum() == 0:
        st.info("No revenue data matches the selected filters.")
    else:
        revenue_df["Month"] = revenue_df["Month"].apply(
            lambda month_num: calendar.month_name[month_num]
        )
        fig = px.line(revenue_df, x="Month", y="Revenue", markers=True)
        fig.update_layout(height=450, xaxis_title="Month", yaxis_title="Revenue (EGP)")
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# =====================================================
# ATTENDANCE & EXAMS
# =====================================================

left, right = st.columns(2)

with left:
    st.subheader("📋 Attendance Status")

    attendance_data = attendance_summary(
        academic_year_id=academic_year_id,
        grade_id=grade_id,
        student_group=student_group,
    )

    attendance_df = pd.DataFrame(attendance_data, columns=["Status", "Count"])

    if attendance_df.empty or attendance_df["Count"].sum() == 0:
        st.info("No attendance records found for the selected filters.")
    else:
        fig = px.pie(attendance_df, names="Status", values="Count", hole=0.60)
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("🏆 Top Students")

    top_data = top_students(
        limit=10,
        academic_year_id=academic_year_id,
        grade_id=grade_id,
        student_group=student_group,
    )

    top_df = pd.DataFrame(top_data, columns=["Student", "Average"])

    if top_df.empty:
        st.info("No exams available for the selected filters.")
    else:
        top_df["Average"] = top_df["Average"].astype(float).round(2)
        fig = px.bar(top_df, x="Student", y="Average", text="Average")
        fig.update_layout(height=420, xaxis_title="", yaxis_title="Average Score")
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# =====================================================
# TABLES
# =====================================================

left, right = st.columns(2)

with left:
    st.subheader("🥇 Top 10 Students")

    if top_df.empty:
        st.info("No data available for the selected filters.")
    else:
        st.dataframe(top_df, use_container_width=True, hide_index=True)

with right:
    st.subheader("🚨 Unpaid Students")

    unpaid_data = unpaid_students(
        academic_year_id=academic_year_id,
        grade_id=grade_id,
        student_group=student_group,
    )

    unpaid_df = pd.DataFrame(unpaid_data, columns=["Student", "Grade", "Month"])

    if unpaid_df.empty:
        st.success("There are no unpaid students for the selected filters 🎉")
    else:
        st.dataframe(unpaid_df, use_container_width=True, hide_index=True)

st.divider()

st.caption("Center Management System © 2026 | Dashboard")