from flask import Blueprint, request, jsonify
from .models import db, Student
from .utils import calculate_new_gpa, calculate_target_gpa
import random

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
                "user_id": student.user_id,
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
                        "is_repeated": enrollment.is_repeated,
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


@main_bp.route("/calculate_target_gpa", methods=["POST"])
def calculate_target_gpa_route():
    try:
        print(23)
        data = request.get_json(force=True)
        print(33)
        student_id = data.get("student_id")
        target_gpa = data.get("target_gpa")
        remaining_credits = data.get("remaining_credits")
        num_courses = data.get("num_courses")
        print(data)

        # Validate inputs
        if not all([student_id, target_gpa, remaining_credits, num_courses]):
            return jsonify({"error": "All fields are required"}), 400

        student = Student.query.filter_by(student_id=student_id).first()
        if not student:
            return jsonify({"error": "Student not found"}), 404

        # Calculate required grades
        result = calculate_target_gpa(
            student.current_total_points_gpa,
            student.current_total_registered_credits_gpa,
            target_gpa,
            remaining_credits,
            num_courses,
        )

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@main_bp.route("/register", methods=["POST"])
def register_student():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    user_id = data.get("user_id")
    name = data.get("name")

    if not user_id or not name:
        return jsonify({"error": "Missing required fields"}), 400

    # Check if the student already exists
    existing_student = Student.query.filter_by(user_id=user_id).first()
    if existing_student:
        return jsonify({"error": "Student already exists"}), 409

    # Create a new student
    new_student = Student(
        student_id=user_id,
        name=name,
        current_total_points_gpa=0.0,
        current_total_registered_credits_gpa=0.0,
        current_total_points_mgpa=0.0,
        current_total_registered_credits_mgpa=0.0,
        user_id=user_id,
    )

    try:
        db.session.add(new_student)
        db.session.commit()
        # Return the new student's information
        student_info = {
            "id": new_student.id,
            "student_id": new_student.student_id,
            "name": new_student.name,
            "current_total_points_gpa": new_student.current_total_points_gpa,
            "current_total_registered_credits_gpa": new_student.current_total_registered_credits_gpa,
            "current_total_points_mgpa": new_student.current_total_points_mgpa,
            "current_total_registered_credits_mgpa": new_student.current_total_registered_credits_mgpa,
            "user_id": new_student.user_id,
            "is_major": new_student.is_major,
        }
        return (
            jsonify(
                {
                    "message": "Student registered successfully!",
                    "student_info": student_info,
                }
            ),
            201,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main_bp.route("/is_registered/<string:student_id>", methods=["GET"])
def is_student_registered(student_id):
    if not student_id:
        return jsonify({"error": "Student ID is required"}), 400

    # Query the database for the student
    student = Student.query.filter_by(user_id=student_id).first()

    # Return the registration status and student info
    if student:
        student_info = {
            "id": student.id,
            "student_id": student.student_id,
            "name": student.name,
            "current_total_points_gpa": student.current_total_points_gpa,
            "current_total_registered_credits_gpa": student.current_total_registered_credits_gpa,
            "current_total_points_mgpa": student.current_total_points_mgpa,
            "current_total_registered_credits_mgpa": student.current_total_registered_credits_mgpa,
            "user_id": student.user_id,
            "is_major": student.is_major,
            "courses": [],
        }
        for enrollment in student.enrollments:
            course = enrollment.course
            student_info["courses"].append(
                {
                    "course_id": course.id,
                    "course_name": course.name,
                    "credits": course.credits,
                    "is_major": course.is_major,
                    "grade": enrollment.grade,
                    "is_repeated": enrollment.is_repeated,
                }
            )

        return jsonify({"is_registered": True, "student_info": student_info}), 200
    else:
        return jsonify({"is_registered": False}), 200


@main_bp.route("/update_field_of_study", methods=["POST"])
def update_field_of_study():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    user_id = data.get("user_id")
    student_id = data.get("studentId")
    is_major = data.get("isMajor")
    name = data.get("name")
    current_total_points_gpa = data.get("currentTotalPointsGpa")
    current_total_registered_credits_gpa = data.get("currentTotalRegisteredCreditsGpa")
    current_total_points_mgpa = data.get("currentTotalPointsMgpa")
    current_total_registered_credits_mgpa = data.get(
        "currentTotalRegisteredCreditsMgpa"
    )

    # Validate required fields
    if not user_id or not student_id:
        return (
            jsonify({"error": "Missing required fields: user_id and student_id"}),
            400,
        )

    # Find the student
    student = Student.query.filter_by(user_id=user_id).first()
    if not student:
        return jsonify({"error": "Student not found"}), 404

    # Update fields
    student.student_id = student_id
    student.is_major = is_major
    student.name = name
    try:
        if current_total_points_gpa is not None:
            student.current_total_points_gpa = float(current_total_points_gpa)
        if current_total_registered_credits_gpa is not None:
            student.current_total_registered_credits_gpa = float(
                current_total_registered_credits_gpa
            )
        if current_total_points_mgpa is not None:
            student.current_total_points_mgpa = float(current_total_points_mgpa)
        if current_total_registered_credits_mgpa is not None:
            student.current_total_registered_credits_mgpa = float(
                current_total_registered_credits_mgpa
            )
    except ValueError:
        return jsonify({"error": "Invalid numeric values for GPA or credits"}), 400

    # Commit the changes
    try:
        db.session.commit()
        return jsonify({"message": "Student information updated successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database commit failed: {str(e)}"}), 500
