# SSC Management System

A Streamlit app for **Indian school students in Class 6–10** (upper primary / secondary). Teachers and admins manage students, academic data, and dropout-risk insights; students complete profiles, interest assessments, and early career guidance.

## Features

- **Super Admin:** staff overview dashboard, user creation, and user management
- **Class-scoped staff:** admins and superadmins assigned to a class share the same student cohort when a class admin exists; otherwise the superadmin works in an independent workspace for that class
- **Students:** school profile, interest assessment (RIASEC-style), career ideas and roadmaps
- **Dropout risk:** train and run predictions on uploaded term marks and attendance
- **Change password:** staff and students update passwords from their dashboard using the current password

## Roles

| Role | Access |
|------|--------|
| **Super Admin** | Sign-in choice: **Admin UI** (class operations) or **User Management** (staff accounts) |
| **Admin** | Dashboard, students, uploads, dropout analysis — scoped to assigned class |
| **Student** | Profile, assessment, career ideas |

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

With a virtual environment:

```bash
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Access and passwords

Passwords are **not** listed in this repository. Staff and students can open **Change password** on their dashboard (current password + new password).

New staff accounts are created in **User Creation**; share the generated **username** and initial password through your secure onboarding process.

## Demo flow

1. **Super Admin** → **User Creation** → add admins per class
2. **Admin** → **Student Management** → create students → upload marks
3. **Dropout Analysis** → train model → run predictions
4. **Student** → complete profile → interest assessment → career ideas

Restart the app after upgrades; legacy demo student data is removed on startup.

## Project layout

See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for how the repository is organized.

## Deploy on Streamlit Community Cloud

1. Main file: `app.py`
2. Python version: `runtime.txt` in the repo root (`python-3.12`)
3. Dependencies: `requirements.txt` only (do not pin `pyarrow` separately)
4. After pushing, use **Manage app → Reboot app** if builds fail

## Deploy on Render

1. **Python 3.12** — use `.python-version` (`3.12.8`) or set `PYTHON_VERSION=3.12.8`
2. Build: `pip install -r requirements.txt`
3. Start: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
