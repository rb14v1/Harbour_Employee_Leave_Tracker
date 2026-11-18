from django.db import models
from django.db.models.functions import Lower

from common.models import TimeStampedModel


class Employee(TimeStampedModel):
    employee_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField(max_length=254)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    joining_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["full_name", "id"]
        constraints = [
            models.UniqueConstraint(Lower("email"), name="employee_email_unique_ci"),
        ]
        indexes = [
            models.Index(fields=["is_active"], name="employee_active_idx"),
            models.Index(fields=["department"], name="employee_department_idx"),
        ]

    def __str__(self):
        return f"{self.employee_id} - {self.full_name}"
