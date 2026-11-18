from django.db import transaction
from django.db.models import Sum
from rest_framework.exceptions import ValidationError

from apps.employees.models import Employee
from common.exceptions import ConflictError

from .models import LeaveApplication, LeaveType

Status = LeaveApplication.Status
ACTIVE_STATUSES = (Status.PENDING, Status.APPROVED)


def _lock_employee(employee_id):
    return Employee.objects.select_for_update().get(pk=employee_id)


def _lock_application(application_id):
    employee_id = LeaveApplication.objects.values_list("employee_id", flat=True).get(pk=application_id)
    _lock_employee(employee_id)
    return LeaveApplication.objects.select_for_update().get(pk=application_id)


def _validate_date_range(start_date, end_date):
    if end_date < start_date:
        raise ValidationError({"end_date": "End date cannot be before start date."})


def _ensure_employee_active(employee):
    if not employee.is_active:
        raise ValidationError({"employee": "Inactive employees cannot apply for leave."})


def _ensure_no_overlap(employee_id, start_date, end_date, exclude_id=None):
    queryset = LeaveApplication.objects.filter(
        employee_id=employee_id,
        status__in=ACTIVE_STATUSES,
        start_date__lte=end_date,
        end_date__gte=start_date,
    )
    if exclude_id is not None:
        queryset = queryset.exclude(pk=exclude_id)
    conflict = queryset.order_by("id").first()
    if conflict is not None:
        raise ConflictError(
            f"Dates overlap leave application #{conflict.pk} "
            f"({conflict.start_date} to {conflict.end_date}, {conflict.status.lower()})."
        )


def _taken_days(employee_id, leave_type_id, year):
    total = LeaveApplication.objects.filter(
        employee_id=employee_id,
        leave_type_id=leave_type_id,
        status=Status.APPROVED,
        start_date__year=year,
    ).aggregate(total=Sum("number_of_days"))["total"]
    return total or 0


def _ensure_balance(employee_id, leave_type, year, days):
    allowance = leave_type.default_annual_allowance
    if allowance is None:
        return
    remaining = allowance - _taken_days(employee_id, leave_type.pk, year)
    if days > remaining:
        raise ValidationError(
            {
                "leave_type": (
                    f"Insufficient leave balance. Remaining: {max(remaining, 0)} day(s), "
                    f"requested: {days} day(s)."
                )
            }
        )


def _require_status(application, allowed, action):
    if application.status not in allowed:
        names = " or ".join(s.lower() for s in allowed)
        raise ConflictError(f"Only {names} applications can be {action}.")


@transaction.atomic
def create_leave_application(*, employee, leave_type, start_date, end_date, reason):
    _validate_date_range(start_date, end_date)
    employee = _lock_employee(employee.pk)
    _ensure_employee_active(employee)
    _ensure_no_overlap(employee.pk, start_date, end_date)
    return LeaveApplication.objects.create(
        employee=employee,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
    )


@transaction.atomic
def update_leave_application(application_id, **changes):
    application = _lock_application(application_id)
    _require_status(application, (Status.PENDING,), "edited")

    start_date = changes.get("start_date", application.start_date)
    end_date = changes.get("end_date", application.end_date)
    _validate_date_range(start_date, end_date)

    employee = changes.get("employee", application.employee)
    if employee.pk != application.employee_id:
        employee = _lock_employee(employee.pk)
    _ensure_employee_active(employee)
    _ensure_no_overlap(employee.pk, start_date, end_date, exclude_id=application.pk)

    for field, value in changes.items():
        setattr(application, field, value)
    application.save()
    return application


@transaction.atomic
def approve_leave_application(application_id, admin_remarks=""):
    application = _lock_application(application_id)
    _require_status(application, (Status.PENDING,), "approved")
    _ensure_no_overlap(
        application.employee_id,
        application.start_date,
        application.end_date,
        exclude_id=application.pk,
    )
    _ensure_balance(
        application.employee_id,
        application.leave_type,
        application.start_date.year,
        application.number_of_days,
    )
    application.status = Status.APPROVED
    application.admin_remarks = admin_remarks
    application.save()
    return application


@transaction.atomic
def reject_leave_application(application_id, admin_remarks=""):
    application = _lock_application(application_id)
    _require_status(application, (Status.PENDING,), "rejected")
    application.status = Status.REJECTED
    application.admin_remarks = admin_remarks
    application.save()
    return application


@transaction.atomic
def cancel_leave_application(application_id, admin_remarks=""):
    application = _lock_application(application_id)
    _require_status(application, (Status.PENDING, Status.APPROVED), "cancelled")
    application.status = Status.CANCELLED
    application.admin_remarks = admin_remarks
    application.save()
    return application


@transaction.atomic
def delete_leave_application(application_id):
    application = _lock_application(application_id)
    if application.status == Status.APPROVED:
        raise ConflictError("Approved applications cannot be deleted. Cancel them instead.")
    application.delete()


def build_balance(allocated, taken):
    return {
        "allocated": allocated,
        "taken": taken,
        "remaining": None if allocated is None else allocated - taken,
    }


def get_leave_balances(*, year, employee_id=None):
    employees = Employee.objects.all()
    if employee_id is not None:
        employees = employees.filter(pk=employee_id)
    leave_types = list(LeaveType.objects.all())

    taken_map = {
        (row["employee_id"], row["leave_type_id"]): row["total"]
        for row in LeaveApplication.objects.filter(status=Status.APPROVED, start_date__year=year)
        .order_by()
        .values("employee_id", "leave_type_id")
        .annotate(total=Sum("number_of_days"))
    }

    rows = []
    for employee in employees:
        for leave_type in leave_types:
            taken = taken_map.get((employee.pk, leave_type.pk), 0)
            rows.append(
                {
                    "employee_id": employee.pk,
                    "employee_code": employee.employee_id,
                    "employee_name": employee.full_name,
                    "leave_type_id": leave_type.pk,
                    "leave_type_name": leave_type.name,
                    "year": year,
                    **build_balance(leave_type.default_annual_allowance, taken),
                }
            )
    return rows
