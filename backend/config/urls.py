from django.contrib import admin
from django.urls import include, path

from common.views import HealthView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", HealthView.as_view(), name="health"),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.employees.urls")),
    path("api/", include("apps.leaves.urls")),
    path("api/", include("apps.dashboard.urls")),
]
