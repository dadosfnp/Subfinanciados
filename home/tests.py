"""Testes do endpoint de filtros dependentes (/api/get-dependent-filters/).

Cobre os dois comportamentos que dependem de lógica própria e quebrariam em silêncio:

1. cada select lista as opções da sua dimensão sem se fechar sobre a própria
   seleção — o bug que obrigava o usuário a passar por "Todas" para trocar de UF;
2. o filtro de Agrupamento (consórcio), que é muitos-para-muitos e por isso não
   segue o mesmo caminho de ORM da Região Metropolitana.

Os dados são sintéticos de propósito: as planilhas de base_datas/ mudam a cada
atualização anual e um teste ancorado nelas passaria a falhar por motivo errado.

Rodar com: python manage.py test home
"""
import json

from django.test import TestCase
from django.urls import reverse

from home.models import Consorcio, IndicadoresAtuais, Municipio, RegiaoMetropolitana


class FiltrosDependentesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.rm_recife = RegiaoMetropolitana.objects.create(nome='RM do Recife')
        cls.rm_sp = RegiaoMetropolitana.objects.create(nome='RM de São Paulo')

        cls.recife = cls._municipio('2611606', 'Recife', 'PE', 'Nordeste', rm=cls.rm_recife,
                                    populacao=1500000, receita_pc=3000.0)
        cls.olinda = cls._municipio('2609600', 'Olinda', 'PE', 'Nordeste', rm=cls.rm_recife,
                                    populacao=390000, receita_pc=1500.0)
        cls.santo_andre = cls._municipio('3547809', 'Santo André', 'SP', 'Sudeste', rm=cls.rm_sp,
                                         populacao=750000, receita_pc=4000.0)
        cls.diadema = cls._municipio('3513801', 'Diadema', 'SP', 'Sudeste', rm=cls.rm_sp,
                                     populacao=390000, receita_pc=2500.0)
        cls.curitiba = cls._municipio('4106902', 'Curitiba', 'PR', 'Sul', rm=None,
                                      populacao=1770000, receita_pc=5000.0)

        cls.grande_abc = Consorcio.objects.create(nome='Grande ABC')
        cls.grande_abc.municipios.set([cls.santo_andre, cls.diadema])

        cls.assomec = Consorcio.objects.create(nome='ASSOMEC')
        cls.assomec.municipios.set([cls.curitiba])

    @staticmethod
    def _municipio(cod_ibge, nome, uf, regiao, rm, populacao, receita_pc):
        municipio = Municipio.objects.create(
            cod_ibge=cod_ibge,
            name_muni=nome,
            name_muni_uf=f'{nome} - {uf}',
            uf=uf,
            regiao=regiao,
            rm=rm,
        )
        IndicadoresAtuais.objects.create(
            municipio=municipio,
            populacao_atual=populacao,
            rc_atual=receita_pc * populacao,
            rc_atual_pc=receita_pc,
            quintil_atual='3º quintil',
            capag='B',
        )
        return municipio

    def filtros(self, **params):
        resposta = self.client.get(reverse('api_get_dependent_filters'), params)
        self.assertEqual(resposta.status_code, 200)
        return json.loads(resposta.content)

    # ---- 1. o select não se fecha sobre a própria seleção ----

    def test_uf_selecionada_nao_reduz_a_lista_de_ufs(self):
        """Com UF=PE, o select de UF continua oferecendo as outras UFs."""
        dados = self.filtros(uf='PE')
        self.assertEqual(dados['ufs'], ['PE', 'PR', 'SP'])

    def test_rm_selecionada_nao_reduz_a_lista_de_rms(self):
        dados = self.filtros(rm='RM do Recife')
        self.assertEqual(dados['rms'], ['RM de São Paulo', 'RM do Recife'])

    def test_agrupamento_selecionado_nao_reduz_a_lista_de_agrupamentos(self):
        dados = self.filtros(consorcio='Grande ABC')
        self.assertEqual(dados['consorcios'], ['ASSOMEC', 'Grande ABC'])

    def test_uf_selecionada_restringe_as_demais_dimensoes(self):
        """A cascata útil continua valendo: UF=PE só lista o que existe em PE."""
        dados = self.filtros(uf='PE')
        self.assertEqual(dados['municipios'], ['Olinda - PE', 'Recife - PE'])
        self.assertEqual(dados['rms'], ['RM do Recife'])
        self.assertEqual(dados['regioes'], ['Nordeste'])
        self.assertEqual(dados['consorcios'], [])

    def test_regiao_e_uf_combinadas(self):
        """Filtros de dimensões diferentes se somam; o da própria dimensão, não."""
        dados = self.filtros(uf='PE', regiao='Nordeste')
        self.assertEqual(dados['ufs'], ['PE'])  # só PE é do Nordeste nesta base
        self.assertEqual(dados['municipios'], ['Olinda - PE', 'Recife - PE'])

    # ---- 2. filtro de Agrupamento (consórcio) ----

    def test_agrupamento_restringe_aos_municipios_do_consorcio(self):
        dados = self.filtros(consorcio='Grande ABC')
        self.assertEqual(dados['municipios'], ['Diadema - SP', 'Santo André - SP'])
        self.assertEqual(dados['ufs'], ['SP'])

    def test_lista_de_agrupamentos_respeita_a_uf_selecionada(self):
        self.assertEqual(self.filtros(uf='PR')['consorcios'], ['ASSOMEC'])
        self.assertEqual(self.filtros(uf='SP')['consorcios'], ['Grande ABC'])

    def test_agrupamento_incompativel_com_a_uf_devolve_lista_vazia(self):
        dados = self.filtros(consorcio='Grande ABC', uf='PE')
        self.assertEqual(dados['municipios'], [])

    def test_municipio_em_dois_agrupamentos_aparece_uma_vez_so(self):
        """A relação é M2M: o município pode estar em vários consórcios sem duplicar."""
        outro = Consorcio.objects.create(nome='Consórcio de Saúde')
        outro.municipios.add(self.diadema)

        dados = self.filtros(consorcio='Consórcio de Saúde')
        self.assertEqual(dados['municipios'], ['Diadema - SP'])

        dados = self.filtros(uf='SP')
        self.assertEqual(dados['municipios'], ['Diadema - SP', 'Santo André - SP'])
        self.assertEqual(dados['consorcios'], ['Consórcio de Saúde', 'Grande ABC'])

    def test_sem_filtro_lista_tudo(self):
        dados = self.filtros()
        self.assertEqual(len(dados['municipios']), 5)
        self.assertEqual(dados['ufs'], ['PE', 'PR', 'SP'])
        self.assertEqual(dados['consorcios'], ['ASSOMEC', 'Grande ABC'])

    def test_valor_todos_equivale_a_sem_filtro(self):
        self.assertEqual(self.filtros(uf='todos', consorcio='todos'), self.filtros())


class FiltroDeAgrupamentoNasTelasTests(TestCase):
    """O mesmo parâmetro `consorcio` precisa valer nas três telas."""

    @classmethod
    def setUpTestData(cls):
        cls.municipio = FiltrosDependentesTests._municipio(
            '3547809', 'Santo André', 'SP', 'Sudeste', rm=None,
            populacao=750000, receita_pc=4000.0,
        )
        FiltrosDependentesTests._municipio(
            '4106902', 'Curitiba', 'PR', 'Sul', rm=None,
            populacao=1770000, receita_pc=5000.0,
        )
        consorcio = Consorcio.objects.create(nome='Grande ABC')
        consorcio.municipios.add(cls.municipio)

    def test_mapa_devolve_apenas_os_municipios_do_agrupamento(self):
        resposta = self.client.get('/api/dados-municipios/', {'consorcio': 'Grande ABC'})
        self.assertEqual(resposta.status_code, 200)
        geojson = json.loads(resposta.content)
        nomes = [f['properties']['name_muni'] for f in geojson['features']]
        self.assertEqual(nomes, ['Santo André'])

    def test_kpis_da_analise_agregada_consideram_o_agrupamento(self):
        resposta = self.client.get('/api/dados-detalhados/', {'consorcio': 'Grande ABC'})
        self.assertEqual(resposta.status_code, 200)
        kpis = json.loads(resposta.content)['kpis']
        self.assertEqual(kpis['quantidade'], 1)
        self.assertEqual(kpis['populacao'], 750000)

    def test_dashboard_dos_graficos_aceita_o_agrupamento(self):
        resposta = self.client.get('/api/dashboard-data/', {'consorcio': 'Grande ABC'})
        self.assertEqual(resposta.status_code, 200)
