# Final Project: Online Course Assessment

This project adds a graded assessment to the IBM Online Course Django application. Students can review course lessons, submit one answer per question, and see their score and answer-by-answer feedback. The admin site supports editing lessons, questions, and choices inline.

## Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py manage.py migrate
py manage.py seed_demo
py manage.py createsuperuser
py manage.py runserver
```

Open `http://127.0.0.1:8000/admin/` to manage course content and `http://127.0.0.1:8000/onlinecourse/` to view courses. The demo command creates an enrolled student account: `examstudent` / `course1234`.

## Assessment implementation

- `onlinecourse/models.py`: `Question`, `Choice`, and `Submission` models.
- `onlinecourse/admin.py`: question and choice inlines, question administration, and lesson administration.
- `onlinecourse/templates/onlinecourse/course_details_bootstrap.html`: course name, lessons, and assessment form.
- `onlinecourse/views.py` and `onlinecourse/urls.py`: submission, scoring, result view, and routes.

## Screenshots

- `screenshots/03-admin-site.png`: Django admin showing Authentication and Authorization and OnlineCourse.
- `screenshots/07-final.png`: successful five-question attempt with score and answer feedback.

## Verification

```powershell
py manage.py check
py manage.py test
```
