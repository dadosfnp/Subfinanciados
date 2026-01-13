from django.shortcuts import render

def ifem_landing(request):
    """Renderiza a página de abertura do IFEM."""
    return render(request, "ifem/ifem.html")
