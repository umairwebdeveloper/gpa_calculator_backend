from app import db, create_app
from seed import seed_enrollments, seed_students, seed_courses

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print("Migrating database...")
        db.create_all()
        print("Seeding data...")
        seed_students(20)
        seed_courses(10)
        seed_enrollments(30)
        print("Setup complete!")
