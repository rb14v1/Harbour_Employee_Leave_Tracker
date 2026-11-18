from django.db import models
from django.db.models import F, Q

from apps.employees.models import Employee
from common.models import TimeStampedModel


class LeaveType(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    default_annual_allowance = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Days per calendar year. Leave empty for unlimited.",
    )

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return self.name


class LeaveApplication(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    employee = models.ForeignKey(
        Employee, on_delete=models.PROTECT, related_name="leave_applications"
    )
    leave_type = models.ForeignKey(
        LeaveType, on_delete=models.PROTECT, related_name="applications"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    number_of_days = models.PositiveIntegerField(editable=False)
    reason = models.TextField()
    applied_on = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    admin_remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-applied_on", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__gte=F("start_date")),
                name="leave_end_not_before_start",
            ),
            models.CheckConstraint(
                condition=Q(number_of_days__gte=1),
                name="leave_days_at_least_one",
            ),
            models.CheckConstraint(
                condition=Q(status__in=["PENDING", "APPROVED", "REJECTED", "CANCELLED"]),
                name="leave_status_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["employee", "status"], name="leave_employee_status_idx"),
            models.Index(fields=["start_date", "end_date"], name="leave_date_range_idx"),
        ]

    def save(self, *args, **kwargs):
        self.number_of_days = (self.end_date - self.start_date).days + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} {self.leave_type} {self.start_date} to {self.end_date}"
