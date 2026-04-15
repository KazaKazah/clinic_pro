from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie



@ensure_csrf_cookie
def stock_dashboard_page(request):
    return render(request, "inventory/stock_dashboard.html")