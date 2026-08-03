from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DECIMAL,
    Enum,
    Boolean,
    ForeignKey,
    TIMESTAMP
)
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy.sql import func

# AcademicYear model
class AcademicYear(Base):

    __tablename__ = "Academic_Years"

    academic_year_id = Column(Integer, primary_key=True, autoincrement=True)

    academic_year = Column(String(20), nullable=False, unique=True)

    start_date = Column(Date)

    end_date = Column(Date)

    status = Column(
        Enum("Current", "Completed", "Upcoming"),
        default="Upcoming"
    )

    students = relationship("Student", back_populates="academic_year")

    lessons = relationship("Lesson", back_populates="academic_year")

# Grade model
class Grade(Base):

    __tablename__ = "Grades"

    grade_id = Column(Integer, primary_key=True, autoincrement=True)

    grade_name = Column(String(50), nullable=False, unique=True)

    stage = Column(
        Enum("Primary", "Baccalaureate"),
        nullable=False
    )

    students = relationship("Student", back_populates="grade")

    lessons = relationship("Lesson", back_populates="grade")

# Student model
class Student(Base):

    __tablename__ = "Students"

    student_id = Column(Integer, primary_key=True, autoincrement=True)

    full_name = Column(String(100), nullable=False)

    grade_id = Column(Integer, ForeignKey("Grades.grade_id"))

    student_group = Column(String(20))

    phone = Column(String(20))

    parent_phone = Column(String(20))

    monthly_fee = Column(DECIMAL(10,2))

    join_date = Column(Date)

    is_active = Column(
        Boolean,
        default=True
    )

    academic_year_id = Column(
        Integer,
        ForeignKey("Academic_Years.academic_year_id")
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now()
    )

    grade = relationship("Grade", back_populates="students")

    academic_year = relationship(
        "AcademicYear",
        back_populates="students"
    )

    attendance = relationship(
        "Attendance",
        back_populates="student"
    )

    exams = relationship(
        "Exam",
        back_populates="student"
    )

    payments = relationship(
        "Payment",
        back_populates="student"
    )
    

# Lesson model
class Lesson(Base):

    __tablename__ = "Lessons"

    lesson_id = Column(Integer, primary_key=True, autoincrement=True)

    grade_id = Column(
        Integer,
        ForeignKey("Grades.grade_id"),
        nullable=False
    )

    lesson_number = Column(Integer, nullable=False)

    lesson_title = Column(String(200))

    lesson_date = Column(Date)

    academic_year_id = Column(
        Integer,
        ForeignKey("Academic_Years.academic_year_id"),
        nullable=False
    )

    grade = relationship(
        "Grade",
        back_populates="lessons"
    )

    academic_year = relationship(
        "AcademicYear",
        back_populates="lessons"
    )

    attendance = relationship(
        "Attendance",
        back_populates="lesson",
        cascade="all, delete-orphan"
    )

    exams = relationship(
        "Exam",
        back_populates="lesson",
        cascade="all, delete-orphan"
    )
    
# Attendance model
class Attendance(Base):

    __tablename__ = "Attendance"

    attendance_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    student_id = Column(
        Integer,
        ForeignKey("Students.student_id"),
        nullable=False
    )

    lesson_id = Column(
        Integer,
        ForeignKey("Lessons.lesson_id"),
        nullable=False
    )

    status = Column(
        Enum("Present", "Absent"),
        nullable=False
    )

    student = relationship(
        "Student",
        back_populates="attendance"
    )

    lesson = relationship(
        "Lesson",
        back_populates="attendance"
    )
    
# Exam model
class Exam(Base):

    __tablename__ = "Exams"

    exam_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    student_id = Column(
        Integer,
        ForeignKey("Students.student_id"),
        nullable=False
    )

    lesson_id = Column(
        Integer,
        ForeignKey("Lessons.lesson_id"),
        nullable=False
    )

    exam_name = Column(String(100))

    score = Column(DECIMAL(5,2))

    total_score = Column(DECIMAL(5,2))

    exam_date = Column(Date)

    student = relationship(
        "Student",
        back_populates="exams"
    )

    lesson = relationship(
        "Lesson",
        back_populates="exams"
    )
    
# Payment model
class Payment(Base):

    __tablename__ = "Payments"

    payment_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    student_id = Column(
        Integer,
        ForeignKey("Students.student_id"),
        nullable=False
    )

    payment_for_month = Column(String(20))

    amount = Column(DECIMAL(10,2))

    payment_date = Column(Date)

    status = Column(
        Enum("Paid", "Unpaid"),
        default="Unpaid"
    )

    student = relationship(
        "Student",
        back_populates="payments"
    )
    
