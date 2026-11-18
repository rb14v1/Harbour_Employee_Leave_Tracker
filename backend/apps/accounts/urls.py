from django.urls import path

from .views import AuthConfigView, DemoLoginView, LoginView, LogoutView, MeView, RefreshView

urlpatterns = [
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("config/", AuthConfigView.as_view(), name="auth-config"),
    path("demo-login/", DemoLoginView.as_view(), name="auth-demo-login"),
]
