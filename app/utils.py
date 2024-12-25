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


def calculate_new_gpa(student_id, courses_data):
    """
    Calculate Semester GPA, Updated GPA, and MGPA based on user input.
    Fetch data from the database and handle new course creation.
    Ensure GPA values do not exceed 4.0.
    """
    # Fetch the student
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        raise ValueError("Student not found")

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
            # Create a new course
            course = Course(
                name=course_name,
                credits=credits,
                is_major=is_major,
            )
            db.session.add(course)
            db.session.commit()
        except Exception as e:
            print(e)

        # Handle repeated courses
        if is_repeated:
            previous_enrollment = Enrollment.query.filter_by(
                student_id=student.id, course_id=course_id
            ).first()

            if previous_enrollment:
                previous_grade = previous_enrollment.grade
                previous_points = GRADE_SCALE.get(previous_grade, 0.0) * credits
                new_points = GRADE_SCALE.get(new_grade, 0.0) * credits

                if new_points > previous_points:
                    replacement_points += new_points - previous_points
                    replacement_credits += credits
                continue

        # Add new course points and credits
        new_points = GRADE_SCALE.get(new_grade, 0.0) * credits
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
    semester_gpa = min(
        new_total_points / new_registered_credits if new_registered_credits > 0 else 0,
        4.0,
    )
    
    print('New total points', new_total_points,new_registered_credits)

    # Updated GPA
    total_gpa_points = (
        (
            student.current_total_points_gpa
            * student.current_total_registered_credits_gpa
        )
        + new_total_points
        + replacement_points
    )
    total_gpa_credits = (
        student.current_total_registered_credits_gpa + new_registered_credits
    )
    new_gpa = min(
        (total_gpa_points / total_gpa_credits) if total_gpa_credits > 0 else 0,
        4.0,
    )

    # Updated MGPA
    total_mgpa_points = (
        student.current_total_points_mgpa * student.current_total_registered_credits_gpa
    ) + major_points
    total_mgpa_credits = student.current_total_registered_credits_gpa + major_credits
    new_mgpa = min(
        (total_mgpa_points / total_mgpa_credits) if total_mgpa_credits > 0 else 0,
        4.0,
    )

    # Update student totals in the database
    # student.current_total_points_gpa = new_gpa
    # student.current_total_registered_credits_gpa = total_gpa_credits
    # student.current_total_points_mgpa = new_mgpa
    # db.session.commit()

    # Return results
    return {
        "semester_gpa": round(semester_gpa, 2),
        "new_gpa": round(new_gpa, 2),
        "new_mgpa": round(new_mgpa, 2),
    }


def calculate_target_gpa(
    current_points,
    current_credits,
    target_gpa,
    remaining_credits,
    num_courses,
    num_solutions=3,
):
    """
    Generate multiple random solutions for grades to achieve the target GPA.

    :param current_points: Current total GPA points.
    :param current_credits: Current total registered GPA credits.
    :param target_gpa: Target GPA the student wants to achieve.
    :param remaining_credits: Total credits for the remaining courses.
    :param num_courses: Number of remaining courses.
    :param num_solutions: Number of random solutions to generate.
    :return: A dictionary containing random grade solutions.
    """
    if target_gpa < 0 or target_gpa > 4.0:
        return {"error": "Invalid target GPA. It must be between 0.0 and 4.0."}

    if remaining_credits <= 0 or num_courses <= 0:
        return {"error": "Remaining credits and number of courses must be positive."}

    if remaining_credits < num_courses:
        return {"error": "Remaining credits cannot be less than the number of courses."}

    required_points = (
        target_gpa * (current_credits + remaining_credits) - current_points
    )

    if required_points <= 0:
        return {
            "error": "Target GPA is already achieved or no additional points are needed."
        }

    if required_points > remaining_credits * 4.0:
        return {
            "error": "Target GPA is unachievable with the given remaining credits and courses."
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
        last_grade = min(
            (
                grade
                for grade, points in GRADE_SCALE.items()
                if points * credits_per_course >= remaining_points
            ),
            key=lambda g: abs(GRADE_SCALE[g] * credits_per_course - remaining_points),
            default="A+",
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
