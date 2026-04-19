from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from config.views import dashboard_page

admin.site.site_header = "Администрирование клиники"
admin.site.site_title = "Клиника"
admin.site.index_title = "Панель управления"


urlpatterns = [
    path("admin/", admin.site.urls),

    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("", dashboard_page, name="dashboard_page"),
    path("", include("patients.urls_pages")),
    path("", include("outpatient.urls_pages")),
]
