# Project structure

```
app.py                 # Streamlit entry point and routing
config/                # App settings, constants, school labels
data/                  # Static JSON (career catalog, labour outlook)
docs/                  # Documentation
models/                # Trained ML artifacts (dropout pipeline, reference models)
scripts/               # Deployment helpers
src/
  auth/                # Login guards, password hashing, authentication
  db/                  # SQLAlchemy models, database session, seed data
  ml/                  # Dropout training and prediction
  psychometric/        # Interest assessment questions and scoring
  services/            # Business logic (students, users, dropout, OTP reset, …)
  utils/               # Shared helpers (admin scope, dates, file upload)
ui/
  components/          # Reusable UI (theme, tables, password reset, charts)
  pages/               # Streamlit page renderers by feature area
    admin_*            # Class admin operations
    student_*          # Student-facing pages
    superadmin_*       # Superadmin staff management
    user_*             # User creation and directory
    login.py           # Sign-in
.streamlit/            # Streamlit theme config
requirements.txt
runtime.txt
.python-version
```

## Routing

- `app.py` chooses sidebar pages from the signed-in role and loads the matching module under `ui/pages/`.
- Data access goes through `src/services/`; pages should not query the database directly except via `get_db_session()` wrappers in services.

## Admin data scope

- **Shared cohort:** class admins (and superadmins in Admin UI) with the same `assigned_grade` share students whose profile class matches that grade, when at least one active class admin exists for the grade.
- **Independent cohort:** superadmin in Admin UI for a grade with no class admin yet — only students they created are visible.
