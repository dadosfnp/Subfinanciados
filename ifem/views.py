from django.shortcuts import render

# [NOVO] View simples para renderizar a Landing Page
def landing_page(request):
    return render(request, 'ifem/index.html')