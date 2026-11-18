from rest_framework import serializers

from .models import LeaveApplication, LeaveType


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ["id", "name", "default_annual_allowance", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class LeaveApplicationSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    employee_code = serializers.CharField(source="employee.employee_id", read_only=True)
    leave_type_name = serializers.CharField(source="leave_type.name", read_only=True)

    class Meta:
        model = LeaveApplication
        fields = [
            "id",
            "employee",
            "employee_name",
            "employee_code",
            "leave_type",
            "leave_type_name",
            "start_date",
            "end_date",
            "number_of_days",
            "reason",
            "applied_on",
            "status",
            "admin_remarks",
        ]
        read_only_fields = ["id", "number_of_days", "applied_on", "status", "admin_remarks"]


class ReviewSerializer(serializers.Serializer):
    admin_remarks = serializers.CharField(required=False, allow_blank=True, max_length=1000, default="")
