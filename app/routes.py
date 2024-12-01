from flask import Blueprint, request, jsonify
from .models import db, Student
from .utils import calculate_new_gpa

main_bp = Blueprint("main", __name__)


@main_bp.route("/students", methods=["GET"])
def get_all_students():
    try:
        # Query all students from the database
        students = Student.query.all()

        # Serialize the student data into a JSON-friendly format
        students_data = [
            {
                "id": student.student_id,
                "name": student.name,
                "current_total_points_gpa": student.current_total_points_gpa,
                "current_total_registered_credits_gpa": student.current_total_registered_credits_gpa,
                "current_total_points_mgpa": student.current_total_points_mgpa,
                "current_total_registered_credits_mgpa": student.current_total_registered_credits_mgpa,
            }
            for student in students
        ]

        # Return the serialized data
        return jsonify(students_data), 200
    except Exception as e:
        # Handle unexpected errors
        return jsonify({"error": str(e)}), 500


@main_bp.route("/students_with_courses", methods=["GET"])
def get_students_with_courses():
    try:
        # Query all students
        students = Student.query.all()

        # Serialize the data
        students_with_courses = []
        for student in students:
            student_data = {
                "id": student.student_id,
                "name": student.name,
                "current_total_points_gpa": student.current_total_points_gpa,
                "current_total_registered_credits_gpa": student.current_total_registered_credits_gpa,
                "current_total_points_mgpa": student.current_total_points_mgpa,
                "current_total_registered_credits_mgpa": student.current_total_registered_credits_mgpa,
                "courses": [],
            }

            # Fetch enrolled courses for this student
            for enrollment in student.enrollments:
                course = enrollment.course
                student_data["courses"].append(
                    {
                        "course_id": course.id,
                        "course_name": course.name,
                        "credits": course.credits,
                        "is_major": course.is_major,
                        "grade": enrollment.grade,
                        "is_repeated": enrollment.is_repeated
                    }
                )

            students_with_courses.append(student_data)

        # Return serialized data
        return jsonify(students_with_courses), 200
    except Exception as e:
        # Handle unexpected errors
        return jsonify({"error": str(e)}), 500
    

@main_bp.route("/calculate_gpa", methods=["POST"])
def calculate_gpa():
    try:
        # Parse JSON request body
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON or missing Content-Type header"}), 415

    # Validate required keys in the payload
    if "student_id" not in data or "courses" not in data:
        return (
            jsonify(
                {"error": "Invalid payload: 'student_id' and 'courses' are required"}
            ),
            400,
        )

    student_id = data["student_id"]
    courses_data = data["courses"]

    # Check if the student exists
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return jsonify({"error": f"Student with ID {student_id} not found"}), 404

    # Call the GPA calculation function with database-integrated logic
    try:
        result = calculate_new_gpa(student_id, courses_data)
        return jsonify(result), 200
    except ValueError as ve:
        # Handle specific errors raised in calculate_new_gpa
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        # Handle unexpected errors
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
