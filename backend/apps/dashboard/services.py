from django.db.models import Count, Q
from django.utils import timezone

from apps.employees.models import Employee
from apps.leaves.models import LeaveApplication, LeaveType

Status = LeaveApplication.Status


def _application_row(application):
    return {
        "id": application.pk,
        "employee_id": application.employee.pk,
        "employee_code": application.employee.employee_id,
        "employee_name": application.employee.full_name,
        "leave_type_name": application.leave_type.name,
        "start_date": application.start_date,
        "end_date": application.end_date,
        "number_of_days": application.number_of_days,
        "status": application.status,
        "applied_on": application.applied_on,
    }


def build_dashboard():
    today = timezone.localdate()

    employee_counts = Employee.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
    )
    status_counts = LeaveApplication.objects.aggregate(
        total=Count("id"),
        pending=Count("id", filter=Q(status=Status.PENDING)),
        approved=Count("id", filter=Q(status=Status.APPROVED)),
        rejected=Count("id", filter=Q(status=Status.REJECTED)),
        cancelled=Count("id", filter=Q(status=Status.CANCELLED)),
    )
    on_leave = (
        LeaveApplication.objects.select_related("employee", "leave_type")
        .filter(status=Status.APPROVED, start_date__lte=today, end_date__gte=today)
        .order_by("end_date", "id")
    )
    by_leave_type = (
        LeaveType.objects.annotate(
            total=Count("applications"),
            pending=Count("applications", filter=Q(applications__status=Status.PENDING)),
            approved=Count("applications", filter=Q(applications__status=Status.APPROVED)),
            rejected=Count("applications", filter=Q(applications__status=Status.REJECTED)),
            cancelled=Count("applications", filter=Q(applications__status=Status.CANCELLED)),
        )
        .order_by("name")
        .values("id", "name", "total", "pending", "approved", "rejected", "cancelled")
    )
    recent = LeaveApplication.objects.select_related("employee", "leave_type")[:10]

    return {
        "date": today,
        "employees": {
            "total": employee_counts["total"],
            "active": employee_counts["active"],
            "inactive": employee_counts["total"] - employee_counts["active"],
        },
        "leave_applications": {
            "total": status_counts["total"],
            "pending": status_counts["pending"],
            "approved": status_counts["approved"],
            "rejected": status_counts["rejected"],
            "cancelled": status_counts["cancelled"],
        },
        "employees_on_leave": [_application_row(a) for a in on_leave],
        "by_leave_type": list(by_leave_type),
        "recent_applications": [_application_row(a) for a in recent],
    }
