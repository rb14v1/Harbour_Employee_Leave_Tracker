from django.db import IntegrityError, transaction
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from common.testing import AdminAPITestCase, make_employee

from apps.employees.models import Employee


def payload(**overrides):
    data = {
        "employee_id": "EMP100",
        "full_name": "Asha Rao",
        "email": "asha.rao@example.com",
        "department": "Finance",
        "designation": "Analyst",
        "joining_date": "2021-04-01",
    }
    data.update(overrides)
    return data


class EmployeeCRUDTests(AdminAPITestCase):
    def test_create_employee(self):
        response = self.client.post(reverse("employee-list"), payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["employee_id"], "EMP100")
        self.assertTrue(response.data["is_active"])
        self.assertTrue(Employee.objects.filter(employee_id="EMP100").exists())

    def test_create_rejects_duplicate_employee_id(self):
        make_employee(100, employee_id="EMP100")
        response = self.client.post(
            reverse("employee-list"), payload(email="other@example.com"), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("employee_id", response.data)

    def test_create_rejects_duplicate_email_case_insensitive(self):
        make_employee(1, email="same@example.com")
        response = self.client.post(
            reverse("employee-list"),
            payload(employee_id="EMP200", email="SAME@example.com"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_create_rejects_missing_required_fields(self):
        response = self.client.post(reverse("employee-list"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("full_name", response.data)

    def test_create_rejects_invalid_email(self):
        response = self.client.post(
            reverse("employee-list"), payload(email="not-an-email"), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_returns_paginated_employees(self):
        for index in range(1, 4):
            make_employee(index)
        response = self.client.get(reverse("employee-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 3)

    def test_retrieve_employee(self):
        employee = make_employee(5)
        response = self.client.get(reverse("employee-detail", args=[employee.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["full_name"], "Employee 5")

    def test_retrieve_missing_employee_returns_404(self):
        response = self.client.get(reverse("employee-detail", args=[999999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_employee(self):
        employee = make_employee(7)
        response = self.client.put(
            reverse("employee-detail", args=[employee.pk]),
            payload(employee_id="EMP007", full_name="Updated Name", email="employee7@example.com"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        employee.refresh_from_db()
        self.assertEqual(employee.full_name, "Updated Name")

    def test_update_allows_keeping_own_email(self):
        employee = make_employee(8)
        response = self.client.patch(
            reverse("employee-detail", args=[employee.pk]),
            {"email": employee.email},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_deactivates_instead_of_removing(self):
        employee = make_employee(9)
        response = self.client.delete(reverse("employee-detail", args=[employee.pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        employee.refresh_from_db()
        self.assertFalse(employee.is_active)
        self.assertTrue(Employee.objects.filter(pk=employee.pk).exists())

    def test_filter_by_active_status(self):
        make_employee(1)
        make_employee(2, is_active=False)
        active = self.client.get(reverse("employee-list"), {"is_active": "true"})
        inactive = self.client.get(reverse("employee-list"), {"is_active": "false"})
        self.assertEqual(active.data["count"], 1)
        self.assertEqual(inactive.data["count"], 1)

    def test_filter_rejects_invalid_boolean(self):
        response = self.client.get(reverse("employee-list"), {"is_active": "maybe"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_by_name_and_department(self):
        make_employee(1, full_name="Priya Shah", department="Sales")
        make_employee(2, full_name="Ravi Kumar", department="Engineering")
        by_name = self.client.get(reverse("employee-list"), {"search": "priya"})
        by_department = self.client.get(reverse("employee-list"), {"search": "engineering"})
        self.assertEqual([e["full_name"] for e in by_name.data["results"]], ["Priya Shah"])
        self.assertEqual([e["full_name"] for e in by_department.data["results"]], ["Ravi Kumar"])


class EmployeeDatabaseConstraintTests(APITestCase):
    def test_database_rejects_duplicate_email_ignoring_case(self):
        make_employee(1, email="dup@example.com")
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_employee(2, email="DUP@example.com")

    def test_database_rejects_duplicate_employee_id(self):
        make_employee(1, employee_id="SAME")
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_employee(2, employee_id="SAME")


class EmployeePermissionTests(APITestCase):
    def test_unauthenticated_requests_are_rejected(self):
        employee = make_employee(1)
        self.assertEqual(self.client.get(reverse("employee-list")).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            self.client.post(reverse("employee-list"), payload(), format="json").status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            self.client.delete(reverse("employee-detail", args=[employee.pk])).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
