from datetime import date

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.employees.models import Employee

PASSWORD = "StrongPass!12345"


class AdminAPITestCase(APITestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password=PASSWORD
        )
        self.client.force_authenticate(user=self.admin)


def make_employee(index=1, **overrides):
    data = {
        "employee_id": f"EMP{index:03d}",
        "full_name": f"Employee {index}",
        "email": f"employee{index}@example.com",
        "department": "Engineering",
        "designation": "Developer",
        "joining_date": date(2020, 1, 1),
    }
    data.update(overrides)
    return Employee.objects.create(**data)
