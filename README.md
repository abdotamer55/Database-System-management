# 🎓 Education Center Management System

A professional **Education Center Management System** built with **Python, Streamlit, SQLAlchemy, and MySQL**.

The system helps instructors and education centers manage students, lessons, attendance, exams, and payments through a modern interactive dashboard.

---

# ✨ Features

## 📊 Dashboard

- Interactive analytics
- Student statistics
- Active / Inactive students
- Monthly income
- Attendance overview
- Payment overview
- Professional charts
- Real-time database statistics

---

## 👨‍🎓 Students Management

- Add Student
- Edit Student
- Delete Student
- View Student Details
- Search Students
- Filter by Grade
- Filter by Academic Year
- Filter by Group
- Active / Inactive Students

---

## 📚 Lessons Management

- Add Lesson
- Edit Lesson
- Delete Lesson
- Lesson Scheduling
- Grade Assignment
- Academic Year Support

---

## ✅ Attendance System

- Mark Attendance
- Present / Absent
- Attendance History
- Attendance Statistics

---

## 📝 Exams Management

- Create Exams
- Student Scores
- Total Score
- Performance Tracking

---

## 💰 Payments Management

- Record Payments
- Paid / Unpaid Status
- Monthly Fees
- Payment History
- Income Tracking

---

## 🎯 Academic Years

- Multiple Academic Years
- Current Year
- Upcoming Years
- Completed Years

---

## 🏫 Grade Management

Supports multiple grades including:

- Primary
- Baccalaureate

---

# 🛠️ Built With

- Python 3.12
- Streamlit
- SQLAlchemy ORM
- MySQL
- PyMySQL
- Pandas
- Plotly
- CSS
- JavaScript

---

# 📁 Project Structure

```text
Education-Center-Management-System
│
├── app.py
├── database.py
├── models.py
├── crud.py
├── sidebar.py
├── filters.py
├── settings.py
├── style.py
│
├── pages/
│   ├── 01_Dashboard.py
│   ├── 02_Students.py
│   ├── 03_Lessons.py
│   ├── 04_Attendance.py
│   ├── 05_Exams.py
│   ├── 06_Payments.py
│
├── assets/
│
├── requirements.txt
│
└── README.md
```

---

# 🗄️ Database Design

The project uses **MySQL** with SQLAlchemy ORM.

### Tables

- Academic_Years
- Grades
- Students
- Lessons
- Attendance
- Exams
- Payments

All tables are connected using **Foreign Keys** and SQLAlchemy Relationships.

---

# ⚡ Dashboard

The dashboard provides real-time analytics directly from the database.

### KPIs

- Total Students
- Active Students
- Inactive Students
- Monthly Revenue

### Charts

- Students by Grade
- Students by Academic Year
- Attendance Statistics
- Payment Statistics

---

# 🔍 Students Page

Features include:

- Advanced Search
- Dynamic Filters
- Add Student Dialog
- Edit Student Dialog
- Delete Confirmation
- View Student Profile
- Professional Data Table

---

# 🔐 Data Validation

The application validates:

- Required Fields
- Duplicate Entries
- Foreign Keys
- Invalid Data
- Database Integrity

---

# 🎨 User Interface

The application uses a custom Dark Theme featuring:

- Modern Sidebar
- Professional Dashboard
- Responsive Layout
- Animated Components
- Interactive Charts
- Custom CSS
- Custom JavaScript

Inspired by:

- Notion
- GitHub
- Vercel
- Stripe Dashboard
- Microsoft Admin Center

---

# 🚀 Installation

Clone the repository

```bash
git clone https://github.com/yourusername/Education-Center-Management-System.git
```

Move into the project

```bash
cd Education-Center-Management-System
```

Install requirements

```bash
pip install -r requirements.txt
```

---

# ⚙️ Configure Database

Create a MySQL database.

Example:

```sql
CREATE DATABASE center_db;
```

Update your database credentials inside

```python
database.py
```

Example

```python
DATABASE_URL = "mysql+pymysql://root:password@localhost:3306/center_db"
```

---

# ▶️ Run Application

```bash
streamlit run app.py
```

---

# 📷 Screenshots

You can place screenshots here.

Example:

```
assets/dashboard.png

assets/students.png

assets/payments.png
```

---

# 📈 Future Improvements

- Authentication System
- User Roles
- Backup & Restore
- Export Excel
- Export PDF
- Notifications
- SMS Integration
- WhatsApp Integration
- Email Reports
- Parent Portal
- Student Portal
- Teacher Portal
- Financial Reports
- AI Insights

---

# 🧠 Technologies

| Technology | Usage |
| ------------ | ------ |
| Python | Backend |
| Streamlit | Frontend |
| SQLAlchemy | ORM |
| MySQL | Database |
| Pandas | Data Processing |
| Plotly | Visualization |
| CSS | UI Design |
| JavaScript | UI Enhancements |

---

# 📊 Project Status

Current Progress

- ✅ Database Design
- ✅ SQLAlchemy Models
- ✅ CRUD Operations
- ✅ Dashboard
- ✅ Student Management
- 🚧 Lessons Management
- 🚧 Attendance Management
- 🚧 Exams Management
- 🚧 Payments Management
- 🚧 Authentication
- 🚧 Reports

---

# 👨‍💻 Author

**Abdelrahman Tamer**

AI Engineer | Python Developer | Data Analyst

GitHub:
<https://github.com/abdotamer55>


---

# ⭐ Support

If you like this project, consider giving it a ⭐ on GitHub.

It helps support the project and encourages future development.

---

# 📄 License

This project is intended for educational purposes and portfolio demonstration.

Feel free to fork, improve, and contribute.
