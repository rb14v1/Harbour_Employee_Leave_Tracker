from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import LeaveApplicationViewSet, LeaveBalanceView, LeaveTypeViewSet

router = SimpleRouter()
router.register("leave-types", LeaveTypeViewSet, basename="leave-type")
router.register("leaves", LeaveApplicationViewSet, basename="leave")

urlpatterns = router.urls + [
    path("leave-balances/", LeaveBalanceView.as_view(), name="leave-balances"),
]
