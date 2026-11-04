"""Testes da API de indicadores para o Sistema FNP (/api/sistema-fnp/indicadores-municipais/).

Dados sintéticos. Cobre: desligada sem token configurado, recusa sem token ou
com token errado, resposta completa com o token certo, município sem os dados
relacionados e o filtro ``?ibge=``.

Rodar com: python manage.py test home.tests_api_sistema
"""
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from home.models import AdaptaBrasil, IndicadoresAtuais, Municipio

TOKEN = 'token-de-teste-123'


class ApiSistemaFnpTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.com_dados = Municipio.objects.create(
            cod_ibge='1111111', name_muni='Cidade Ficticia', name_muni_uf='Cidade Ficticia - SP',
            uf='SP', regiao='Sudeste')
        IndicadoresAtuais.objects.create(
            municipio=cls.com_dados, populacao_atual=120000, rc_atual_pc=3000.0,
            quintil_atual='2º quintil', capag='B')
        AdaptaBrasil.objects.create(municipio=cls.com_dados, media_ponderada=0.7)
        cls.sem_dados = Municipio.objects.create(
            cod_ibge='2222222', name_muni='Vila Modelo', name_muni_uf='Vila Modelo - MG',
            uf='MG', regiao='Sudeste')

    def _get(self, token=None, **params):
        cabecalhos = {'HTTP_AUTHORIZATION': f'Bearer {token}'} if token else {}
        return self.client.get(reverse('api_sistema_indicadores_municipais'), params, **cabecalhos)

    def test_desligada_sem_token_configurado(self):
        with mock.patch.dict('os.environ', {'IFEM_API_TOKEN': ''}):
            self.assertEqual(self._get(token=TOKEN).status_code, 503)

    @mock.patch.dict('os.environ', {'IFEM_API_TOKEN': TOKEN})
    def test_recusa_sem_token_ou_errado(self):
        self.assertEqual(self._get().status_code, 401)
        self.assertEqual(self._get(token='errado').status_code, 401)

    @mock.patch.dict('os.environ', {'IFEM_API_TOKEN': TOKEN})
    def test_resposta_completa(self):
        resposta = self._get(token=TOKEN)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta['Cache-Control'], 'no-store')
        dados = resposta.json()
        self.assertEqual(dados['versao'], 1)
        self.assertEqual(dados['total'], 2)
        primeiro, segundo = dados['municipios']
        self.assertEqual(primeiro['ibge'], '1111111')
        self.assertEqual(primeiro['atuais']['capag'], 'B')
        self.assertEqual(primeiro['atuais']['quintil_atual'], '2º quintil')
        self.assertEqual(primeiro['adapta_brasil']['media_ponderada'], 0.7)
        self.assertIsNone(primeiro['sus_dependente'])
        # Município sem registros relacionados vem com None, sem erro.
        self.assertIsNone(segundo['atuais'])
        self.assertIsNone(segundo['adapta_brasil'])

    @mock.patch.dict('os.environ', {'IFEM_API_TOKEN': TOKEN})
    def test_filtro_por_ibge(self):
        dados = self._get(token=TOKEN, ibge='2222222').json()
        self.assertEqual([m['ibge'] for m in dados['municipios']], ['2222222'])
        self.assertEqual(self._get(token=TOKEN, ibge='abc').status_code, 400)

    @mock.patch.dict('os.environ', {'IFEM_API_TOKEN': TOKEN})
    def test_so_get(self):
        resposta = self.client.post(reverse('api_sistema_indicadores_municipais'),
                                    HTTP_AUTHORIZATION=f'Bearer {TOKEN}')
        self.assertEqual(resposta.status_code, 405)
