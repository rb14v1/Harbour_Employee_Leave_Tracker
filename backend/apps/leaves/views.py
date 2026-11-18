from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from common.query import parse_date_param, parse_int_param

from . import services
from .models import LeaveApplication, LeaveType
from .serializers import LeaveApplicationSerializer, LeaveTypeSerializer, ReviewSerializer


class LeaveTypeViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveTypeSerializer
    queryset = LeaveType.objects.all()
    search_fields = ["name"]
    ordering_fields = ["name", "default_annual_allowance"]


class LeaveApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveApplicationSerializer
    search_fields = ["reason", "employee__full_name", "employee__employee_id"]
    ordering_fields = ["applied_on", "start_date", "end_date", "status"]

    def get_queryset(self):
        queryset = LeaveApplication.objects.select_related("employee", "leave_type")

        employee_id = parse_int_param(self.request, "employee")
        if employee_id is not None:
            queryset = queryset.filter(employee_id=employee_id)

        leave_type_id = parse_int_param(self.request, "leave_type")
        if leave_type_id is not None:
            queryset = queryset.filter(leave_type_id=leave_type_id)

        status_value = self.request.query_params.get("status")
        if status_value:
            status_value = status_value.strip().upper()
            if status_value not in LeaveApplication.Status.values:
                raise ValidationError(
                    {"status": f"Must be one of: {', '.join(LeaveApplication.Status.values)}."}
                )
            queryset = queryset.filter(status=status_value)

        start_from = parse_date_param(self.request, "start_date_from")
        if start_from is not None:
            queryset = queryset.filter(start_date__gte=start_from)

        start_to = parse_date_param(self.request, "start_date_to")
        if start_to is not None:
            queryset = queryset.filter(start_date__lte=start_to)

        return queryset

    def perform_create(self, serializer):
        serializer.instance = services.create_leave_application(**serializer.validated_data)

    def perform_update(self, serializer):
        serializer.instance = services.update_leave_application(
            serializer.instance.pk, **serializer.validated_data
        )

    def perform_destroy(self, instance):
        services.delete_leave_application(instance.pk)

    def _review(self, request, pk, operation):
        self.get_object()
        review = ReviewSerializer(data=request.data)
        review.is_valid(raise_exception=True)
        application = operation(int(pk), admin_remarks=review.validated_data["admin_remarks"])
        return Response(self.get_serializer(application).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._review(request, pk, services.approve_leave_application)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._review(request, pk, services.reject_leave_application)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._review(request, pk, services.cancel_leave_application)


class LeaveBalanceView(APIView):
    def get(self, request):
        year = parse_int_param(request, "year")
        if year is None:
            year = timezone.localdate().year
        employee_id = parse_int_param(request, "employee")
        return Response(services.get_leave_balances(year=year, employee_id=employee_id))
