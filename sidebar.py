import streamlit as st
from pathlib import Path


def load_css():
    css_path = Path(__file__).resolve().parent / "assets" / "style.css"
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def show_sidebar():

    load_css()

    with st.sidebar:

        st.markdown(
            """
            <h2 style='text-align:center;'>🎓 Center System</h2>
            <p style='text-align:center;color:gray;'>
            Educational Center Management
            </p>
            """,
            unsafe_allow_html=True
        )

        st.divider()
        st.page_link(
            "app.py",
            label="Home",
            icon="🏠"
        )

        st.divider()

        st.page_link(
            "pages/01_Dashboard.py",
            label="Dashboard",
            icon="📊"
        )

        st.page_link(
            "pages/02_Students.py",
            label="Students",
            icon="👨‍🎓"
        )

        st.page_link(
            "pages/03_Lessons.py",
            label="Lessons",
            icon="📚"
        )

        st.page_link(
            "pages/04_Attendance.py",
            label="Attendance",
            icon="✅"
        )

        st.page_link(
            "pages/05_Exams.py",
            label="Exams",
            icon="📝"
        )

        st.page_link(
            "pages/06_Payments.py",
            label="Payments",
            icon="💰"
        )
        st.divider()

        st.success("Academic Year\n2026 / 2027")

        st.info("Administrator")

        st.caption("Version 1.0")