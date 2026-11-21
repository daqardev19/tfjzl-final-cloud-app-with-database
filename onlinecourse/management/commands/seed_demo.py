from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from onlinecourse.models import Choice, Course, Enrollment, Instructor, Lesson, Question


DEMO_QUESTIONS = [
    ("Which language is Django written in?", 2, ["Python", "Ruby", "Java"], 0),
    ("Which command starts Django's development server?", 2, ["runserver", "startapp", "collectstatic"], 0),
    ("Which file defines Django models?", 2, ["models.py", "views.py", "admin.py"], 0),
    ("What does a Django URL pattern connect to?", 2, ["A view", "A database row", "A CSS file"], 0),
    ("Which template tag protects a POST form?", 2, ["csrf_token", "static", "extends"], 0),
]


class Command(BaseCommand):
    help = "Create a local course, exam, and student for assignment screenshots."

    def handle(self, *args, **options):
        instructor_user, _ = User.objects.get_or_create(
            username="course-instructor",
            defaults={"first_name": "Course", "last_name": "Instructor"},
        )
        instructor, _ = Instructor.objects.get_or_create(
            user=instructor_user,
            defaults={"full_time": True, "total_learners": 1},
        )
        course, _ = Course.objects.get_or_create(
            name="Django Assessment Course",
            defaults={
                "image": "course_images/django.png",
                "description": "A sample course with a five-question Django assessment.",
                "pub_date": "2025-01-01",
            },
        )
        course.instructors.add(instructor)
        lessons = [
            (1, "Django fundamentals", "Models describe data; views handle requests; templates render pages."),
            (2, "Building web applications", "Django routes requests to views and provides form security tools."),
        ]
        lesson_objects = []
        for order, title, content in lessons:
            lesson, _ = Lesson.objects.get_or_create(
                course=course,
                order=order,
                defaults={"title": title, "content": content},
            )
            lesson_objects.append(lesson)
        for index, (question_text, grade, choices, correct_index) in enumerate(DEMO_QUESTIONS):
            lesson = lesson_objects[0 if index < 3 else 1]
            question, _ = Question.objects.get_or_create(
                lesson=lesson,
                question_text=question_text,
                defaults={"grade": grade},
            )
            for choice_index, choice_text in enumerate(choices):
                Choice.objects.get_or_create(
                    question=question,
                    choice_text=choice_text,
                    defaults={"is_correct": choice_index == correct_index},
                )
        student, created = User.objects.get_or_create(
            username="examstudent",
            defaults={"first_name": "Exam", "last_name": "Student"},
        )
        if created:
            student.set_password("course1234")
            student.save(update_fields=["password"])
        Enrollment.objects.get_or_create(user=student, course=course, defaults={"mode": "honor"})
        self.stdout.write(self.style.SUCCESS("Demo course and assessment are ready."))
        self.stdout.write("Student login: examstudent / course1234")
