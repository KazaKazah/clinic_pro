from django.contrib import admin
from django.urls import path, include
from inpatient.views_pages import nurse_daily_sheet_page
from billing.views import ServiceViewSet
from inventory.views_pages import stock_dashboard_page

urlpatterns = [
    path('admin/', admin.site.urls),

    #
    path('api/', include('patients.urls')),
    path('api/', include('outpatient.urls')),
    path('api/', include('inpatient.urls')),
    path("api/", include("inventory.urls")),
    path('api/', include('billing.urls')),

     #
    path('daily-sheet/', nurse_daily_sheet_page, name='daily_sheet_page'),  
    path("stock/", stock_dashboard_page, name="stock_dashboard_page"), 
    
]
