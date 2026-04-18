from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from config.views import dashboard_page


urlpatterns = [
    path("admin/", admin.site.urls),

    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("", dashboard_page, name="dashboard_page"),
    path("", include("patients.urls_pages")),
    path("", include("outpatient.urls_pages")),
]
