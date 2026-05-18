# Class 6–10 Student Success & Career Guidance

A Streamlit app for **Indian school students in Class 6–10** (upper primary / secondary). Class 11–12 stream and board-exam guidance is planned for a future release.

## Features

- **Teachers / admins:** manage students, upload term marks & attendance, run dropout-risk predictions
- **Students:** school profile, interest assessment (RIASEC-style), early career ideas and roadmaps

## Implemented

- Authentication (admin + student)
- School profiles (class, school name, interests)
- Academic records (percentages, attendance, participation)
- Dropout risk model (baseline; retrain after updates)
- Interest assessment (section-by-section)
- Dashboards and demo career ideas

## In progress

- Personalized career recommendation engine
- Intervention logging

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Use the project virtual environment if you have one:

```bash
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Demo credentials

- Admin: `admin` / `Admin@123`
- Student: `student1` / `Student@123`

## Demo flow

1. Admin → create students (Class 6–10) → download CSV template → upload term marks & attendance
2. Dropout Analysis → train model → run predictions
3. Student → complete profile → interest assessment → career ideas page

**Note:** If you already ran the app with older seed data, delete `data/app.db` once to load the Class 6–10 demo student, or create a fresh student account.
