from app.models import db, Student, Course, Enrollment
import random
from faker import Faker
import random

fake = Faker()


def seed_students(num_students=10):
    for _ in range(num_students):
        student = Student(
            student_id=fake.unique.random_number(digits=9),
            name=fake.name(),
            current_total_points_gpa=round(random.uniform(50, 300), 2),
            current_total_registered_credits_gpa=random.randint(10, 150),
            current_total_points_mgpa=round(random.uniform(10, 50), 2),
            current_total_registered_credits_mgpa=random.randint(5, 50),
        )
        db.session.add(student)
    db.session.commit()
    print(f"Seeded {num_students} students!")


def seed_courses(num_courses=10):
    for _ in range(num_courses):
        course = Course(
            name=fake.word().capitalize(),
            credits=random.choice([1, 2, 3, 4]),
            is_major=random.choice([True, False]),
        )
        db.session.add(course)
    db.session.commit()
    print(f"Seeded {num_courses} courses!")


def seed_enrollments(num_enrollments=30):
    students = Student.query.all()
    courses = Course.query.all()

    for _ in range(num_enrollments):
        enrollment = Enrollment(
            student_id=random.choice(students).id,
            course_id=random.choice(courses).id,
            grade=random.choice(
                ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F"]
            ),
            is_repeated=random.choice([True, False]),
        )
        db.session.add(enrollment)
    db.session.commit()
    print(f"Seeded {num_enrollments} enrollments!")



