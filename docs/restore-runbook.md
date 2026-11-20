# Database restore runbook

Applies to the production PostgreSQL server `psql-employeeleavetrack-44834`
(Azure Database for PostgreSQL flexible server, defined in `infra/terraform/main.tf`).

## Backup configuration

| Setting | Value |
|---|---|
| Automated backups | Enabled (daily full snapshot plus continuous WAL archiving) |
| Retention | 35 days (`backup_retention_days = 35`) |
| Backup storage | Geo-redundant (`geo_redundant_backup_enabled = true`), replicated to the Azure paired region |
| Point-in-time recovery | Any point within the last 35 days |

Check the live settings:

```bash
az postgres flexible-server show \
  --resource-group <resource-group> \
  --name psql-employeeleavetrack-44834 \
  --query "{retention:backup.backupRetentionDays, geo:backup.geoRedundantBackup, earliest:backup.earliestRestoreDate}"
```

## Restore procedure

A restore always creates a **new** server. The original server is left as it is.

### 1. Point-in-time restore (same region)

Use this for data loss or corruption, such as a bad migration or an accidental delete.

```bash
az postgres flexible-server restore \
  --resource-group <resource-group> \
  --name psql-employeeleavetrack-44834-restore \
  --source-server psql-employeeleavetrack-44834 \
  --restore-time "2026-01-01T10:00:00Z"   # UTC time just before the incident
```

### 2. Geo-restore (paired region)

Use this when the primary region is unavailable.

```bash
az postgres flexible-server geo-restore \
  --resource-group <resource-group> \
  --name psql-employeeleavetrack-44834-geo \
  --source-server psql-employeeleavetrack-44834 \
  --location <paired-region>
```

### 3. Verify the restored server

1. Connect with `psql "host=<restored-fqdn> dbname=leave_tracker user=<admin> sslmode=require"`.
2. Check the core tables and row counts against the expected state:
   ```sql
   SELECT count(*) FROM django_migrations;
   \dt
   ```
3. Run `python manage.py showmigrations` with `DB_HOST` pointing at the restored server. All migrations should be applied.

### 4. Cut over the application

1. Set `DB_HOST` (and `DB_USER` / `DB_PASSWORD` if they changed) for the backend to the restored server.
2. Restart the backend and confirm `GET /api/health/` returns healthy.
3. Re-apply any firewall rules, private networking and server parameters, because these are not always copied by a restore.
4. Once the restore is confirmed, either rename it in Terraform or import it into Terraform state so `infra/terraform` matches what is running.

## Restore test (required before go-live, then at least every 6 months)

1. Pick a restore time at least 1 hour in the past.
2. Run the point-in-time restore (step 1) to a temporary server named `psql-employeeleavetrack-44834-restoretest`.
3. Run the verification steps (step 3).
4. Record the result below, then delete the temporary server:
   `az postgres flexible-server delete --resource-group <resource-group> --name psql-employeeleavetrack-44834-restoretest --yes`

| Date | Performed by | Restore type | Restore point (UTC) | Time to restore | Result |
|---|---|---|---|---|---|
| _pending, must be completed before go-live_ | | PITR | | | |

## Local development (docker compose)

The local `db` service uses the `pgdata` Docker volume and is not backed up. Take a manual dump if you need one:

```bash
docker compose exec db pg_dump -U postgres -Fc leave_tracker > leave_tracker.dump
docker compose exec -T db pg_restore -U postgres -d leave_tracker --clean < leave_tracker.dump
```
