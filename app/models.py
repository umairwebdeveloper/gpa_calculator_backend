from flask_sqlalchemy import SQLAlchemy

from . import db

class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    current_total_points_gpa = db.Column(db.Float, default=0.0)
    current_total_registered_credits_gpa = db.Column(db.Float, default=0.0)
    current_total_points_mgpa = db.Column(db.Float, default=0.0)
    current_total_registered_credits_mgpa = db.Column(db.Float, default=0.0)

    # Relationship with Enrollment
    enrollments = db.relationship("Enrollment", backref="student", lazy=True)

    def __repr__(self):
        return f"<Student {self.student_id}>"


class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    is_major = db.Column(db.Boolean, default=False)

    # Relationship with Enrollment
    enrollments = db.relationship("Enrollment", backref="course", lazy=True)

    def __repr__(self):
        return f"<Course {self.name}>"


class Enrollment(db.Model):
    __tablename__ = "enrollments"
    enrollment_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    grade = db.Column(db.String(2))
    is_repeated = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Enrollment Student: {self.student_id}, Course: {self.course_id}, Grade: {self.grade}>"
