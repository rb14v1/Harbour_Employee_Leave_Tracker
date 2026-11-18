from rest_framework import status, viewsets
from rest_framework.response import Response

from common.query import parse_bool_param

from . import services
from .models import Employee
from .serializers import EmployeeSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    search_fields = ["employee_id", "full_name", "email", "department", "designation"]
    ordering_fields = ["full_name", "employee_id", "department", "joining_date"]

    def get_queryset(self):
        queryset = Employee.objects.all()
        is_active = parse_bool_param(self.request, "is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
        department = self.request.query_params.get("department")
        if department:
            queryset = queryset.filter(department__iexact=department.strip())
        return queryset

    def destroy(self, request, *args, **kwargs):
        services.deactivate_employee(self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)
