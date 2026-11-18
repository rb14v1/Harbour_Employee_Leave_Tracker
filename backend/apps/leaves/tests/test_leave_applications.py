from datetime import date

from django.db import IntegrityError, transaction
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from common.testing import AdminAPITestCase, make_employee

from apps.leaves.models import LeaveApplication, LeaveType

Status = LeaveApplication.Status


def make_application(employee, leave_type, start, end, status_value=Status.PENDING):
    application = LeaveApplication.objects.create(
        employee=employee,
        leave_type=leave_type,
        start_date=start,
        end_date=end,
        reason="Test reason",
    )
    if status_value != Status.PENDING:
        LeaveApplication.objects.filter(pk=application.pk).update(status=status_value)
        application.refresh_from_db()
    return application


class LeaveApplicationCreateTests(AdminAPITestCase):
    def setUp(self):
        super().setUp()
        self.employee = make_employee(1)
        self.casual = LeaveType.objects.get(name="Casual Leave")

    def payload(self, **overrides):
        data = {
            "employee": self.employee.pk,
            "leave_type": self.casual.pk,
            "start_date": "2030-03-04",
            "end_date": "2030-03-06",
            "reason": "Family event",
        }
        data.update(overrides)
        return data

    def test_create_pending_application_with_inclusive_day_count(self):
        response = self.client.post(reverse("leave-list"), self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "PENDING")
        self.assertEqual(response.data["number_of_days"], 3)
        self.assertEqual(response.data["employee_name"], "Employee 1")

    def test_end_date_before_start_date_returns_400(self):
        response = self.client.post(
            reverse("leave-list"),
            self.payload(start_date="2030-03-10", end_date="2030-03-05"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("end_date", response.data)

    def test_missing_reason_returns_400(self):
        data = self.payload()
        del data["reason"]
        response = self.client.post(reverse("leave-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_employee_returns_400(self):
        response = self.client.post(reverse("leave-list"), self.payload(employee=999999), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inactive_employee_cannot_apply(self):
        self.employee.is_active = False
        self.employee.save()
        response = self.client.post(reverse("leave-list"), self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_overlapping_pending_application_returns_409(self):
        make_application(self.employee, self.casual, date(2030, 3, 4), date(2030, 3, 6))
        response = self.client.post(
            reverse("leave-list"),
            self.payload(start_date="2030-03-05", end_date="2030-03-07"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_overlapping_approved_application_returns_409(self):
        make_application(self.employee, self.casual, date(2030, 3, 4), date(2030, 3, 6), Status.APPROVED)
        response = self.client.post(
            reverse("leave-list"),
            self.payload(start_date="2030-03-06", end_date="2030-03-08"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_adjacent_dates_do_not_overlap(self):
        make_application(self.employee, self.casual, date(2030, 3, 4), date(2030, 3, 6))
        response = self.client.post(
            reverse("leave-list"),
            self.payload(start_date="2030-03-07", end_date="2030-03-08"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_rejected_and_cancelled_applications_do_not_block_overlap(self):
        make_application(self.employee, self.casual, date(2030, 3, 4), date(2030, 3, 6), Status.REJECTED)
        make_application(self.employee, self.casual, date(2030, 3, 4), date(2030, 3, 6), Status.CANCELLED)
        response = self.client.post(reverse("leave-list"), self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class LeaveApplicationReviewTests(AdminAPITestCase):
    def setUp(self):
        super().setUp()
        self.employee = make_employee(1)
        self.casual = LeaveType.objects.get(name="Casual Leave")
        self.application = make_application(self.employee, self.casual, date(2030, 5, 1), date(2030, 5, 3))

    def action(self, name, application=None, data=None):
        application = application or self.application
        return self.client.post(
            reverse(f"leave-{name}", args=[application.pk]), data or {}, format="json"
        )

    def test_approve_pending_application(self):
        response = self.action("approve", data={"admin_remarks": "Enjoy"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "APPROVED")
        self.assertEqual(response.data["admin_remarks"], "Enjoy")

    def test_reject_pending_application(self):
        response = self.action("reject", data={"admin_remarks": "Team deadline"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "REJECTED")

    def test_cancel_approved_application(self):
        self.action("approve")
        response = self.action("cancel")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "CANCELLED")

    def test_approving_twice_returns_409(self):
        self.action("approve")
        response = self.action("approve")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_rejecting_approved_application_returns_409(self):
        self.action("approve")
        response = self.action("reject")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_cancelling_rejected_application_returns_409(self):
        self.action("reject")
        response = self.action("cancel")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_review_of_missing_application_returns_404(self):
        response = self.client.post(reverse("leave-approve", args=[999999]), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_approve_fails_when_balance_insufficient(self):
        casual_allowance = self.casual.default_annual_allowance
        make_application(
            self.employee,
            self.casual,
            date(2030, 1, 1),
            date(2030, 1, casual_allowance),
            Status.APPROVED,
        )
        response = self.action("approve")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("leave_type", response.data)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Status.PENDING)

    def test_unlimited_leave_type_ignores_balance(self):
        unpaid = LeaveType.objects.get(name="Unpaid Leave")
        application = make_application(self.employee, unpaid, date(2030, 6, 1), date(2030, 9, 30))
        response = self.action("approve", application=application)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LeaveApplicationEditDeleteTests(AdminAPITestCase):
    def setUp(self):
        super().setUp()
        self.employee = make_employee(1)
        self.casual = LeaveType.objects.get(name="Casual Leave")

    def test_edit_pending_application(self):
        application = make_application(self.employee, self.casual, date(2030, 7, 1), date(2030, 7, 2))
        response = self.client.patch(
            reverse("leave-detail", args=[application.pk]),
            {"end_date": "2030-07-04", "reason": "Extended"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["number_of_days"], 4)
        self.assertEqual(response.data["reason"], "Extended")

    def test_edit_into_invalid_range_returns_400(self):
        application = make_application(self.employee, self.casual, date(2030, 7, 1), date(2030, 7, 2))
        response = self.client.patch(
            reverse("leave-detail", args=[application.pk]), {"end_date": "2030-06-30"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_edit_that_creates_overlap_returns_409(self):
        make_application(self.employee, self.casual, date(2030, 8, 1), date(2030, 8, 5))
        application = make_application(self.employee, self.casual, date(2030, 9, 1), date(2030, 9, 2))
        response = self.client.patch(
            reverse("leave-detail", args=[application.pk]),
            {"start_date": "2030-08-04", "end_date": "2030-08-04"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_approved_application_cannot_be_edited(self):
        application = make_application(
            self.employee, self.casual, date(2030, 7, 1), date(2030, 7, 2), Status.APPROVED
        )
        response = self.client.patch(
            reverse("leave-detail", args=[application.pk]), {"reason": "Changed"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_delete_pending_application(self):
        application = make_application(self.employee, self.casual, date(2030, 7, 1), date(2030, 7, 2))
        response = self.client.delete(reverse("leave-detail", args=[application.pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(LeaveApplication.objects.filter(pk=application.pk).exists())

    def test_delete_approved_application_returns_409(self):
        application = make_application(
            self.employee, self.casual, date(2030, 7, 1), date(2030, 7, 2), Status.APPROVED
        )
        response = self.client.delete(reverse("leave-detail", args=[application.pk]))
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(LeaveApplication.objects.filter(pk=application.pk).exists())

    def test_employee_with_leave_history_cannot_be_hard_deleted(self):
        make_application(self.employee, self.casual, date(2030, 7, 1), date(2030, 7, 2))
        response = self.client.delete(reverse("employee-detail", args=[self.employee.pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.employee.refresh_from_db()
        self.assertFalse(self.employee.is_active)


class LeaveApplicationFilterTests(AdminAPITestCase):
    def test_filter_by_status_and_employee(self):
        first = make_employee(1)
        second = make_employee(2)
        casual = LeaveType.objects.get(name="Casual Leave")
        make_application(first, casual, date(2030, 1, 1), date(2030, 1, 1), Status.APPROVED)
        make_application(second, casual, date(2030, 2, 1), date(2030, 2, 1))

        by_status = self.client.get(reverse("leave-list"), {"status": "approved"})
        by_employee = self.client.get(reverse("leave-list"), {"employee": second.pk})
        self.assertEqual(by_status.data["count"], 1)
        self.assertEqual(by_employee.data["count"], 1)
        self.assertEqual(by_employee.data["results"][0]["status"], "PENDING")

    def test_invalid_status_filter_returns_400(self):
        response = self.client.get(reverse("leave-list"), {"status": "maybe"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_date_filter_returns_400(self):
        response = self.client.get(reverse("leave-list"), {"start_date_from": "2030-02-30"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LeaveBalanceTests(AdminAPITestCase):
    def setUp(self):
        super().setUp()
        self.employee = make_employee(1)
        self.casual = LeaveType.objects.get(name="Casual Leave")

    def balance_for(self, year=2030, leave_type_name="Casual Leave"):
        response = self.client.get(reverse("leave-balances"), {"year": year, "employee": self.employee.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return next(row for row in response.data if row["leave_type_name"] == leave_type_name)

    def test_only_approved_leave_is_deducted(self):
        make_application(self.employee, self.casual, date(2030, 1, 1), date(2030, 1, 2), Status.APPROVED)
        make_application(self.employee, self.casual, date(2030, 2, 1), date(2030, 2, 3))
        make_application(self.employee, self.casual, date(2030, 3, 1), date(2030, 3, 4), Status.REJECTED)
        make_application(self.employee, self.casual, date(2030, 4, 1), date(2030, 4, 5), Status.CANCELLED)

        balance = self.balance_for()
        self.assertEqual(balance["allocated"], 12)
        self.assertEqual(balance["taken"], 2)
        self.assertEqual(balance["remaining"], 10)

    def test_balance_is_per_year(self):
        make_application(self.employee, self.casual, date(2029, 12, 30), date(2029, 12, 31), Status.APPROVED)
        balance = self.balance_for(year=2030)
        self.assertEqual(balance["taken"], 0)
        self.assertEqual(balance["remaining"], 12)

    def test_unlimited_leave_has_no_remaining_value(self):
        balance = self.balance_for(leave_type_name="Unpaid Leave")
        self.assertIsNone(balance["allocated"])
        self.assertIsNone(balance["remaining"])

    def test_approval_reduces_balance(self):
        application = make_application(self.employee, self.casual, date(2030, 5, 1), date(2030, 5, 2))
        self.client.post(reverse("leave-approve", args=[application.pk]), {}, format="json")
        self.assertEqual(self.balance_for()["remaining"], 10)

    def test_cancelling_approved_leave_restores_balance(self):
        application = make_application(self.employee, self.casual, date(2030, 5, 1), date(2030, 5, 2))
        self.client.post(reverse("leave-approve", args=[application.pk]), {}, format="json")
        self.client.post(reverse("leave-cancel", args=[application.pk]), {}, format="json")
        self.assertEqual(self.balance_for()["remaining"], 12)


class LeaveDatabaseConstraintTests(APITestCase):
    def test_database_rejects_end_date_before_start_date(self):
        employee = make_employee(1)
        casual = LeaveType.objects.get(name="Casual Leave")
        with self.assertRaises(IntegrityError), transaction.atomic():
            LeaveApplication.objects.create(
                employee=employee,
                leave_type=casual,
                start_date=date(2030, 2, 10),
                end_date=date(2030, 2, 1),
                reason="Invalid",
            )

    def test_database_rejects_unknown_status(self):
        employee = make_employee(1)
        casual = LeaveType.objects.get(name="Casual Leave")
        application = make_application(employee, casual, date(2030, 1, 1), date(2030, 1, 1))
        with self.assertRaises(IntegrityError), transaction.atomic():
            LeaveApplication.objects.filter(pk=application.pk).update(status="BOGUS")

    def test_database_rejects_duplicate_leave_type_name(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            LeaveType.objects.create(name="Casual Leave", default_annual_allowance=1)


class LeavePermissionTests(APITestCase):
    def test_unauthenticated_requests_are_rejected(self):
        self.assertEqual(self.client.get(reverse("leave-list")).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(reverse("leave-type-list")).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(reverse("leave-balances")).status_code, status.HTTP_401_UNAUTHORIZED)
