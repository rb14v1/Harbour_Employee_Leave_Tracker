# Infrastructure

Deployment and environment notes. Local development runs through `docker-compose.yml`.

- `db`: PostgreSQL 16 with a named volume (`pgdata`).
- `backend`: Django served by gunicorn on port 8000. Runs migrations and `create_admin` on start.
