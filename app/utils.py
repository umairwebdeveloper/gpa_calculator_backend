from .models import db, Student, Course, Enrollment
from uuid import uuid4


def calculate_new_gpa(student_id, courses_data):
    """
    Calculate Semester GPA, Updated GPA, and MGPA based on user input.
    Fetch data from the database and handle new course creation.
    """
    # Fetch the student
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        raise ValueError("Student not found")
    print(student)

    # Grade scale mapping
    grade_scale = {
        "A": 4.0,
        "A-": 3.7,
        "B+": 3.3,
        "B": 3.0,
        "B-": 2.7,
        "C+": 2.3,
        "C": 2.0,
        "C-": 1.7,
        "D+": 1.3,
        "D": 1.0,
        "F": 0.0,
    }

    new_total_points = 0
    new_registered_credits = 0
    replacement_points = 0
    replacement_credits = 0
    major_points = 0
    major_credits = 0

    # Process each course
    for course_data in courses_data:
        course_id = course_data.get("course_id")
        course_name = course_data.get("course_name", f"Course-{course_id}")
        credits = course_data.get("credits", 3)  # Default to 3 credits
        is_major = course_data.get("is_major", False)
        new_grade = course_data["new_grade"]
        is_repeated = course_data.get("is_repeated", False)

        # Generate a new unique ID for the course
        new_course_id = str(uuid4())
        try:
            # If the course already exists, create a new course with a new ID
            course = Course(
                name=course_name,
                credits=credits,
                is_major=is_major,
            )
            # Add the new course to the database session
            db.session.add(course)

            # Commit the transaction to save the course
            db.session.commit()
        except Exception as e:
            print(e)

        print(12)

        # Handle repeated courses
        if is_repeated:
            # Fetch previous enrollment
            previous_enrollment = Enrollment.query.filter_by(
                student_id=student.id, course_id=course_id
            ).first()

            if previous_enrollment:
                previous_grade = previous_enrollment.grade
                previous_points = grade_scale.get(previous_grade, 0.0) * credits
                new_points = grade_scale.get(new_grade, 0.0) * credits

                if new_points > previous_points:
                    replacement_points += new_points - previous_points
                    replacement_credits += credits
                continue  # Skip further processing as repeated courses don't add new credits

        # Add new course points and credits
        new_points = grade_scale.get(new_grade, 0.0) * credits
        new_total_points += new_points
        new_registered_credits += credits

        # Add to major points if the course is a major
        if is_major:
            major_points += new_points
            major_credits += credits

        # Add or update the enrollment
        enrollment = Enrollment.query.filter_by(
            student_id=student.id, course_id=course.id
        ).first()
        if not enrollment:
            enrollment = Enrollment(
                student_id=student.id,
                course_id=course.id,
                grade=new_grade,
                is_repeated=is_repeated,
            )
            db.session.add(enrollment)
        else:
            enrollment.grade = new_grade
            enrollment.is_repeated = is_repeated
        db.session.commit()

    # Semester GPA
    semester_gpa = (
        new_total_points / new_registered_credits if new_registered_credits > 0 else 0
    )

    # Updated GPA
    updated_total_points_gpa = (
        student.current_total_points_gpa + new_total_points + replacement_points
    )
    updated_total_credits_gpa = (
        student.current_total_registered_credits_gpa + new_registered_credits
    )
    new_gpa = (
        updated_total_points_gpa / updated_total_credits_gpa
        if updated_total_credits_gpa > 0
        else 0
    )

    # Updated MGPA
    updated_total_points_mgpa = student.current_total_points_mgpa + major_points
    updated_total_credits_mgpa = (
        student.current_total_registered_credits_mgpa + major_credits
    )
    new_mgpa = (
        updated_total_points_mgpa / updated_total_credits_mgpa
        if updated_total_credits_mgpa > 0
        else 0
    )

    # Update student totals in the database
    student.current_total_points_gpa = updated_total_points_gpa
    student.current_total_registered_credits_gpa = updated_total_credits_gpa
    student.current_total_points_mgpa = updated_total_points_mgpa
    student.current_total_registered_credits_mgpa = updated_total_credits_mgpa
    db.session.commit()

    # Return results
    return {
        "semester_gpa": round(semester_gpa, 2),
        "new_gpa": round(new_gpa, 2),
        "new_mgpa": round(new_mgpa, 2),
    }
