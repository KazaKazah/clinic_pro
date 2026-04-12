from django.shortcuts import render
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

def nurse_daily_sheet_page(request):
    return render(request, 'nurse/daily_sheet.html')


@ensure_csrf_cookie
def nurse_daily_sheet_page(request):
    return render(request, 'nurse/daily_sheet.html')