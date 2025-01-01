from flask_admin.contrib.sqla import ModelView
from wtforms import SelectField
from wtforms_sqlalchemy.fields import QuerySelectField
from . import db
from . import admin


class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    current_total_points_gpa = db.Column(db.Float, default=0.0)
    current_total_registered_credits_gpa = db.Column(db.Float, default=0.0)
    current_total_points_mgpa = db.Column(db.Float, default=0.0)
    current_total_registered_credits_mgpa = db.Column(db.Float, default=0.0)
    user_id = db.Column(db.String(1000), nullable=True)
    is_major = db.Column(db.String(50), nullable=True)

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


class EnrollmentAdmin(ModelView):
    form_columns = ["student_id", "course_id", "grade", "is_repeated"]
    column_list = ["enrollment_id", "student_id", "course_id", "grade", "is_repeated"]
    column_searchable_list = ["student_id", "course_id", "grade"]


class StudentAdmin(ModelView):
    form_columns = [
        "student_id",
        "name",
        "current_total_points_gpa",
        "current_total_registered_credits_gpa",
        "current_total_points_mgpa",
        "user_id",
        "is_major",
    ]
    column_list = [
        "id",
        "student_id",
        "name",
        "current_total_points_gpa",
        "current_total_registered_credits_gpa",
        "current_total_points_mgpa",
        "user_id",
        "is_major",
    ]

    # Enable search functionality for these columns
    column_searchable_list = [
        "student_id",
        "name",
        "user_id",
    ]

    column_labels = {
        "id": "ID",
        "student_id": "Student ID",
        "name": "Full Name",
        "current_total_points_gpa": "GPA",
        "current_total_registered_credits_gpa": "Total Credits",
        "current_total_points_mgpa": "MGPA",
        "user_id": "User Identifier",
        "is_major": "Major",
    }

    # Change form input labels
    form_labels = {
        "student_id": "Student Identifier",
        "name": "Unique Student Name",
        "current_total_points_gpa": "GPA",
        "current_total_registered_credits_gpa": "Total Credits",
        "current_total_points_mgpa": "MGPA",
        "user_id": "Unique User ID",
        "is_major": "Major Status",
    }

    form_overrides = {
        "is_major": SelectField,
    }

    # Define choices for 'is_major' dropdown
    form_args = {
        "is_major": {
            "choices": [
                ("Accounting", "Accounting"),
                ("MIS", "MIS"),
                ("Economic", "Economic"),
                ("Finance", "Finance"),
                ("Marketing", "Marketing"),
                ("Management", "Management"),
                ("Public Administration", "Public Administration"),
                ("Operation Management", "Operation Management"),
            ]
        }
    }


class CourseAdmin(ModelView):
    form_columns = ["name", "credits"]
    column_list = ["id", "name", "credits"]

    # Enable search functionality for these columns
    column_searchable_list = ["name"]


admin.add_view(StudentAdmin(Student, db.session))
admin.add_view(CourseAdmin(Course, db.session))
admin.add_view(EnrollmentAdmin(Enrollment, db.session))
