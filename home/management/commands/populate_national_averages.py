from django.core.management.base import BaseCommand
from django.db.models import Avg, F, ExpressionWrapper, FloatField, Q
from home.models import Municipio, MediaNacionalReceita

class Command(BaseCommand):
    help = 'Calcula e popula TODAS as médias nacionais per capita para o dashboard'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando cálculo massivo de médias nacionais (Ano 2024)...")

        # MAPEAMENTO COMPLETO DE TODOS OS NÍVEIS (1, 2 e 3)
        mapping = {
            # Nível 1 - Conta Detalhada
            'imposto_taxas_contribuicoes': 'conta_detalhada__imposto_taxas_contribuicoes',
            'contribuicoes': 'conta_detalhada__contribuicoes',
            'transferencias_correntes': 'conta_detalhada__transferencias_correntes',
            'outras_receita': 'conta_detalhada__outras_receita',

            # Nível 2 - Conta Especifica (Atenção: 'tranferencias' sem o 's' conforme seu model)
            'imposto': 'conta_especifica__imposto',
            'taxas': 'conta_especifica__taxas',
            'contribuicoes_melhoria': 'conta_especifica__contribuicoes_melhoria',
            'contribuicoes_sociais': 'conta_especifica__contribuicoes_sociais',
            'contribuicoes_iluminacao_publica': 'conta_especifica__contribuicoes_iluminacao_publica',
            'outras_contribuicoes': 'conta_especifica__outras_contribuicoes',
            'tranferencias_uniao': 'conta_especifica__tranferencias_uniao',
            'tranferencias_estados': 'conta_especifica__tranferencias_estados',
            'outras_tranferencias': 'conta_especifica__outras_tranferencias',
            'receita_patrimonial': 'conta_especifica__receita_patrimonial',
            'receita_agropecuaria': 'conta_especifica__receita_agropecuaria',
            'receita_industrial': 'conta_especifica__receita_industrial',
            'receita_servicos': 'conta_especifica__receita_servicos',
            'outras_receitas': 'conta_especifica__outras_receitas',

            # Nível 3 - Conta Mais Especifica (Atenção aos nomes iptu, itbi, iss...)
            'iptu': 'conta_mais_especifica__iptu',
            'itbi': 'conta_mais_especifica__itbi',
            'iss': 'conta_mais_especifica__iss',
            'imposto_renda': 'conta_mais_especifica__imposto_renda',
            'outros_impostos': 'conta_mais_especifica__outros_impostos',
            'taxa_policia': 'conta_mais_especifica__taxa_policia',
            'taxa_prestacao_servico': 'conta_mais_especifica__taxa_prestacao_servico',
            'outras_taxas': 'conta_mais_especifica__outras_taxas',
            'contribuicao_melhoria_pavimento_obras': 'conta_mais_especifica__contribuicao_melhoria_pavimento_obras',
            'contribuicao_melhoria_agua_potavel': 'conta_mais_especifica__contribuicao_melhoria_agua_potavel',
            'contribuicao_melhoria_iluminacao_publica': 'conta_mais_especifica__contribuicao_melhoria_iluminacao_publica',
            'outras_contribuicoes_melhoria': 'conta_mais_especifica__outras_contribuicoes_melhoria',
            'transferencia_uniao_fpm': 'conta_mais_especifica__transferencia_uniao_fpm',
            'transferencia_uniao_exploracao': 'conta_mais_especifica__transferencia_uniao_exploracao',
            'transferencia_uniao_sus': 'conta_mais_especifica__transferencia_uniao_sus',
            'transferencia_uniao_fnde': 'conta_mais_especifica__transferencia_uniao_fnde',
            'transferencia_uniao_fundeb': 'conta_mais_especifica__transferencia_uniao_fundeb',
            'transferencia_uniao_fnas': 'conta_mais_especifica__transferencia_uniao_fnas',
            'outras_transferencias_uniao': 'conta_mais_especifica__outras_transferencias_uniao',
            'transferencia_estado_icms': 'conta_mais_especifica__transferencia_estado_icms',
            'transferencia_estado_ipva': 'conta_mais_especifica__transferencia_estado_ipva',
            'transferencia_estado_exploracao': 'conta_mais_especifica__transferencia_estado_exploracao',
            'transferencia_estado_sus': 'conta_mais_especifica__transferencia_estado_sus',
            'transferencia_estado_assistencia': 'conta_mais_especifica__transferencia_estado_assistencia',
            'outras_transferencias_estado': 'conta_mais_especifica__outras_transferencias_estado',
        }

        defaults_data = {}
        for field, path in mapping.items():
            # Filtro robusto para garantir médias reais (ignorando nulos e zeros)
            qs = Municipio.objects.filter(populacao24__gt=0).filter(Q(**{f"{path}__gt": 0})).annotate(
                pc=ExpressionWrapper(F(path) / F('populacao24'), output_field=FloatField())
            )
            val = qs.aggregate(avg=Avg('pc'))['avg'] or 0
            defaults_data[field] = val
            self.stdout.write(f"Sincronizado: {field} -> R$ {val:.2f}")

        MediaNacionalReceita.objects.update_or_create(
            ano_referencia=2024,
            defaults=defaults_data
        )
        self.stdout.write(self.style.SUCCESS("\nSucesso! Todas as rubricas de 2024 foram atualizadas no banco."))