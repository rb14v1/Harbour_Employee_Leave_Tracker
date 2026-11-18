from django.contrib import admin

from .models import LeaveApplication, LeaveType


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "default_annual_allowance"]


@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ["employee", "leave_type", "start_date", "end_date", "number_of_days", "status"]
    list_filter = ["status", "leave_type"]
    search_fields = ["employee__full_name", "employee__employee_id", "reason"]
