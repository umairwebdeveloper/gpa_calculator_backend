from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

# Initialize Flask app and extensions
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SECRET_KEY"] = "your_secret_key"
db = SQLAlchemy(app)


# Define models (as given above)
class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    # Relationship with Enrollment


class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    credits = db.Column(db.Integer, nullable=False)

    # Relationship with Enrollment

    def __repr__(self):
        return f"<Course {self.name}>"


class Enrollment(db.Model):
    __tablename__ = "enrollments"
    enrollment_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    grade = db.Column(db.String(2))

    def __repr__(self):
        return f"<Enrollment Student: {self.student_id}, Course: {self.course_id}, Grade: {self.grade}>"


# Initialize Flask-Admin
admin = Admin(app, name="Admin Panel", template_mode="bootstrap4")


# Register models with Flask-Admin


admin.add_view(ModelView(Student, db.session))
admin.add_view(ModelView(Course, db.session))
admin.add_view(ModelView(Enrollment, db.session))

if __name__ == "__main__":
    # Create tables
    with app.app_context():
        db.create_all()

    # Run the app
    app.run(debug=True)
