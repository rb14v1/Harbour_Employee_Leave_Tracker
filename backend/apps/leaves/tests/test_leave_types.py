from datetime import date

from django.urls import reverse
from rest_framework import status

from common.testing import AdminAPITestCase, make_employee

from apps.leaves.models import LeaveApplication, LeaveType


class LeaveTypeTests(AdminAPITestCase):
    def test_default_leave_types_are_seeded(self):
        response = self.client.get(reverse("leave-type-list"))
        names = {item["name"] for item in response.data["results"]}
        self.assertTrue({"Casual Leave", "Sick Leave", "Earned Leave", "Unpaid Leave"}.issubset(names))

    def test_unpaid_leave_is_unlimited_and_casual_has_allowance(self):
        self.assertIsNone(LeaveType.objects.get(name="Unpaid Leave").default_annual_allowance)
        self.assertEqual(LeaveType.objects.get(name="Casual Leave").default_annual_allowance, 12)

    def test_create_leave_type(self):
        response = self.client.post(
            reverse("leave-type-list"),
            {"name": "Maternity Leave", "default_annual_allowance": 90},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["default_annual_allowance"], 90)

    def test_create_rejects_duplicate_name(self):
        response = self.client.post(
            reverse("leave-type-list"), {"name": "Sick Leave", "default_annual_allowance": 5}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_rejects_negative_allowance(self):
        response = self.client.post(
            reverse("leave-type-list"), {"name": "Negative", "default_annual_allowance": -1}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_allowance(self):
        leave_type = LeaveType.objects.get(name="Sick Leave")
        response = self.client.patch(
            reverse("leave-type-detail", args=[leave_type.pk]),
            {"default_annual_allowance": 14},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        leave_type.refresh_from_db()
        self.assertEqual(leave_type.default_annual_allowance, 14)

    def test_delete_unused_leave_type(self):
        leave_type = LeaveType.objects.create(name="Temporary", default_annual_allowance=1)
        response = self.client.delete(reverse("leave-type-detail", args=[leave_type.pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_leave_type_in_use_returns_409(self):
        employee = make_employee(1)
        leave_type = LeaveType.objects.get(name="Casual Leave")
        LeaveApplication.objects.create(
            employee=employee,
            leave_type=leave_type,
            start_date=date(2030, 1, 2),
            end_date=date(2030, 1, 3),
            reason="Test",
        )
        response = self.client.delete(reverse("leave-type-detail", args=[leave_type.pk]))
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(LeaveType.objects.filter(pk=leave_type.pk).exists())
