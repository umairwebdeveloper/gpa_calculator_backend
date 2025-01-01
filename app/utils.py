from .models import db, Student, Course, Enrollment
from uuid import uuid4
import random

# Grade scale mapping
GRADE_SCALE = {
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


def calculate_new_gpa(student_id=None, courses_data=[], custom_data=None):
    """
    Calculate Semester GPA, Updated GPA, and MGPA based on user input.
    Supports calculations with or without student_id. If student_id is None,
    custom values must be passed in custom_data.

    Parameters:
        student_id (int or None): ID of the student. Pass None to use custom data.
        courses_data (list): List of dictionaries containing course data.
        custom_data (dict or None): Custom data for GPA calculation if student_id is None. Must include:
            - current_total_points_gpa
            - current_total_registered_credits_gpa
            - current_total_points_mgpa
            - current_total_registered_credits_mgpa

    Returns:
        dict: Dictionary with keys 'semester_gpa', 'new_gpa', and 'new_mgpa'.
    """
    if student_id:
        # Fetch the student
        student = Student.query.filter_by(student_id=student_id).first()
        if not student:
            raise ValueError("Student not found")

        current_total_points_gpa = student.current_total_points_gpa
        current_total_registered_credits_gpa = (
            student.current_total_registered_credits_gpa
        )
        current_total_points_mgpa = student.current_total_points_mgpa
        current_total_registered_credits_mgpa = (
            student.current_total_registered_credits_gpa
        )
    else:
        if not custom_data:
            raise ValueError("Custom data is required when student_id is None")

        # Extract custom data fields
        current_total_points_gpa = custom_data.get("current_total_points_gpa", 0)
        current_total_registered_credits_gpa = custom_data.get(
            "current_total_registered_credits_gpa", 0
        )
        current_total_points_mgpa = custom_data.get("current_total_points_mgpa", 0)
        current_total_registered_credits_mgpa = custom_data.get(
            "current_total_registered_credits_gpa", 0
        )

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

        new_points = GRADE_SCALE.get(new_grade, 0.0) * credits

        # Handle repeated courses
        if is_repeated and student_id:
            previous_enrollment = Enrollment.query.filter_by(
                student_id=student.id, course_id=course_id
            ).first()

            if previous_enrollment:
                previous_grade = previous_enrollment.grade
                previous_points = GRADE_SCALE.get(previous_grade, 0.0) * credits

                if new_points > previous_points:
                    replacement_points += new_points - previous_points
                    replacement_credits += credits
                continue

        # Add new course points and credits
        new_total_points += new_points
        new_registered_credits += credits

        # Add to major points if the course is a major
        if is_major:
            major_points += new_points
            major_credits += credits

        # Add or update the enrollment (only for student_id)
        if student_id:
            course = Course.query.filter_by(name=course_name).first()
            if not course:
                course = Course(name=course_name, credits=credits, is_major=is_major)
                db.session.add(course)
                db.session.commit()

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
    semester_gpa = round(
        min(
            (
                new_total_points / new_registered_credits
                if new_registered_credits > 0
                else 0
            ),
            4.0,
        ),
        2,
    )

    # Updated GPA
    total_gpa_points = (
        (current_total_points_gpa * current_total_registered_credits_gpa)
        + new_total_points
        + replacement_points
    )
    total_gpa_credits = current_total_registered_credits_gpa + new_registered_credits
    new_gpa = round(
        min(
            (total_gpa_points / total_gpa_credits) if total_gpa_credits > 0 else 0, 4.0
        ),
        2,
    )

    # Updated MGPA
    total_mgpa_points = (
        current_total_points_mgpa * current_total_registered_credits_mgpa
    ) + major_points
    total_mgpa_credits = current_total_registered_credits_mgpa + major_credits
    new_mgpa = round(
        min(
            (total_mgpa_points / total_mgpa_credits) if total_mgpa_credits > 0 else 0,
            4.0,
        ),
        2,
    )

    # Update student totals in the database (only for student_id)
    if student_id:
        student.current_total_points_gpa = new_gpa
        student.current_total_registered_credits_gpa = total_gpa_credits
        student.current_total_points_mgpa = new_mgpa
        db.session.commit()

    # Return results
    return {
        "semester_gpa": semester_gpa,
        "new_gpa": new_gpa,
        "new_mgpa": new_mgpa,
    }


def calculate_target_gpa(
    gpa,
    current_credits,
    target_gpa,
    remaining_credits,
    num_courses,
    num_solutions=3,
):
    """
    Generate multiple random solutions for grades to achieve the target GPA.

    :param gpa: Current GPA (0.0 to 4.0).
    :param current_credits: Total credits the student has completed.
    :param target_gpa: Target GPA the student wants to achieve.
    :param remaining_credits: Total credits for the remaining courses.
    :param num_courses: Number of remaining courses.
    :param num_solutions: Number of random solutions to generate.
    :return: A dictionary containing random grade solutions or an error message.
    """
    # Validation for input ranges
    if gpa < 0 or gpa > 4.0:
        return {"error": "Invalid GPA. It must be between 0.0 and 4.0."}

    if target_gpa < 0 or target_gpa > 4.0:
        return {"error": "Invalid target GPA. It must be between 0.0 and 4.0."}

    if remaining_credits <= 0 or num_courses <= 0:
        return {"error": "Remaining credits and number of courses must be positive."}

    if remaining_credits < num_courses:
        return {"error": "Remaining credits cannot be less than the number of courses."}

    # Calculate current points from GPA
    current_points = gpa * current_credits

    # Calculate required points to achieve the target GPA
    required_points = (
        target_gpa * (current_credits + remaining_credits) - current_points
    )

    # Check if the target GPA is achievable
    max_achievable_points = remaining_credits * 4.0
    if required_points > max_achievable_points:
        return {
            "error": (
                f"Target GPA {target_gpa} is unachievable. "
                f"Maximum achievable GPA with {remaining_credits} credits is "
                f"{round((current_points + max_achievable_points) / (current_credits + remaining_credits), 2)}."
            )
        }

    credits_per_course = remaining_credits / num_courses
    solutions = []

    for _ in range(num_solutions):
        total_points_generated = 0
        selected_grades = []

        # Generate grades for all but the last course
        for _ in range(num_courses - 1):
            grade = random.choice(list(GRADE_SCALE.keys()))
            grade_points = GRADE_SCALE[grade] * credits_per_course
            selected_grades.append(grade)
            total_points_generated += grade_points

        # Adjust the last course grade to balance the total points
        remaining_points = required_points - total_points_generated
        if remaining_points < 0:
            last_grade = "F"
        else:
            last_grade = min(
                (
                    grade
                    for grade, points in GRADE_SCALE.items()
                    if points * credits_per_course >= remaining_points
                ),
                key=lambda g: abs(
                    GRADE_SCALE[g] * credits_per_course - remaining_points
                ),
                default="A",
            )
        selected_grades.append(last_grade)

        # Add the formatted solution to the results
        grade_counts = {}
        for grade in selected_grades:
            grade_counts[grade] = grade_counts.get(grade, 0) + 1

        formatted_solution = " & ".join(
            f"{count}{grade}" for grade, count in grade_counts.items()
        )
        solutions.append(f"({formatted_solution})")

    return {
        "target_gpa": round(target_gpa, 2),
        "required_points": round(required_points, 2),
        "random_solutions": " OR ".join(solutions),
    }
