# -*- coding: utf-8 -*-
"""Importa os consórcios intermunicipais e associa os municípios que os compõem.

A planilha (base_datas/consorcios.xlsx) é a fonte da verdade: o nome que estiver na
coluna `consorcio` é exatamente o que aparece no filtro "Agrupamento" das telas de
gráficos, mapa e análise agregada. Não há normalização de nome aqui de propósito —
mudar o rótulo exibido é editar a planilha, não o código.

Idempotente: recarrega a composição inteira de cada consórcio a cada execução
(`.set()`), então rodar duas vezes dá o mesmo resultado e municípios removidos da
planilha saem da associação.
"""
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction

from home.models import Consorcio, Municipio

# Barra normal, nunca invertida: em Linux (o container de produção) a barra invertida
# vira parte literal do nome do arquivo. Os demais comandos de import usam este formato.
CAMINHO_PLANILHA = 'base_datas/consorcios.xlsx'


class Command(BaseCommand):
    help = 'Lê base_datas/consorcios.xlsx e associa os municípios aos seus consórcios'

    def handle(self, *args, **options):
        self.stdout.write(f'Lendo o arquivo: {CAMINHO_PLANILHA}')

        # dtype=str no código IBGE: sem isso o pandas lê como int e perde o zero à
        # esquerda dos municípios do Norte/Nordeste (ex.: 1100015 sobrevive, mas o
        # formato de 7 dígitos é o que casa com a PK de Municipio, que é CharField).
        try:
            df = pd.read_excel(CAMINHO_PLANILHA, dtype={'cod_ibge': str})
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(
                f'Planilha não encontrada em {CAMINHO_PLANILHA}. '
                'Ela é versionada no repositório — confira se o arquivo veio no deploy.'
            ))
            raise

        colunas_esperadas = {'cod_ibge', 'consorcio'}
        faltando = colunas_esperadas - set(df.columns)
        if faltando:
            raise ValueError(
                f'Planilha {CAMINHO_PLANILHA} sem as colunas {sorted(faltando)}. '
                f'Colunas encontradas: {list(df.columns)}'
            )

        df['cod_ibge'] = df['cod_ibge'].astype(str).str.strip().str.zfill(7)
        df['consorcio'] = df['consorcio'].astype(str).str.strip()

        nao_encontrados = []
        total_associados = 0

        # Uma transação para a carga inteira: um erro no meio deixaria consórcios com
        # composição parcial, que é pior do que nenhum consórcio — o filtro apareceria
        # na tela mostrando um agregado errado, sem nenhum sinal de falha.
        with transaction.atomic():
            for nome_consorcio, grupo in df.groupby('consorcio', sort=True):
                consorcio, criado = Consorcio.objects.get_or_create(nome=nome_consorcio)

                codigos = grupo['cod_ibge'].tolist()
                municipios = list(Municipio.objects.filter(cod_ibge__in=codigos))

                encontrados = {m.cod_ibge for m in municipios}
                for cod in codigos:
                    if cod not in encontrados:
                        nao_encontrados.append((nome_consorcio, cod))

                consorcio.municipios.set(municipios)
                total_associados += len(municipios)

                marca = 'criado' if criado else 'atualizado'
                self.stdout.write(f'  {nome_consorcio}: {len(municipios)} município(s) [{marca}]')

        for nome_consorcio, cod in nao_encontrados:
            # Warning e não erro: um município fora da base (fusão, código antigo) não
            # invalida o resto do consórcio, mas precisa aparecer no log do deploy.
            self.stdout.write(self.style.WARNING(
                f'Município {cod} ({nome_consorcio}) não existe na base — ignorado.'
            ))

        self.stdout.write(self.style.SUCCESS(
            f'Consórcios importados: {Consorcio.objects.count()} '
            f'({total_associados} associações de município).'
        ))
