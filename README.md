# Employee Leave Tracker

Single-administrator web app for a small organisation to manage employees, leave types, leave applications and balances.

## Stack

- Backend: Python, Django, Django REST Framework, JWT (`djangorestframework-simplejwt`), PostgreSQL
- Frontend: React, Vite, TypeScript, CSS (in progress)

## Layout

```
backend/    Django project (config/, common/, apps/accounts|employees|leaves|dashboard)
frontend/   React + Vite app (in progress)
infra/      Deployment notes
.github/    CI workflows
```

## Backend setup (local)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Set environment variables (see `backend/.env.example`), then:

```bash
python manage.py migrate
python manage.py create_admin   # reads DJANGO_ADMIN_* variables
python manage.py runserver
```

Run tests:

```bash
python manage.py test
```

## API

All routes are under `/api/`. Health check: `GET /api/health/`.

| Method | Route | Purpose |
|---|---|---|
| POST | `/api/auth/login/` | Obtain access and refresh tokens |
| POST | `/api/auth/refresh/` | Rotate refresh token |
| POST | `/api/auth/logout/` | Revoke refresh token |
| GET | `/api/auth/me/` | Current admin |

Errors: 400 validation, 401 unauthenticated, 403 forbidden, 404 not found, 409 conflict (database constraint).
