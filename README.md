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

Errors: 400 validation, 401 unauthenticated, 403 forbidden, 404 not found, 409 conflict (overlap, status or database constraint).

Other resources: `/api/employees/`, `/api/leave-types/`, `/api/leaves/` (with `approve/`, `reject/`, `cancel/` actions), `/api/leave-balances/?year=&employee=`, `/api/dashboard/`.

Business rules:
- Employee DELETE deactivates the employee. Hard delete is blocked when leave history exists.
- Leave types in use cannot be deleted (409). Empty allowance means unlimited (Unpaid Leave).
- Only approved leave is deducted from balances, grouped by the year the leave starts.
- Overlapping pending or approved applications for the same employee are rejected (409).
- Approval checks the balance (400 if insufficient). Only pending applications can be edited, approved ones cannot be deleted.

## Frontend setup (local)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api` to the backend on `127.0.0.1:8000`.

Production build: `npm run build`.

## Docker

Copy `.env.example` to `.env`, set `POSTGRES_PASSWORD` and `DJANGO_SECRET_KEY`, then:

```bash
docker compose up --build
```

The app is served at http://localhost:8080. nginx proxies `/api/` to the backend.
