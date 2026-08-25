"""Testes do cache do GeoJSON do mapa.

O modo de falha que estes testes cobrem é silencioso e caro: se um filtro novo
não entrar em `_PARAMS_RELEVANTES_MAPA`, a chave de cache passa a ignorá-lo e o
mapa serve a resposta de OUTRO recorte — sem erro, sem log, com o número de
municípios errado na tela. Foi o risco real ao adicionar o filtro Agrupamento.

Rodar com: python manage.py test map
"""
import json

from django.core.cache import caches
from django.test import TestCase

from home.models import Consorcio, IndicadoresAtuais, Municipio


class CacheDoMapaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.santo_andre = cls._municipio('3547809', 'Santo André', 'SP', 'Sudeste', 750000, 4000.0)
        cls.curitiba = cls._municipio('4106902', 'Curitiba', 'PR', 'Sul', 1770000, 5000.0)
        cls.recife = cls._municipio('2611606', 'Recife', 'PE', 'Nordeste', 1500000, 3000.0)

        cls.grande_abc = Consorcio.objects.create(nome='Grande ABC')
        cls.grande_abc.municipios.add(cls.santo_andre)

    @staticmethod
    def _municipio(cod_ibge, nome, uf, regiao, populacao, receita_pc):
        municipio = Municipio.objects.create(
            cod_ibge=cod_ibge,
            name_muni=nome,
            name_muni_uf=f'{nome} - {uf}',
            uf=uf,
            regiao=regiao,
            coordx=-46.5,
            coordy=-23.6,
        )
        IndicadoresAtuais.objects.create(
            municipio=municipio,
            populacao_atual=populacao,
            rc_atual=receita_pc * populacao,
            rc_atual_pc=receita_pc,
            quintil_atual='3º quintil',
        )
        return municipio

    def setUp(self):
        # O cache do mapa é LocMemCache e sobrevive entre testes do mesmo processo:
        # sem limpar, o primeiro teste envenena os seguintes.
        caches['mapa'].clear()

    def municipios_no_mapa(self, **params):
        resposta = self.client.get('/api/dados-municipios/', params)
        self.assertEqual(resposta.status_code, 200)
        geojson = json.loads(resposta.content)
        return sorted(f['properties']['name_muni'] for f in geojson['features'])

    def test_cache_nao_confunde_recortes_de_agrupamento(self):
        """Requisitar sem filtro antes não pode contaminar a resposta filtrada."""
        self.assertEqual(len(self.municipios_no_mapa()), 3)
        self.assertEqual(self.municipios_no_mapa(consorcio='Grande ABC'), ['Santo André'])
        # E o caminho inverso: a resposta filtrada não vira a resposta geral.
        self.assertEqual(len(self.municipios_no_mapa()), 3)

    def test_agrupamentos_diferentes_geram_entradas_diferentes(self):
        outro = Consorcio.objects.create(nome='ASSOMEC')
        outro.municipios.add(self.curitiba)

        self.assertEqual(self.municipios_no_mapa(consorcio='Grande ABC'), ['Santo André'])
        self.assertEqual(self.municipios_no_mapa(consorcio='ASSOMEC'), ['Curitiba'])

    def test_segunda_requisicao_identica_vem_do_cache(self):
        primeira = self.client.get('/api/dados-municipios/', {'consorcio': 'Grande ABC'})
        with self.assertNumQueries(0):
            segunda = self.client.get('/api/dados-municipios/', {'consorcio': 'Grande ABC'})
        self.assertEqual(primeira.content, segunda.content)

    def test_etag_muda_quando_o_agrupamento_muda(self):
        etag_geral = self.client.get('/api/dados-municipios/')['ETag']
        etag_abc = self.client.get('/api/dados-municipios/', {'consorcio': 'Grande ABC'})['ETag']
        self.assertNotEqual(etag_geral, etag_abc)
