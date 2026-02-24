from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Avg
from home.models import Municipio

def landing_page(request):
    return render(request, 'ifem/index.html')

def busca_municipio_simples_api(request):
    """
    Endpoint otimizado para o autocomplete da Landing Page do IFEM.
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 3:
        return JsonResponse({'results': [], 'national_avg': 0})

    # Busca até 10 municípios que contenham o termo digitado
    qs = Municipio.objects.filter(name_muni_uf__icontains=query).order_by('name_muni_uf')[:10]
    
    # Média nacional de Receita per Capita
    national_avg = Municipio.objects.aggregate(avg_rc=Avg('rc_24_pc'))['avg_rc'] or 0

    results = []
    for m in qs:
            results.append({
                'nome': m.name_muni_uf,
                'rc_pc': float(m.rc_24_pc or 0),
                'quintil': str(m.quintil24) if m.quintil24 else "",
                'decil': str(m.decil24) if m.decil24 else "",
            })

    return JsonResponse({
            'national_avg': float(national_avg),
            'results': results
        })