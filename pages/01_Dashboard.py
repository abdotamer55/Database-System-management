import streamlit as st
import pandas as pd
import plotly.express as px

from crud import (
    get_academic_years,
    get_dashboard_stats,
    get_grades,
    students_by_grade,
    monthly_revenue,
    attendance_summary,
    top_students,
    unpaid_students,
    get_groups
)
from sidebar import show_sidebar

st.set_page_config(
    page_title="Dashboard",
    page_icon="📊",
    layout="wide"
)

show_sidebar()

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Center Dashboard")
st.caption("Educational Center Management System")

st.divider()

# =====================================================
# FILTERS
# =====================================================

c1, c2, c3, c4 = st.columns([2,2,2,1])

with c1:
    years = get_academic_years()

    year_options = ["All"] + [
        y.academic_year
        for y in years
    ]

    academic_year = st.selectbox(
        "Academic Year",
        year_options
    )

with c2:
    grades = get_grades()

    grade_options = ["All"] + [
        g.grade_name
        for g in grades
    ]

    grade = st.selectbox(
        "Grade",
        grade_options
    )

with c3:
    groups = get_groups()

    group_options = ["All"] + groups

    group = st.selectbox(
        "Group",
        group_options
    )

with c4:

    st.write("")
    st.write("")

    refresh = st.button(
        "🔄 Refresh",
        use_container_width=True
    )

st.divider()

# =====================================================
# DASHBOARD STATS
# =====================================================

stats = get_dashboard_stats()

students = stats["students"]
lessons = stats["lessons"]
revenue = stats["revenue"]
active = stats["active"]

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "👨‍🎓 Total Students",
        students
    )

with col2:

    st.metric(
        "📚 Lessons",
        lessons
    )

with col3:

    st.metric(
        "💰 Revenue",
        f"{revenue:,.0f} EGP"
    )

with col4:

    st.metric(
        "🟢 Active Students",
        active
    )

st.divider()

# =====================================================
# CHARTS
# =====================================================

left, right = st.columns(2)

# =====================================================
# STUDENTS PER GRADE
# =====================================================

with left:

    st.subheader("👨‍🎓 Students Per Grade")

    grades = students_by_grade()

    df = pd.DataFrame(
        grades,
        columns=[
            "Grade",
            "Students"
        ]
    )

    fig = px.bar(
        df,
        x="Grade",
        y="Students",
        text="Students"
    )

    fig.update_layout(
        height=450,
        xaxis_title="",
        yaxis_title="Students"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =====================================================
# MONTHLY REVENUE
# =====================================================

with right:

    st.subheader("💰 Monthly Revenue")

    revenue_data = monthly_revenue()

    revenue_df = pd.DataFrame(
        revenue_data,
        columns=[
            "Month",
            "Revenue"
        ]
    )

    fig = px.line(
        revenue_df,
        x="Month",
        y="Revenue",
        markers=True
    )

    fig.update_layout(
        height=450,
        xaxis_title="Month",
        yaxis_title="Revenue (EGP)"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

st.divider()
# =====================================================
# ATTENDANCE & EXAMS
# =====================================================

left, right = st.columns(2)

# =====================================================
# ATTENDANCE DONUT
# =====================================================

with left:

    st.subheader("📋 Attendance Status")

    attendance = attendance_summary()

    attendance_df = pd.DataFrame(
        attendance,
        columns=[
            "Status",
            "Count"
        ]
    )

    if attendance_df.empty:

        st.info("No attendance records found.")

    else:

        fig = px.pie(
            attendance_df,
            names="Status",
            values="Count",
            hole=0.60
        )

        fig.update_layout(height=420)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# =====================================================
# EXAMS
# =====================================================

with right:

    st.subheader("🏆 Top Students")

    top = top_students()

    top_df = pd.DataFrame(
        top,
        columns=[
            "Student",
            "Average"
        ]
    )

    if top_df.empty:

        st.info("No exams available.")

    else:

        top_df["Average"] = top_df["Average"].astype(float).round(2)

        fig = px.bar(
            top_df,
            x="Student",
            y="Average",
            text="Average"
        )

        fig.update_layout(
            height=420,
            xaxis_title="",
            yaxis_title="Average Score"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

st.divider()

# =====================================================
# TABLES
# =====================================================

left, right = st.columns(2)

# =====================================================
# TOP STUDENTS TABLE
# =====================================================

with left:

    st.subheader("🥇 Top 10 Students")

    if top_df.empty:

        st.info("No data available.")

    else:

        st.dataframe(
            top_df,
            use_container_width=True,
            hide_index=True
        )

# =====================================================
# UNPAID STUDENTS
# =====================================================

with right:

    st.subheader("🚨 Unpaid Students")

    unpaid = unpaid_students()

    unpaid_df = pd.DataFrame(
        unpaid,
        columns=[
            "Student",
            "Grade",
            "Month"
        ]
    )

    if unpaid_df.empty:

        st.success("There are no unpaid students 🎉")

    else:

        st.dataframe(
            unpaid_df,
            use_container_width=True,
            hide_index=True
        )

st.divider()

# =====================================================
# FOOTER
# =====================================================

st.caption(
    "Center Management System © 2026 | Dashboard"
)