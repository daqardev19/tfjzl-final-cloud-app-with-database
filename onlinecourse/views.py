import logging

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic

from .models import Choice, Course, Enrollment, Question, Submission

logger = logging.getLogger(__name__)


def registration_request(request):
    context = {}
    if request.method == "GET":
        return render(request, "onlinecourse/user_registration_bootstrap.html", context)

    username = request.POST.get("username", "").strip()
    password = request.POST.get("psw", "")
    first_name = request.POST.get("firstname", "")
    last_name = request.POST.get("lastname", "")
    if User.objects.filter(username=username).exists():
        context["message"] = "User already exists."
        return render(request, "onlinecourse/user_registration_bootstrap.html", context)

    user = User.objects.create_user(
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )
    login(request, user)
    return redirect("onlinecourse:index")


def login_request(request):
    context = {}
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username", ""),
            password=request.POST.get("psw", ""),
        )
        if user is not None:
            login(request, user)
            return redirect("onlinecourse:index")
        context["message"] = "Invalid username or password."
    return render(request, "onlinecourse/user_login_bootstrap.html", context)


def logout_request(request):
    logout(request)
    return redirect("onlinecourse:index")


def check_if_enrolled(user, course):
    return user.is_authenticated and Enrollment.objects.filter(user=user, course=course).exists()


class CourseListView(generic.ListView):
    template_name = "onlinecourse/course_list_bootstrap.html"
    context_object_name = "course_list"

    def get_queryset(self):
        courses = Course.objects.order_by("-total_enrollment")[:10]
        for course in courses:
            course.is_enrolled = check_if_enrolled(self.request.user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = "onlinecourse/course_details_bootstrap.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_enrolled"] = check_if_enrolled(self.request.user, self.object)
        return context


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if request.user.is_authenticated:
        _, created = Enrollment.objects.get_or_create(
            user=request.user, course=course, defaults={"mode": "honor"}
        )
        if created:
            course.total_enrollment += 1
            course.save(update_fields=["total_enrollment"])
    return HttpResponseRedirect(reverse("onlinecourse:course_details", args=(course.id,)))


def extract_answers(request):
    """Return submitted choice IDs from the per-question exam fields."""
    answers = []
    for key, value in request.POST.items():
        if key.startswith("choice_") and value.isdigit():
            answers.append(int(value))
    return answers


@login_required

def submit(request, course_id):
    """Save the learner's selected exam choices and show the result."""
    if request.method != "POST":
        return redirect("onlinecourse:course_details", pk=course_id)
    course = get_object_or_404(Course, pk=course_id)
    enrollment = get_object_or_404(Enrollment, user=request.user, course=course)
    submission = Submission.objects.create(enrollment=enrollment)

    selected_ids = extract_answers(request)
    valid_choices = Choice.objects.filter(
        id__in=selected_ids,
        question__lesson__course=course,
    )
    submission.choices.set(valid_choices)
    return redirect(
        "onlinecourse:show_exam_result",
        course_id=course.id,
        submission_id=submission.id,
    )


@login_required

def show_exam_result(request, course_id, submission_id):
    """Calculate and render the score and answer-by-answer feedback."""
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(
        Submission,
        pk=submission_id,
        enrollment__user=request.user,
        enrollment__course=course,
    )
    selected_choices = submission.choices.all()
    selected_by_question = {choice.question_id: choice for choice in selected_choices}
    questions = Question.objects.filter(lesson__course=course).select_related("lesson")

    exam_results = []
    total_grade = 0
    total_score = 0
    for question in questions:
        correct_choice = question.choices.filter(is_correct=True).first()
        selected_choice = selected_by_question.get(question.id)
        is_correct = bool(
            correct_choice and selected_choice and selected_choice.id == correct_choice.id
        )
        total_grade += question.grade
        if is_correct:
            total_score += question.grade
        exam_results.append(
            {
                "question": question,
                "selected_choice": selected_choice,
                "correct_choice": correct_choice,
                "is_correct": is_correct,
            }
        )

    grade = round((total_score / total_grade) * 100) if total_grade else 0
    return render(
        request,
        "onlinecourse/exam_result_bootstrap.html",
        {
            "course": course,
            "submission": submission,
            "exam_results": exam_results,
            "total_score": total_score,
            "total_grade": total_grade,
            "grade": grade,
            "passed": grade >= 70,
        },
    )
