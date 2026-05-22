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
streamlit run streamlit_app.py
```

Use the project virtual environment if you have one:

```bash
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Demo credentials

- Admin: `admin` / `Admin@123`
- Students: created by the admin under **Student Management** (no default demo student account)

## Demo flow

1. Admin → create students (Class 6–10) → download CSV template → upload term marks & attendance
2. Dropout Analysis → train model → run predictions
3. Student → complete profile → interest assessment → career ideas page

**Note:** Restart the app after upgrading; legacy demo data for removed students is cleaned up automatically on startup.

## Deploy on Streamlit Community Cloud

1. Main file: `streamlit_app.py`
2. Python version: `runtime.txt` must be in the repo root (`python-3.12`). Without it, Cloud may use Python 3.14 and fail to build `pandas` / `pyarrow`.
3. Dependencies: only `requirements.txt` (do not pin `pyarrow` or other Streamlit-managed packages separately).
4. After pushing, open **Manage app → Reboot app** if dependency errors persist.

## Deploy on Render

1. **Python 3.12 is required.** Render ignores `runtime.txt`; use the repo root `.python-version` (`3.12.8`) or set environment variable `PYTHON_VERSION` to `3.12.8` in the Render dashboard.
2. Build command: `pip install -r requirements.txt`
3. Start command: `streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`
4. If the build still picks Python 3.14, clear the build cache and redeploy after pushing `.python-version`.
