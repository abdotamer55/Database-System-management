from sqlalchemy import select
from sqlalchemy.orm import joinedload
from database import SessionLocal
from sqlalchemy import func
from models import Student, Lesson, Payment, Attendance
from models import (
    Student,
    Grade,
    AcademicYear,
    Lesson,
    Attendance,
    Exam,
    Payment
)

def get_session():
    return SessionLocal()
  
# Add Student
def add_student(
    full_name,
    grade_id,
    student_group,
    phone,
    parent_phone,
    monthly_fee,
    join_date,
    academic_year_id,
    is_active=True
):
    session = get_session()

    try:

        student = Student(
            full_name=full_name,
            grade_id=grade_id,
            student_group=student_group,
            phone=phone,
            parent_phone=parent_phone,
            monthly_fee=monthly_fee,
            join_date=join_date,
            academic_year_id=academic_year_id,
            is_active=is_active
        )

        session.add(student)

        session.commit()

        session.refresh(student)

        return student

    finally:

        session.close()
        
# Show all students
def get_students():

    session = get_session()

    try:

        students = (
            session.query(Student)
            .options(
                joinedload(Student.grade),
                joinedload(Student.academic_year)
            )
            .all()
        )

        return students

    finally:

        session.close()
  
# Search students by name
def search_student(keyword):

    session = get_session()

    try:

        students = (
            session.query(Student)
            .filter(
                Student.full_name.ilike(f"%{keyword}%")
            )
            .all()
        )

        return students

    finally:

        session.close()
        
# Modify student details
def update_student(student_id, **kwargs):

    session = get_session()

    try:

        student = session.get(Student, student_id)

        if not student:
            return False

        for key, value in kwargs.items():

            if hasattr(student, key):

                setattr(student, key, value)

        session.commit()

        return True

    finally:

        session.close()
        
# Delete student
def delete_student(student_id):

    session = get_session()

    try:

        student = session.get(Student, student_id)

        if not student:

            return False

        session.delete(student)

        session.commit()

        return True

    finally:

        session.close()
        
# Lesson management functions
def add_lesson(
    grade_id,
    lesson_number,
    lesson_title,
    lesson_date,
    academic_year_id
):

    session = get_session()

    try:

        lesson = Lesson(
            grade_id=grade_id,
            lesson_number=lesson_number,
            lesson_title=lesson_title,
            lesson_date=lesson_date,
            academic_year_id=academic_year_id
        )

        session.add(lesson)

        session.commit()

        session.refresh(lesson)

        return lesson

    finally:

        session.close()

# Attendance management functions
def add_attendance(
    student_id,
    lesson_id,
    status
):

    session = get_session()

    try:

        attendance = Attendance(
            student_id=student_id,
            lesson_id=lesson_id,
            status=status
        )

        session.add(attendance)

        session.commit()

    finally:

        session.close()

# Exam management functions
def add_exam(
    student_id,
    lesson_id,
    exam_name,
    score,
    total_score,
    exam_date
):

    session = get_session()

    try:

        exam = Exam(
            student_id=student_id,
            lesson_id=lesson_id,
            exam_name=exam_name,
            score=score,
            total_score=total_score,
            exam_date=exam_date
        )

        session.add(exam)

        session.commit()

    finally:

        session.close()

# Payment management functions
def add_payment(
    student_id,
    payment_for_month,
    amount,
    payment_date,
    status
):

    session = get_session()

    try:

        payment = Payment(
            student_id=student_id,
            payment_for_month=payment_for_month,
            amount=amount,
            payment_date=payment_date,
            status=status
        )

        session.add(payment)

        session.commit()

    finally:

        session.close()
        
# Get total number of students
def get_total_students():
    session = get_session()

    try:
        return session.query(func.count(Student.student_id)).scalar()

    finally:
        session.close()

# Get total number of active students        
def get_active_students():
    session = get_session()

    try:
        return (
            session.query(func.count(Student.student_id))
            .filter(Student.is_active == True)
            .scalar()
        )

    finally:
        session.close()

# Get total number of inactive students
def get_inactive_students():
    session = get_session()

    try:
        return (
            session.query(func.count(Student.student_id))
            .filter(Student.is_active == False)
            .scalar()
        )

    finally:
        session.close()

# Get total number of students in a specific grade
def get_grades():

    session = get_session()

    try:
        return (
            session.query(Grade)
            .order_by(Grade.grade_name)
            .all()
        )

    finally:
        session.close()
        
# Get total number of students in a specific group
def get_groups():

    session = SessionLocal()

    try:

        groups = (
            session.query(
                Student.student_group
            )
            .distinct()
            .order_by(
                Student.student_group
            )
            .all()
        )

        return [g[0] for g in groups]

    finally:
        session.close()

# Get total number of students in a specific academic year
def get_academic_years():

    session = get_session()

    try:
        return (
            session.query(AcademicYear)
            .order_by(AcademicYear.academic_year.desc())
            .all()
        )

    finally:
        session.close()

# Get students filtered by search, grade, academic year, group and status.
# All filtering happens in SQL so nothing is ever narrowed down after the
# fact in a DataFrame.
def get_students_filtered(
    search="",
    grade_id=None,
    academic_year_id=None,
    student_group=None,
    is_active=None
):

    session = get_session()

    try:

        query = (
            session.query(Student)
            .options(
                joinedload(Student.grade),
                joinedload(Student.academic_year)
            )
        )

        if search:

            query = query.filter(
                Student.full_name.ilike(f"%{search}%")
            )

        if grade_id:

            query = query.filter(
                Student.grade_id == grade_id
            )

        if academic_year_id:

            query = query.filter(
                Student.academic_year_id == academic_year_id
            )

        if student_group:

            query = query.filter(
                Student.student_group == student_group
            )

        if is_active is not None:

            query = query.filter(
                Student.is_active == is_active
            )

        return (
            query.order_by(Student.student_id.desc())
            .all()
        )

    finally:

        session.close()

# Check whether a student with this name already exists (case-insensitive).
# Used by the Add dialog to warn about likely duplicate entries.
def student_name_exists(full_name, exclude_id=None):

    session = get_session()

    try:

        query = session.query(Student).filter(
            func.lower(Student.full_name) == full_name.strip().lower()
        )

        if exclude_id:

            query = query.filter(Student.student_id != exclude_id)

        return session.query(query.exists()).scalar()

    finally:

        session.close()
        
from sqlalchemy import distinct

def get_student_filters():

    session = get_session()

    try:

        grades = (
            session.query(Grade)
            .order_by(Grade.grade_name)
            .all()
        )

        groups = (
            session.query(
                distinct(Student.student_group)
            )
            .filter(Student.student_group != None)
            .all()
        )

        groups = [g[0] for g in groups]

        return grades, groups

    finally:

        session.close()

# Get student details by ID (eager-loaded to avoid DetachedInstanceError
# once the session that fetched it is closed)
def get_student(student_id):

    session = get_session()

    try:

        return (
            session.query(Student)
            .options(
                joinedload(Student.grade),
                joinedload(Student.academic_year)
            )
            .filter(Student.student_id == student_id)
            .first()
        )

    finally:

        session.close()

# Modified Statues of student      
def toggle_student_status(student_id):

    session = get_session()

    try:

        student = session.get(Student, student_id)

        if student:

            student.is_active = not student.is_active

            session.commit()

            return True

        return False

    finally:

        session.close()
        
def get_dashboard_stats():
    session = get_session()

    try:

        total_students = session.query(
            func.count(Student.student_id)
        ).scalar()

        active_students = session.query(
            func.count(Student.student_id)
        ).filter(
            Student.is_active == True
        ).scalar()

        total_lessons = session.query(
            func.count(Lesson.lesson_id)
        ).scalar()

        total_payments = session.query(
            func.coalesce(func.sum(Payment.amount), 0)
        ).scalar()

        return {
            "students": total_students,
            "active": active_students,
            "lessons": total_lessons,
            "revenue": float(total_payments)
        }

    finally:
        session.close()
        
def students_by_grade():

    session = get_session()

    try:

        result = (
            session.query(
                Grade.grade_name,
                func.count(Student.student_id)
            )
            .join(Student)
            .group_by(Grade.grade_name)
            .all()
        )

        return result

    finally:

        session.close()

def monthly_revenue():

    session = get_session()

    try:

        result = (
            session.query(
                func.month(Payment.payment_date),
                func.sum(Payment.amount)
            )
            .group_by(
                func.month(Payment.payment_date)
            )
            .all()
        )

        return result

    finally:

        session.close()
def attendance_summary():

    session = SessionLocal()

    try:

        result = (
            session.query(
                Attendance.status,
                func.count(Attendance.attendance_id)
            )
            .group_by(Attendance.status)
            .all()
        )

        return result

    finally:
        session.close()
        
def top_students(limit=10):

    session = get_session()

    try:

        result = (
            session.query(
                Student.full_name,
                func.avg(Exam.score).label("avg_score")
            )
            .join(Exam)
            .group_by(Student.student_id)
            .order_by(func.avg(Exam.score).desc())
            .limit(limit)
            .all()
        )

        return result

    finally:

        session.close()
        
def unpaid_students():

    session = get_session()

    try:

        result = (
            session.query(Student)
            .join(Payment)
            .filter(
                Payment.status == "Pending"
            )
            .all()
        )

        return result

    finally:

        session.close()
        

# =====================================================================
# LESSON QUERY / UPDATE / DELETE FUNCTIONS
# (add_lesson() already existed above; these were missing)
# =====================================================================

def get_lessons_filtered(search="", grade_id=None, academic_year_id=None):

    session = get_session()

    try:

        query = (
            session.query(Lesson)
            .options(
                joinedload(Lesson.grade),
                joinedload(Lesson.academic_year)
            )
        )

        if search:
            query = query.filter(Lesson.lesson_title.ilike(f"%{search}%"))

        if grade_id:
            query = query.filter(Lesson.grade_id == grade_id)

        if academic_year_id:
            query = query.filter(Lesson.academic_year_id == academic_year_id)

        return (
            query.order_by(Lesson.lesson_date.desc(), Lesson.lesson_number.desc())
            .all()
        )

    finally:
        session.close()


def get_lesson(lesson_id):

    session = get_session()

    try:
        return (
            session.query(Lesson)
            .options(
                joinedload(Lesson.grade),
                joinedload(Lesson.academic_year)
            )
            .filter(Lesson.lesson_id == lesson_id)
            .first()
        )

    finally:
        session.close()


def update_lesson(lesson_id, **kwargs):

    session = get_session()

    try:
        lesson = session.get(Lesson, lesson_id)

        if not lesson:
            return False

        for key, value in kwargs.items():
            if hasattr(lesson, key):
                setattr(lesson, key, value)

        session.commit()
        return True

    finally:
        session.close()


def delete_lesson(lesson_id):
    """Deletes a lesson. Attendance and Exam records linked to it are
    removed too, via the cascade="all, delete-orphan" already defined
    on Lesson.attendance / Lesson.exams in models.py."""

    session = get_session()

    try:
        lesson = session.get(Lesson, lesson_id)

        if not lesson:
            return False

        session.delete(lesson)
        session.commit()
        return True

    finally:
        session.close()


def get_total_lessons():

    session = get_session()

    try:
        return session.query(func.count(Lesson.lesson_id)).scalar()

    finally:
        session.close()


# =====================================================================
# ATTENDANCE QUERY / UPSERT / UPDATE / DELETE FUNCTIONS
# (add_attendance() already existed above; these were missing)
# =====================================================================

def get_attendance_filtered(
    lesson_id=None,
    grade_id=None,
    academic_year_id=None,
    status=None,
    search=""
):

    session = get_session()

    try:
        query = (
            session.query(Attendance)
            .options(
                joinedload(Attendance.student),
                joinedload(Attendance.lesson).joinedload(Lesson.grade)
            )
        )

        if grade_id or academic_year_id:
            query = query.join(Lesson, Attendance.lesson_id == Lesson.lesson_id)

            if grade_id:
                query = query.filter(Lesson.grade_id == grade_id)

            if academic_year_id:
                query = query.filter(Lesson.academic_year_id == academic_year_id)

        if lesson_id:
            query = query.filter(Attendance.lesson_id == lesson_id)

        if status and status != "All":
            query = query.filter(Attendance.status == status)

        if search:
            query = query.join(
                Student, Attendance.student_id == Student.student_id
            ).filter(Student.full_name.ilike(f"%{search}%"))

        return query.order_by(Attendance.attendance_id.desc()).all()

    finally:
        session.close()


def get_attendance_for_lesson(lesson_id):
    """All attendance records already saved for a given lesson, keyed
    for quick lookup when rendering the take-attendance sheet."""

    session = get_session()

    try:
        records = (
            session.query(Attendance)
            .filter(Attendance.lesson_id == lesson_id)
            .all()
        )
        return {r.student_id: r.status for r in records}

    finally:
        session.close()


def save_attendance(student_id, lesson_id, status):
    """Create or update the attendance record for this student+lesson
    pair (upsert), so re-saving a lesson's sheet never creates dupes."""

    session = get_session()

    try:
        record = (
            session.query(Attendance)
            .filter(
                Attendance.student_id == student_id,
                Attendance.lesson_id == lesson_id
            )
            .first()
        )

        if record:
            record.status = status
        else:
            record = Attendance(
                student_id=student_id,
                lesson_id=lesson_id,
                status=status
            )
            session.add(record)

        session.commit()
        return True

    finally:
        session.close()


def update_attendance_status(attendance_id, status):

    session = get_session()

    try:
        record = session.get(Attendance, attendance_id)

        if not record:
            return False

        record.status = status
        session.commit()
        return True

    finally:
        session.close()


def delete_attendance(attendance_id):

    session = get_session()

    try:
        record = session.get(Attendance, attendance_id)

        if not record:
            return False

        session.delete(record)
        session.commit()
        return True

    finally:
        session.close()


def get_lesson_attendance_stats(lesson_id):

    session = get_session()

    try:
        present = (
            session.query(func.count(Attendance.attendance_id))
            .filter(
                Attendance.lesson_id == lesson_id,
                Attendance.status == "Present"
            )
            .scalar()
        )

        absent = (
            session.query(func.count(Attendance.attendance_id))
            .filter(
                Attendance.lesson_id == lesson_id,
                Attendance.status == "Absent"
            )
            .scalar()
        )

        return {"present": present or 0, "absent": absent or 0}

    finally:
        session.close()


# =====================================================================
# EXAM QUERY / UPDATE / DELETE FUNCTIONS
# (add_exam() already existed above; these were missing)
# =====================================================================

def get_exams_filtered(search="", grade_id=None, academic_year_id=None, lesson_id=None):

    session = get_session()

    try:
        query = (
            session.query(Exam)
            .options(
                joinedload(Exam.student),
                joinedload(Exam.lesson).joinedload(Lesson.grade)
            )
        )

        if lesson_id:
            query = query.filter(Exam.lesson_id == lesson_id)

        if grade_id or academic_year_id:
            query = query.join(Lesson, Exam.lesson_id == Lesson.lesson_id)

            if grade_id:
                query = query.filter(Lesson.grade_id == grade_id)

            if academic_year_id:
                query = query.filter(Lesson.academic_year_id == academic_year_id)

        if search:
            query = query.join(
                Student, Exam.student_id == Student.student_id
            ).filter(Student.full_name.ilike(f"%{search}%"))

        return query.order_by(Exam.exam_date.desc()).all()

    finally:
        session.close()


def get_exam(exam_id):

    session = get_session()

    try:
        return (
            session.query(Exam)
            .options(
                joinedload(Exam.student),
                joinedload(Exam.lesson).joinedload(Lesson.grade)
            )
            .filter(Exam.exam_id == exam_id)
            .first()
        )

    finally:
        session.close()


def update_exam(exam_id, **kwargs):

    session = get_session()

    try:
        exam = session.get(Exam, exam_id)

        if not exam:
            return False

        for key, value in kwargs.items():
            if hasattr(exam, key):
                setattr(exam, key, value)

        session.commit()
        return True

    finally:
        session.close()


def delete_exam(exam_id):

    session = get_session()

    try:
        exam = session.get(Exam, exam_id)

        if not exam:
            return False

        session.delete(exam)
        session.commit()
        return True

    finally:
        session.close()


# =====================================================================
# PAYMENT QUERY / UPDATE / DELETE FUNCTIONS
# (add_payment() already existed above; these were missing)
# =====================================================================

def get_payments_filtered(search="", student_id=None, status=None, month=None):

    session = get_session()

    try:
        query = session.query(Payment).options(joinedload(Payment.student))

        if student_id:
            query = query.filter(Payment.student_id == student_id)

        if status and status != "All":
            query = query.filter(Payment.status == status)

        if month and month != "All":
            query = query.filter(Payment.payment_for_month == month)

        if search:
            query = query.join(
                Student, Payment.student_id == Student.student_id
            ).filter(Student.full_name.ilike(f"%{search}%"))

        return query.order_by(Payment.payment_date.desc()).all()

    finally:
        session.close()


def get_payment(payment_id):

    session = get_session()

    try:
        return (
            session.query(Payment)
            .options(joinedload(Payment.student))
            .filter(Payment.payment_id == payment_id)
            .first()
        )

    finally:
        session.close()


def update_payment(payment_id, **kwargs):

    session = get_session()

    try:
        payment = session.get(Payment, payment_id)

        if not payment:
            return False

        for key, value in kwargs.items():
            if hasattr(payment, key):
                setattr(payment, key, value)

        session.commit()
        return True

    finally:
        session.close()


def delete_payment(payment_id):

    session = get_session()

    try:
        payment = session.get(Payment, payment_id)

        if not payment:
            return False

        session.delete(payment)
        session.commit()
        return True

    finally:
        session.close()


def get_payment_stats():
    """Totals used by the Payments page metric cards."""

    session = get_session()

    try:
        total_paid = (
            session.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.status == "Paid")
            .scalar()
        )

        total_unpaid = (
            session.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.status == "Unpaid")
            .scalar()
        )

        pending_count = (
            session.query(func.count(Payment.payment_id))
            .filter(Payment.status == "Unpaid")
            .scalar()
        )

        return {
            "paid": float(total_paid or 0),
            "unpaid": float(total_unpaid or 0),
            "pending_count": pending_count or 0
        }

    finally:
        session.close()


def get_payment_months():
    """Distinct 'payment_for_month' values already in use, for the
    Payments page month filter."""

    session = get_session()

    try:
        months = (
            session.query(distinct(Payment.payment_for_month))
            .filter(Payment.payment_for_month != None)
            .all()
        )
        return [m[0] for m in months]

    finally:
        session.close()