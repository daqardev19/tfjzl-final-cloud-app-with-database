from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Choice, Course, Enrollment, Instructor, Lesson, Question, Submission


class AssessmentFlowTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username="student", password="test-pass-123")
        instructor_user = User.objects.create_user(username="instructor", password="test-pass-123")
        instructor = Instructor.objects.create(user=instructor_user, total_learners=1)
        self.course = Course.objects.create(
            name="Django Basics",
            description="Learn Django",
            image="course_images/django.png",
        )
        self.course.instructors.add(instructor)
        self.lesson = Lesson.objects.create(
            course=self.course, title="Models", order=0, content="Models store structured data."
        )
        self.question = Question.objects.create(
            lesson=self.lesson,
            question_text="Which file contains Django models?",
            grade=10,
        )
        self.correct = Choice.objects.create(
            question=self.question, choice_text="models.py", is_correct=True
        )
        self.incorrect = Choice.objects.create(
            question=self.question, choice_text="views.py", is_correct=False
        )
        self.enrollment = Enrollment.objects.create(
            user=self.student, course=self.course, mode="honor"
        )

    def test_course_detail_shows_lessons_and_assessment(self):
        self.client.force_login(self.student)
        response = self.client.get(
            reverse("onlinecourse:course_details", args=(self.course.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Django Basics")
        self.assertContains(response, "Models")
        self.assertContains(response, "Which file contains Django models?")

    def test_correct_answer_passes_and_shows_result(self):
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("onlinecourse:submit", args=(self.course.id,)),
            {f"choice_{self.question.id}": str(self.correct.id)},
        )
        submission = Submission.objects.get(enrollment=self.enrollment)
        self.assertRedirects(
            response,
            reverse(
                "onlinecourse:show_exam_result",
                args=(self.course.id, submission.id),
            ),
        )
        result = self.client.get(response.url)
        self.assertContains(result, "Congratulations!")
        self.assertContains(result, "10 / 10 (100%)")

    def test_incorrect_answer_shows_failed_result(self):
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("onlinecourse:submit", args=(self.course.id,)),
            {f"choice_{self.question.id}": str(self.incorrect.id)},
        )
        result = self.client.get(response.url)
        self.assertContains(result, "Keep learning and try again")
        self.assertContains(result, "0 / 10 (0%)")

    def test_anonymous_exam_submission_redirects_to_login(self):
        response = self.client.post(
            reverse("onlinecourse:submit", args=(self.course.id,)), {}
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)
