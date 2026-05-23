# SSC Management System

A Streamlit app for **Indian school students in Class 6–10** (upper primary / secondary). Teachers and admins manage students, academic data, and dropout-risk insights; students complete profiles, interest assessments, and early career guidance.

## Features

- **Super Admin:** staff account management (create/edit/deactivate admins and superadmins)
- **Class-scoped admins:** dashboards and student tools default to their assigned class (6–10)
- **Students:** school profile, interest assessment (RIASEC-style), career ideas and roadmaps
- **Dropout risk:** train and run predictions on uploaded term marks and attendance
- **Academic data:** CSV bulk upload and per-student manual entry

## Roles

| Role | Access |
|------|--------|
| **Super Admin** | Sign-in choice: **Admin UI** (same as class admin) or **User Management** (staff accounts) |
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

## Demo credentials

| Account | Username | Password | Notes |
|---------|----------|----------|--------|
| Super Admin | `superadmin` | `superadmin@123` | Choose **Admin UI** or **User Management** at sign-in |
| Class admin (demo) | `admin` | `Admin@123` | Defaults to **Class 6** |
| New staff | *(auto-generated)* | `anasha@123` | Created in User Management; username like `anasha_admin6` for Ananya Sharma, Class 6 |

Students are created by admins under **Student Management** (no default student login).

### Staff username format

- **Admin:** first 3 letters of first name + first 3 of last name + `_admin` + class number — e.g. `anasha_admin6`
- **Super Admin:** same prefix + `_superadmin` — e.g. `anasha_superadmin`
- **Password:** first 3 letters of first name + first 3 of last name + `@123` — e.g. `anasha@123`

## Demo flow

1. **Super Admin** → User Management → add admins for each class
2. **Admin** → Student Management → create Class 6–10 students → download CSV template → upload marks
3. **Dropout Analysis** → train model → run predictions
4. **Student** → complete profile → interest assessment → career ideas

Restart the app after upgrades; legacy demo student data is removed on startup.

## Deploy on Streamlit Community Cloud

1. Main file: `app.py`
2. Python version: `runtime.txt` in the repo root (`python-3.12`)
3. Dependencies: `requirements.txt` only (do not pin `pyarrow` separately)
4. After pushing, use **Manage app → Reboot app** if builds fail

## Deploy on Render

1. **Python 3.12** — use `.python-version` (`3.12.8`) or set `PYTHON_VERSION=3.12.8`
2. Build: `pip install -r requirements.txt`
3. Start: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
