from django.shortcuts import render
from django.db.models import Avg, Q, F, FloatField, ExpressionWrapper

from home.models import Municipio


def metodologia_page(request):
    """Página de storytelling da metodologia do IFEM (scroll narrativo com GSAP).

    Passa números REAIS (média nacional e distribuição de municípios por faixa
    populacional) para a página exibir dados oficiais, não ilustrativos.
    """
    media = Municipio.objects.filter(rc_24_pc__isnull=False).aggregate(m=Avg('rc_24_pc'))['m'] or 0
    pop_qs = Municipio.objects.filter(populacao24__isnull=False)

    # Quantidade real de municípios por faixa de porte (a altura da barra reflete
    # a CONTAGEM — por isso as faixas pequenas dominam, como na realidade brasileira).
    faixas_def = [
        ('Até 5 mil', 0, 5000), ('5 a 10 mil', 5000, 10000),
        ('10 a 20 mil', 10000, 20000), ('20 a 50 mil', 20000, 50000),
        ('50 a 100 mil', 50000, 100000), ('100 a 200 mil', 100000, 200000),
        ('200 a 500 mil', 200000, 500000), ('+500 mil', 500000, None),
    ]
    faixas, counts = [], []
    for label, lo, hi in faixas_def:
        cond = Q(populacao24__gte=lo) & (Q(populacao24__lt=hi) if hi else Q())
        c = pop_qs.filter(cond).count()
        counts.append(c)
        faixas.append({'label': label, 'count': c})
    mx = max(counts) or 1
    for item in faixas:
        item['h'] = max(6, round(item['count'] / mx * 130))  # altura proporcional (px)

    total = sum(counts) or 1
    abaixo = pop_qs.filter(populacao24__lte=80000).count()
    acima = total - abaixo

    # Médias nacionais dos indicadores sociais (média dos municípios).
    media_sus = pop_qs.filter(sus_dependente__isnull=False).aggregate(m=Avg('sus_dependente'))['m'] or 0
    media_cad = pop_qs.filter(cadunico__isnull=False, populacao24__gt=0).annotate(
        pct=ExpressionWrapper(F('cadunico') * 100.0 / F('populacao24'), output_field=FloatField())
    ).aggregate(m=Avg('pct'))['m'] or 0

    ctx = {
        'media_nacional': str(round(media)),
        'faixas': faixas,
        'abaixo80': abaixo,
        'acima80': acima,
        'pct_abaixo80': round(abaixo / total * 100),
        'pct_acima80': round(acima / total * 100),
        'media_sus': round(media_sus),
        'media_cad': round(media_cad),
    }
    return render(request, 'metodologia/metodologia.html', ctx)
