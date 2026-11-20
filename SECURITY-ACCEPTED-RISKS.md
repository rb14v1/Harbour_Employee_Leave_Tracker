# Accepted dependency risks

This file lists known CVEs in the dependencies of EmployeeLeaveTrack-44834
(`backend/requirements.txt`, `frontend/package.json`, and the base images in
`backend/Dockerfile` and `frontend/Dockerfile`) that we cannot fix yet.

## Policy

- A CRITICAL or HIGH CVE that **has a fixed version** blocks deployment. Pin the
  dependency to the patched version. Such CVEs must never be listed here.
- A CRITICAL or HIGH CVE that **has no fixed version yet** does not block
  deployment, but it must be listed below with a justification, any
  mitigation, an owner and a review date.
- Review each entry on or before its review date. Once a fix is released,
  pin the patched version and delete the entry.
- Dependabot (`.github/dependabot.yml`) opens weekly update PRs for pip, npm
  and Docker base images. Use a scanner (Trivy, `pip-audit`,
  `npm audit --audit-level=high`) to check dependencies before each release.

## Accepted risks (no fix available)

| CVE | Package / version | Severity | Justification / mitigation | Owner | Added | Review date |
|-----|-------------------|----------|----------------------------|-------|-------|-------------|
| _none_ | | | | | | |

## Being fixed (fix available, so these block deployment)

| CVE | Package / version | Severity | Fixed in | Status |
|-----|-------------------|----------|----------|--------|
| CVE-2026-114136 | djangorestframework 3.16.1 | HIGH | Waiting for the Trivy report | The pin in `backend/requirements.txt` will change |
| CVE-2026-114137 | djangorestframework 3.16.1 | HIGH | Waiting for the Trivy report | The pin in `backend/requirements.txt` will change |
| CVE-2026-114138 | djangorestframework 3.16.1 | HIGH | Waiting for the Trivy report | The pin in `backend/requirements.txt` will change |

Next scheduled review of this file: 2027-02-20.
