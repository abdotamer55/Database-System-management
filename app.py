import streamlit as st
from sidebar import show_sidebar

st.set_page_config(
    page_title="Dashboard",
    page_icon="📊",
    layout="wide"
)
show_sidebar()

# ==========================================
# Page Configuration
# ==========================================

st.set_page_config(
    page_title="Center Management System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.set_page_config(
    page_title="Center Management System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded" 
)
# ==========================================
# Header
# ==========================================

st.title("🎓 Center Management System")

st.caption(
    "Manage students, lessons, attendance, exams and payments from one place."
)

st.divider()

# ==========================================
# Hero Section
# ==========================================

left, right = st.columns([2, 1])

with left:

    st.subheader("Welcome 👋")

    st.write("""
This application helps you manage your educational center professionally.

Using this system you can:

- 👨‍🎓 Manage Students
- 📚 Organize Lessons
- 📋 Track Attendance
- 📝 Record Exams & Scores
- 💰 Manage Payments
- 📊 View Statistics & Reports
""")

    st.info("Select a module from the sidebar to start.")

with right:

    st.image(
        "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=700",
        use_container_width=True
    )

st.divider()

# ==========================================
# Quick Access
# ==========================================

st.subheader("🚀 Quick Access")

col1, col2, col3 = st.columns(3)

with col1:

    if st.button(
        "👨‍🎓 Students",
        use_container_width=True
    ):
        st.switch_page("pages/02_Students.py")

with col2:

    if st.button(
        "📚 Lessons",
        use_container_width=True
    ):
        st.switch_page("pages/03_Lessons.py")

with col3:

    if st.button(
        "📋 Attendance",
        use_container_width=True
    ):
        st.switch_page("pages/04_Attendance.py")

col4, col5 = st.columns(2)

with col4:

    if st.button(
        "📝 Exams",
        use_container_width=True
    ):
        st.switch_page("pages/05_Exams.py")

with col5:

    if st.button(
        "💰 Payments",
        use_container_width=True
    ):
        st.switch_page("pages/06_Payments.py")

st.divider()

# ==========================================
# Features
# ==========================================

st.subheader("System Features")

c1, c2, c3 = st.columns(3)

with c1:
    st.success("""
### Students

- Add Students
- Update Students
- Delete Students
- Search Students
""")

with c2:
    st.info("""
### Academic

- Lessons
- Attendance
- Exams
- Grades
""")

with c3:
    st.warning("""
### Financial

- Monthly Payments
- Income Tracking
- Payment History
""")

st.divider()

st.success("✅ Center Management System is Ready.")