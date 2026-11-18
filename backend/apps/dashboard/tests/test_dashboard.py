from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from common.testing import AdminAPITestCase, make_employee

from apps.leaves.models import LeaveApplication, LeaveType

Status = LeaveApplication.Status


class DashboardTests(AdminAPITestCase):
    def setUp(self):
        super().setUp()
        self.casual = LeaveType.objects.get(name="Casual Leave")
        self.sick = LeaveType.objects.get(name="Sick Leave")
        self.first = make_employee(1)
        self.second = make_employee(2)
        make_employee(3, is_active=False)

        today = timezone.localdate()
        self.on_leave = self._create(self.first, self.casual, today - timedelta(days=1), today + timedelta(days=1), Status.APPROVED)
        self._create(self.second, self.sick, today + timedelta(days=30), today + timedelta(days=31), Status.PENDING)
        self._create(self.second, self.casual, today + timedelta(days=60), today + timedelta(days=60), Status.REJECTED)
        self._create(self.first, self.sick, today - timedelta(days=40), today - timedelta(days=39), Status.CANCELLED)

    def _create(self, employee, leave_type, start, end, status_value):
        application = LeaveApplication.objects.create(
            employee=employee, leave_type=leave_type, start_date=start, end_date=end, reason="Test"
        )
        LeaveApplication.objects.filter(pk=application.pk).update(status=status_value)
        application.refresh_from_db()
        return application

    def get_dashboard(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data

    def test_employee_counts(self):
        data = self.get_dashboard()
        self.assertEqual(data["employees"]["total"], 3)
        self.assertEqual(data["employees"]["active"], 2)
        self.assertEqual(data["employees"]["inactive"], 1)

    def test_application_status_counts(self):
        counts = self.get_dashboard()["leave_applications"]
        self.assertEqual(counts["total"], 4)
        self.assertEqual(counts["pending"], 1)
        self.assertEqual(counts["approved"], 1)
        self.assertEqual(counts["rejected"], 1)
        self.assertEqual(counts["cancelled"], 1)

    def test_employees_currently_on_leave(self):
        on_leave = self.get_dashboard()["employees_on_leave"]
        self.assertEqual(len(on_leave), 1)
        self.assertEqual(on_leave[0]["employee_name"], "Employee 1")
        self.assertEqual(on_leave[0]["id"], self.on_leave.pk)

    def test_grouped_by_leave_type(self):
        by_type = {row["name"]: row for row in self.get_dashboard()["by_leave_type"]}
        self.assertEqual(by_type["Casual Leave"]["total"], 2)
        self.assertEqual(by_type["Casual Leave"]["approved"], 1)
        self.assertEqual(by_type["Casual Leave"]["rejected"], 1)
        self.assertEqual(by_type["Sick Leave"]["pending"], 1)
        self.assertEqual(by_type["Sick Leave"]["cancelled"], 1)
        self.assertEqual(by_type["Earned Leave"]["total"], 0)

    def test_recent_applications_are_newest_first(self):
        recent = self.get_dashboard()["recent_applications"]
        self.assertEqual(len(recent), 4)
        applied = [row["applied_on"] for row in recent]
        self.assertEqual(applied, sorted(applied, reverse=True))

    def test_dashboard_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
