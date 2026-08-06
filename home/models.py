from django.db import models
import uuid


class RegiaoMetropolitana(models.Model):
    nome = models.CharField(max_length=255, unique=True, help_text="Nome único da Região Metropolitana")

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Região Metropolitana"
        verbose_name_plural = "Regiões Metropolitanas"

class Percentis(models.Model):
    percentil = models.IntegerField(unique=True, help_text="Valor do percentil (0-100)")
    valor = models.FloatField()

    def __str__(self):
        return f"{self.percentil}º Percentil"


class Municipio(models.Model):
    # Chave primária natural
    cod_ibge = models.CharField(max_length=7, primary_key=True)
    name_muni = models.CharField(max_length=255)
    name_muni_uf = models.CharField(max_length=255)
    uf = models.CharField(max_length=2, db_index=True)
    coordx = models.FloatField(null=True, blank=True)
    coordy = models.FloatField(null=True, blank=True)
    regiao = models.CharField(max_length=255, db_index=True)
    rm = models.ForeignKey(
        'RegiaoMetropolitana', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='municipios'
    )

    def __str__(self):
        return f"{self.name_muni} ({self.uf})"

    # ---- Propriedades de compatibilidade: dados atuais (IndicadoresAtuais) ----
    def _da(self):
        """Retorna dados_atuais ou None sem gerar exceção."""
        try:
            return self.dados_atuais
        except Exception:
            return None

    def _d2(self):
        """Retorna dados_2000 ou None sem gerar exceção."""
        try:
            return self.dados_2000
        except Exception:
            return None

    @property
    def populacao24(self):
        da = self._da()
        return da.populacao_atual if da else None

    @property
    def populacao24_rank_nacional(self):
        da = self._da()
        return da.populacao_atual_rank_nacional if da else None

    @property
    def populacao24_total_nacional(self):
        da = self._da()
        return da.populacao_atual_total_nacional if da else None

    @property
    def populacao24_rank_estadual(self):
        da = self._da()
        return da.populacao_atual_rank_estadual if da else None

    @property
    def populacao24_total_estadual(self):
        da = self._da()
        return da.populacao_atual_total_estadual if da else None

    @property
    def populacao24_rank_faixa(self):
        da = self._da()
        return da.populacao_atual_rank_faixa if da else None

    @property
    def populacao24_total_faixa(self):
        da = self._da()
        return da.populacao_atual_total_faixa if da else None

    @property
    def rc_24_pc(self):
        da = self._da()
        return da.rc_atual_pc if da else None

    @property
    def rc_2024(self):
        da = self._da()
        return da.rc_atual if da else None

    @property
    def quintil24(self):
        da = self._da()
        return da.quintil_atual if da else None

    @property
    def decil24(self):
        da = self._da()
        return da.decil_atual if da else None

    @property
    def percentil24_n(self):
        da = self._da()
        return da.percentil_atual_n if da else None

    @property
    def percentil24(self):
        da = self._da()
        return da.percentil_atual if da else None

    @property
    def rank_nacional(self):
        da = self._da()
        return da.rank_nacional if da else None

    @property
    def total_nacional(self):
        da = self._da()
        return da.total_nacional if da else None

    @property
    def rank_estadual(self):
        da = self._da()
        return da.rank_estadual if da else None

    @property
    def total_estadual(self):
        da = self._da()
        return da.total_estadual if da else None

    @property
    def rank_faixa(self):
        da = self._da()
        return da.rank_faixa if da else None

    @property
    def total_faixa(self):
        da = self._da()
        return da.total_faixa if da else None

    # ---- Propriedades de compatibilidade: dados 2000 (Indicadores2000) ----
    @property
    def populacao00(self):
        d2 = self._d2()
        return d2.populacao_00 if d2 else None

    @property
    def rc_00_pc(self):
        d2 = self._d2()
        return d2.rc_00_pc if d2 else None

    @property
    def rc_2000(self):
        d2 = self._d2()
        return d2.rc_00 if d2 else None

    @property
    def quintil00(self):
        d2 = self._d2()
        return d2.quintil_00 if d2 else None

    @property
    def decil00(self):
        d2 = self._d2()
        return d2.decil_00 if d2 else None

    @property
    def percentil00_n(self):
        d2 = self._d2()
        return d2.percentil_00_n if d2 else None

    @property
    def rank_nacional_00(self):
        d2 = self._d2()
        return d2.rank_nacional_00 if d2 else None

    @property
    def total_nacional_00(self):
        d2 = self._d2()
        return d2.total_nacional_00 if d2 else None


class Indicadores2000(models.Model):
    municipio = models.OneToOneField(
        Municipio,
        on_delete=models.CASCADE,
        primary_key=True, 
        related_name='dados_2000'
    )
    populacao_00 = models.IntegerField(null=True, blank=True)
    rc_00 = models.FloatField(null=True, blank=True)
    rc_00_pc = models.FloatField(null=True, blank=True)
    quintil_00 = models.CharField(max_length=50, null=True, blank=True)
    decil_00 = models.CharField(max_length=50, null=True, blank=True)
    percentil_00 = models.CharField(max_length=50, null=True, blank=True)
    percentil_00_n = models.IntegerField(null=True, blank=True)
    rank_nacional_00 = models.IntegerField(null=True, blank=True)
    total_nacional_00 = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Dados 2000 - {self.municipio.name_muni}"

class SusDependente(models.Model):
    municipio = models.OneToOneField(
        Municipio,
        on_delete=models.CASCADE,
        primary_key=True, 
        related_name='sus_dependente'
    )
    sus_dependente = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Dependência SUS - {self.municipio.name_muni}"

class AdaptaBrasil(models.Model):
    municipio = models.OneToOneField(
        Municipio,
        on_delete=models.CASCADE,
        primary_key=True, 
        related_name='dados_adapta_brasil'
    )
    bio_int_bio = models.FloatField(null=True, blank=True)
    des_des_ter = models.FloatField(null=True, blank=True)
    des_in_enx_ala = models.FloatField(null=True, blank=True)
    rec_ris_est_hid = models.FloatField(null=True, blank=True)
    sau_arb = models.FloatField(null=True, blank=True)
    sau_lei_teg_ame = models.FloatField(null=True, blank=True)
    sau_lei_vis = models.FloatField(null=True, blank=True)
    sau_mal = models.FloatField(null=True, blank=True)
    seg_ali_ace_con_ali = models.FloatField(null=True, blank=True)
    seg_ali_dis = models.FloatField(null=True, blank=True)
    seg_ene_ace = models.FloatField(null=True, blank=True)
    seg_ene_dis = models.FloatField(null=True, blank=True)
    def __str__(self):
        return f"Dados AdaptaBrasil - {self.municipio.name_muni}"

class Cadunico(models.Model):
    municipio = models.OneToOneField(
        Municipio,
        on_delete=models.CASCADE,
        primary_key=True, 
        related_name='cadunico'
    )
    cadunico = models.IntegerField(null=True, blank=True)
    cadunico_rank_nacional = models.IntegerField(null=True, blank=True)
    cadunico_total_nacional = models.IntegerField(null=True, blank=True)
    cadunico_rank_estadual = models.IntegerField(null=True, blank=True)
    cadunico_total_estadual = models.IntegerField(null=True, blank=True)
    cadunico_rank_faixa = models.IntegerField(null=True, blank=True)
    cadunico_total_faixa = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"CadÚnico - {self.municipio.name_muni}"

class IndicadoresAtuais(models.Model):
    municipio = models.OneToOneField(
        Municipio,
        on_delete=models.CASCADE,
        primary_key=True, 
        related_name='dados_atuais'
    )
    populacao_atual = models.IntegerField(null=True, db_index=True)
    populacao_atual_rank_nacional = models.IntegerField(null=True, blank=True)
    populacao_atual_total_nacional = models.IntegerField(null=True, blank=True)
    populacao_atual_rank_estadual = models.IntegerField(null=True, blank=True)
    populacao_atual_total_estadual = models.IntegerField(null=True, blank=True)
    populacao_atual_rank_faixa = models.IntegerField(null=True, blank=True)
    populacao_atual_total_faixa = models.IntegerField(null=True, blank=True)
    capag = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    rc_atual = models.FloatField(null=True, blank=True)
    rc_atual_pc = models.FloatField(null=True, blank=True, db_index=True)
    quintil_atual = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    decil_atual = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    percentil_atual = models.CharField(max_length=50, null=True, blank=True)
    percentil_atual_n = models.IntegerField(null=True, blank=True)
    rank_nacional = models.IntegerField(null=True, blank=True)
    total_nacional = models.IntegerField(null=True, blank=True)
    rank_estadual = models.IntegerField(null=True, blank=True)
    total_estadual = models.IntegerField(null=True, blank=True)
    rank_faixa = models.IntegerField(null=True, blank=True)
    total_faixa = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Dados Atuais - {self.municipio.name_muni}"


class ContaDetalhada(models.Model):
    municipio = models.OneToOneField(
        Municipio,
        to_field='cod_ibge',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='conta_detalhada'
    )
    imposto_taxas_contribuicoes = models.FloatField()
    contribuicoes = models.FloatField()
    transferencias_correntes = models.FloatField()
    outras_receita = models.FloatField()

    def _calcular_pc(self, valor):
        try:
            pop = self.municipio.dados_atuais.populacao_atual
        except Exception:
            pop = None
        if pop and pop > 0:
            return valor / pop
        return 0

    
    @property
    def imposto_taxas_contribuicoes_pc(self): return self._calcular_pc(self.imposto_taxas_contribuicoes)
    @property
    def contribuicoes_pc(self): return self._calcular_pc(self.contribuicoes)
    @property
    def transferencias_correntes_pc(self): return self._calcular_pc(self.transferencias_correntes)
    @property
    def outras_receita_pc(self): return self._calcular_pc(self.outras_receita)

    def __str__(self):
        return f"Receita Detalhada de {self.municipio.name_muni_uf}"

class ContaDetalhadaPercentil(models.Model):
    municipio = models.OneToOneField(
        Municipio,
        to_field='cod_ibge',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='conta_detalhada_percentil'
    )
    imposto_taxas_contribuicoes_nacional = models.FloatField()
    contribuicoes_nacional = models.FloatField()
    transferencias_correntes_nacional = models.FloatField()
    outras_receita_nacional = models.FloatField()
    imposto_taxas_contribuicoes_regional = models.FloatField()
    contribuicoes_regional = models.FloatField()
    transferencias_correntes_regional = models.FloatField()
    outras_receita_regional = models.FloatField()
    imposto_taxas_contribuicoes_estadual = models.FloatField()
    contribuicoes_estadual = models.FloatField()
    transferencias_correntes_estadual = models.FloatField()
    outras_receita_estadual = models.FloatField()

    def __str__(self):
        return f"Receita Detalhada Percentil de {self.municipio.name_muni_uf}"

class ContaEspecifica(models.Model):
    municipio = models.OneToOneField(
        Municipio,
        to_field='cod_ibge',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='conta_especifica'
    )
    imposto = models.FloatField()
    taxas = models.FloatField()
    contribuicoes_melhoria = models.FloatField()
    contribuicoes_sociais = models.FloatField()
    contribuicoes_iluminacao_publica = models.FloatField()
    outras_contribuicoes = models.FloatField()
    tranferencias_uniao = models.FloatField()
    tranferencias_estados = models.FloatField()
    outras_tranferencias = models.FloatField()
    receita_patrimonial = models.FloatField()
    receita_agropecuaria = models.FloatField()
    receita_industrial = models.FloatField()
    receita_servicos = models.FloatField()
    outras_receitas = models.FloatField()

    def _calcular_pc(self, valor):
        try:
            pop = self.municipio.dados_atuais.populacao_atual
        except Exception:
            pop = None
        if pop and pop > 0:
            return valor / pop
        return 0


    @property
    def imposto_pc(self): return self._calcular_pc(self.imposto)
    @property
    def taxas_pc(self): return self._calcular_pc(self.taxas)
    @property
    def contribuicoes_melhoria_pc(self): return self._calcular_pc(self.contribuicoes_melhoria)
    @property
    def contribuicoes_sociais_pc(self): return self._calcular_pc(self.contribuicoes_sociais)
    @property
    def contribuicoes_iluminacao_publica_pc(self): return self._calcular_pc(self.contribuicoes_iluminacao_publica)
    @property
    def outras_contribuicoes_pc(self): return self._calcular_pc(self.outras_contribuicoes)
    @property
    def tranferencias_uniao_pc(self): return self._calcular_pc(self.tranferencias_uniao)
    @property
    def tranferencias_estados_pc(self): return self._calcular_pc(self.tranferencias_estados)
    @property
    def outras_tranferencias_pc(self): return self._calcular_pc(self.outras_tranferencias)
    @property
    def receita_patrimonial_pc(self): return self._calcular_pc(self.receita_patrimonial)
    @property
    def receita_agropecuaria_pc(self): return self._calcular_pc(self.receita_agropecuaria)
    @property
    def receita_industrial_pc(self): return self._calcular_pc(self.receita_industrial)
    @property
    def receita_servicos_pc(self): return self._calcular_pc(self.receita_servicos)
    @property
    def outras_receitas_pc(self): return self._calcular_pc(self.outras_receitas)

    def __str__(self):
        return f"Receita Específica de {self.municipio.name_muni_uf}"

class ContaEspecificaPercentil(models.Model):
    municipio = models.OneToOneField(
        Municipio,
        to_field='cod_ibge',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='conta_especifica_percentil'
    )
    # Campos Nacionais
    imposto_nacional = models.FloatField()
    taxas_nacional = models.FloatField()
    contribuicoes_melhoria_nacional = models.FloatField()
    contribuicoes_sociais_nacional = models.FloatField()
    contribuicoes_iluminacao_publica_nacional = models.FloatField()
    outras_contribuicoes_nacional = models.FloatField()
    tranferencias_uniao_nacional = models.FloatField()
    tranferencias_estados_nacional = models.FloatField()
    outras_tranferencias_nacional = models.FloatField()
    receita_patrimonial_nacional = models.FloatField()
    receita_agropecuaria_nacional = models.FloatField()
    receita_industrial_nacional = models.FloatField()
    receita_servicos_nacional = models.FloatField()
    outras_receitas_nacional = models.FloatField()
    # Campos Regionais
    imposto_regional = models.FloatField()
    taxas_regional = models.FloatField()
    contribuicoes_melhoria_regional = models.FloatField()
    contribuicoes_sociais_regional = models.FloatField()
    contribuicoes_iluminacao_publica_regional = models.FloatField()
    outras_contribuicoes_regional = models.FloatField()
    tranferencias_uniao_regional = models.FloatField()
    tranferencias_estados_regional = models.FloatField()
    outras_tranferencias_regional = models.FloatField()
    receita_patrimonial_regional = models.FloatField()
    receita_agropecuaria_regional = models.FloatField()
    receita_industrial_regional = models.FloatField()
    receita_servicos_regional = models.FloatField()
    outras_receitas_regional = models.FloatField()
    # Campos Estaduais
    imposto_estadual = models.FloatField()
    taxas_estadual = models.FloatField()
    contribuicoes_melhoria_estadual = models.FloatField()
    contribuicoes_sociais_estadual = models.FloatField()
    contribuicoes_iluminacao_publica_estadual = models.FloatField()
    outras_contribuicoes_estadual = models.FloatField()
    tranferencias_uniao_estadual = models.FloatField()
    tranferencias_estados_estadual = models.FloatField()
    outras_tranferencias_estadual = models.FloatField()
    receita_patrimonial_estadual = models.FloatField()
    receita_agropecuaria_estadual = models.FloatField()
    receita_industrial_estadual = models.FloatField()
    receita_servicos_estadual = models.FloatField()
    outras_receitas_estadual = models.FloatField()

    def __str__(self):
        return f"Receita Específica Percentil de {self.municipio.name_muni_uf}"

class ContaMaisEspecifica(models.Model):
    municipio = models.OneToOneField(
        Municipio,
        to_field='cod_ibge',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='conta_mais_especifica'
    )
    iptu = models.FloatField()
    itbi = models.FloatField()
    iss = models.FloatField()
    imposto_renda = models.FloatField()
    imposto_icms = models.FloatField()
    imposto_ipva = models.FloatField()
    outros_impostos = models.FloatField()
    taxa_policia = models.FloatField()
    taxa_prestacao_servico = models.FloatField()
    outras_taxas = models.FloatField()
    contribuicao_melhoria_pavimento_obras = models.FloatField()
    contribuicao_melhoria_agua_potavel = models.FloatField()
    contribuicao_melhoria_iluminacao_publica = models.FloatField()
    outras_contribuicoes_melhoria = models.FloatField()
    transferencia_uniao_fpm = models.FloatField()
    transferencia_uniao_exploracao = models.FloatField()
    transferencia_uniao_sus = models.FloatField()
    transferencia_uniao_fnde = models.FloatField()
    transferencia_uniao_fundeb = models.FloatField()
    transferencia_uniao_fnas = models.FloatField()
    transferencia_uniao_fpe = models.FloatField()
    outras_transferencias_uniao = models.FloatField()
    transferencia_estado_icms = models.FloatField()
    transferencia_estado_ipva = models.FloatField()
    transferencia_estado_exploracao = models.FloatField()
    transferencia_estado_sus = models.FloatField()
    transferencia_estado_assistencia = models.FloatField()
    outras_transferencias_estado = models.FloatField()

    def _calcular_pc(self, valor):
        try:
            pop = self.municipio.dados_atuais.populacao_atual
        except Exception:
            pop = None
        if pop and pop > 0:
            return valor / pop
        return 0

    
    # --- Propriedades Impostos ---
    @property
    def iptu_pc(self): return self._calcular_pc(self.iptu)

    @property
    def itbi_pc(self): return self._calcular_pc(self.itbi)

    @property
    def iss_pc(self): return self._calcular_pc(self.iss)

    @property
    def imposto_renda_pc(self): return self._calcular_pc(self.imposto_renda)

    @property
    def imposto_icms_pc(self): return self._calcular_pc(self.imposto_icms)

    @property
    def imposto_ipva_pc(self): return self._calcular_pc(self.imposto_ipva)

    @property
    def outros_impostos_pc(self): return self._calcular_pc(self.outros_impostos)

    @property
    def taxa_policia_pc(self): return self._calcular_pc(self.taxa_policia)

    @property
    def taxa_prestacao_servico_pc(self): return self._calcular_pc(self.taxa_prestacao_servico)

    @property
    def outras_taxas_pc(self): return self._calcular_pc(self.outras_taxas)

    @property
    def contribuicao_melhoria_pavimento_obras_pc(self):
        return self._calcular_pc(self.contribuicao_melhoria_pavimento_obras)

    @property
    def contribuicao_melhoria_agua_potavel_pc(self):
        return self._calcular_pc(self.contribuicao_melhoria_agua_potavel)

    @property
    def contribuicao_melhoria_iluminacao_publica_pc(self):
        return self._calcular_pc(self.contribuicao_melhoria_iluminacao_publica)

    @property
    def outras_contribuicoes_melhoria_pc(self):
        return self._calcular_pc(self.outras_contribuicoes_melhoria)

    @property
    def transferencia_uniao_fpm_pc(self):
        return self._calcular_pc(self.transferencia_uniao_fpm)

    @property
    def transferencia_uniao_exploracao_pc(self):
        return self._calcular_pc(self.transferencia_uniao_exploracao)

    @property
    def transferencia_uniao_sus_pc(self):
        return self._calcular_pc(self.transferencia_uniao_sus)

    @property
    def transferencia_uniao_fnde_pc(self):
        return self._calcular_pc(self.transferencia_uniao_fnde)

    @property
    def transferencia_uniao_fundeb_pc(self):
        return self._calcular_pc(self.transferencia_uniao_fundeb)

    @property
    def transferencia_uniao_fnas_pc(self):
        return self._calcular_pc(self.transferencia_uniao_fnas)
    
    @property
    def transferencia_uniao_fpe_pc(self):
        return self._calcular_pc(self.transferencia_uniao_fpe)

    @property
    def outras_transferencias_uniao_pc(self):
        return self._calcular_pc(self.outras_transferencias_uniao)

    @property
    def transferencia_estado_icms_pc(self):
        return self._calcular_pc(self.transferencia_estado_icms)

    @property
    def transferencia_estado_ipva_pc(self):
        return self._calcular_pc(self.transferencia_estado_ipva)

    @property
    def transferencia_estado_exploracao_pc(self):
        return self._calcular_pc(self.transferencia_estado_exploracao)

    @property
    def transferencia_estado_sus_pc(self):
        return self._calcular_pc(self.transferencia_estado_sus)

    @property
    def transferencia_estado_assistencia_pc(self):
        return self._calcular_pc(self.transferencia_estado_assistencia)

    @property
    def outras_transferencias_estado_pc(self):
        return self._calcular_pc(self.outras_transferencias_estado)
    def __str__(self):
        return f"Receita Mais Específica de {self.municipio.name_muni_uf}"

class ContaMaisEspecificaPercentil(models.Model):
    municipio = models.OneToOneField(
        Municipio,
        to_field='cod_ibge',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='conta_mais_especifica_percentil'
    )
    # Nacional
    iptu_nacional = models.FloatField()
    itbi_nacional = models.FloatField()
    iss_nacional = models.FloatField()
    imposto_renda_nacional = models.FloatField()
    imposto_icms_nacional = models.FloatField()
    imposto_ipva_nacional = models.FloatField()
    outros_impostos_nacional = models.FloatField()
    taxa_policia_nacional = models.FloatField()
    taxa_prestacao_servico_nacional = models.FloatField()
    outras_taxas_nacional = models.FloatField()
    contribuicao_melhoria_pavimento_obras_nacional = models.FloatField()
    contribuicao_melhoria_agua_potavel_nacional = models.FloatField()
    contribuicao_melhoria_iluminacao_publica_nacional = models.FloatField()
    outras_contribuicoes_melhoria_nacional = models.FloatField()
    transferencia_uniao_fpm_nacional = models.FloatField()
    transferencia_uniao_exploracao_nacional = models.FloatField()
    transferencia_uniao_sus_nacional = models.FloatField()
    transferencia_uniao_fnde_nacional = models.FloatField()
    transferencia_uniao_fundeb_nacional = models.FloatField()
    transferencia_uniao_fnas_nacional = models.FloatField()
    transferencia_uniao_fpe_nacional = models.FloatField()
    outras_transferencias_uniao_nacional = models.FloatField()
    transferencia_estado_icms_nacional = models.FloatField()
    transferencia_estado_ipva_nacional = models.FloatField()
    transferencia_estado_exploracao_nacional = models.FloatField()
    transferencia_estado_sus_nacional = models.FloatField()
    transferencia_estado_assistencia_nacional = models.FloatField()
    outras_transferencias_estado_nacional = models.FloatField()
    # Regional
    iptu_regional = models.FloatField()
    itbi_regional = models.FloatField()
    iss_regional = models.FloatField()
    imposto_renda_regional = models.FloatField()
    imposto_icms_regional = models.FloatField()
    imposto_ipva_regional = models.FloatField()
    outros_impostos_regional = models.FloatField()
    taxa_policia_regional = models.FloatField()
    taxa_prestacao_servico_regional = models.FloatField()
    outras_taxas_regional = models.FloatField()
    contribuicao_melhoria_pavimento_obras_regional = models.FloatField()
    contribuicao_melhoria_agua_potavel_regional = models.FloatField()
    contribuicao_melhoria_iluminacao_publica_regional = models.FloatField()
    outras_contribuicoes_melhoria_regional = models.FloatField()
    transferencia_uniao_fpm_regional = models.FloatField()
    transferencia_uniao_exploracao_regional = models.FloatField()
    transferencia_uniao_sus_regional = models.FloatField()
    transferencia_uniao_fnde_regional = models.FloatField()
    transferencia_uniao_fundeb_regional = models.FloatField()
    transferencia_uniao_fnas_regional = models.FloatField()
    transferencia_uniao_fpe_regional = models.FloatField()
    outras_transferencias_uniao_regional = models.FloatField()
    transferencia_estado_icms_regional = models.FloatField()
    transferencia_estado_ipva_regional = models.FloatField()
    transferencia_estado_exploracao_regional = models.FloatField()
    transferencia_estado_sus_regional = models.FloatField()
    transferencia_estado_assistencia_regional = models.FloatField()
    outras_transferencias_estado_regional = models.FloatField()
    # Estadual
    iptu_estadual = models.FloatField()
    itbi_estadual = models.FloatField()
    iss_estadual = models.FloatField()
    imposto_renda_estadual = models.FloatField()
    imposto_icms_estadual = models.FloatField()
    imposto_ipva_estadual = models.FloatField()
    outros_impostos_estadual = models.FloatField()
    taxa_policia_estadual = models.FloatField()
    taxa_prestacao_servico_estadual = models.FloatField()
    outras_taxas_estadual = models.FloatField()
    contribuicao_melhoria_pavimento_obras_estadual = models.FloatField()
    contribuicao_melhoria_agua_potavel_estadual = models.FloatField()
    contribuicao_melhoria_iluminacao_publica_estadual = models.FloatField()
    outras_contribuicoes_melhoria_estadual = models.FloatField()
    transferencia_uniao_fpm_estadual = models.FloatField()
    transferencia_uniao_exploracao_estadual = models.FloatField()
    transferencia_uniao_sus_estadual = models.FloatField()
    transferencia_uniao_fnde_estadual = models.FloatField()
    transferencia_uniao_fundeb_estadual = models.FloatField()
    transferencia_uniao_fnas_estadual = models.FloatField()
    transferencia_uniao_fpe_estadual = models.FloatField()
    outras_transferencias_uniao_estadual = models.FloatField()
    transferencia_estado_icms_estadual = models.FloatField()
    transferencia_estado_ipva_estadual = models.FloatField()
    transferencia_estado_exploracao_estadual = models.FloatField()
    transferencia_estado_sus_estadual = models.FloatField()
    transferencia_estado_assistencia_estadual = models.FloatField()
    outras_transferencias_estado_estadual = models.FloatField()

    def __str__(self):
        return f"Receita Mais Específica Percentil de {self.municipio.name_muni_uf}"

class Noticia(models.Model):
    titulo = models.CharField(max_length=200, verbose_name="Título da Matéria")
    data = models.DateField(verbose_name="Data de Publicação")
    # Hospedagem externa (Google Drive, Imgur, etc.) — filesystem do Render é efêmero,
    # por isso não usamos ImageField. O template resolve o link via `imagem_embed_url`.
    imagem_url = models.URLField(
        max_length=500,
        verbose_name="Link da Imagem de Capa",
        help_text=(
            "Cole o link de compartilhamento da imagem. "
            "Funciona com Google Drive (o arquivo precisa estar como 'Qualquer pessoa com o link'), "
            "Imgur ou qualquer URL pública direta (.jpg/.png)."
        ),
        blank=True,
        null=True,
    )
    tag = models.CharField(max_length=50, verbose_name="Categoria (Tag)")
    link = models.URLField(max_length=500, verbose_name="Link de Destino", blank=True, null=True)

    class Meta:
        verbose_name = "Notícia"
        verbose_name_plural = "Notícias"
        ordering = ['-data']

    def __str__(self):
        return self.titulo

    @property
    def imagem_embed_url(self):
        """
        Converte qualquer formato de link do Google Drive (view, open, uc) para o
        endpoint de thumbnail, que é o mais estável para hotlink em <img>.
        Links de outros hosts (Imgur etc.) passam sem alteração.
        """
        url = (self.imagem_url or '').strip()
        if not url:
            return ''
        if 'drive.google.com' not in url:
            return url

        import re
        match = (
            re.search(r'/file/d/([A-Za-z0-9_-]+)', url)
            or re.search(r'[?&]id=([A-Za-z0-9_-]+)', url)
        )
        if not match:
            return url
        file_id = match.group(1)
        return f'https://drive.google.com/thumbnail?id={file_id}&sz=w1000'


class MediaNacionalReceita(models.Model):
    """
    Entidade de registro unico para armazenamento das medias nacionais pre-calculadas.
    Estrutura projetada para centralizar metricas agregadas e reduzir processamento em tempo de execucao.
    """
    ano_referencia = models.IntegerField(unique=False)
    
    # Metricas de Nivel 1 - Conta Detalhada
    imposto_taxas_contribuicoes = models.FloatField(null=True, blank=True)
    contribuicoes = models.FloatField(null=True, blank=True)
    transferencias_correntes = models.FloatField(null=True, blank=True)
    outras_receita = models.FloatField(null=True, blank=True)

    # Metricas de Nivel 2 - Conta Especifica
    imposto = models.FloatField(null=True, blank=True)
    taxas = models.FloatField(null=True, blank=True)
    contribuicoes_melhoria = models.FloatField(null=True, blank=True)
    contribuicoes_sociais = models.FloatField(null=True, blank=True)
    contribuicoes_iluminacao_publica = models.FloatField(null=True, blank=True)
    outras_contribuicoes = models.FloatField(null=True, blank=True)
    tranferencias_uniao = models.FloatField(null=True, blank=True)
    tranferencias_estados = models.FloatField(null=True, blank=True)
    outras_tranferencias = models.FloatField(null=True, blank=True)
    receita_patrimonial = models.FloatField(null=True, blank=True)
    receita_agropecuaria = models.FloatField(null=True, blank=True)
    receita_industrial = models.FloatField(null=True, blank=True)
    receita_servicos = models.FloatField(null=True, blank=True)
    outras_receitas = models.FloatField(null=True, blank=True)
    
    # Metricas de Nivel 3 - Conta Mais Especifica
    iptu = models.FloatField(null=True, blank=True)
    itbi = models.FloatField(null=True, blank=True)
    iss = models.FloatField(null=True, blank=True)
    imposto_renda = models.FloatField(null=True, blank=True)
    outros_impostos = models.FloatField(null=True, blank=True)
    taxa_policia = models.FloatField(null=True, blank=True)
    taxa_prestacao_servico = models.FloatField(null=True, blank=True)
    outras_taxas = models.FloatField(null=True, blank=True)
    contribuicao_melhoria_pavimento_obras = models.FloatField(null=True, blank=True)
    contribuicao_melhoria_agua_potavel = models.FloatField(null=True, blank=True)
    contribuicao_melhoria_iluminacao_publica = models.FloatField(null=True, blank=True)
    outras_contribuicoes_melhoria = models.FloatField(null=True, blank=True)
    transferencia_uniao_fpm = models.FloatField(null=True, blank=True)
    transferencia_uniao_exploracao = models.FloatField(null=True, blank=True)
    transferencia_uniao_sus = models.FloatField(null=True, blank=True)
    transferencia_uniao_fnde = models.FloatField(null=True, blank=True)
    transferencia_uniao_fundeb = models.FloatField(null=True, blank=True)
    transferencia_uniao_fnas = models.FloatField(null=True, blank=True)
    outras_transferencias_uniao = models.FloatField(null=True, blank=True)
    transferencia_estado_icms = models.FloatField(null=True, blank=True)
    transferencia_estado_ipva = models.FloatField(null=True, blank=True)
    transferencia_estado_exploracao = models.FloatField(null=True, blank=True)
    transferencia_estado_sus = models.FloatField(null=True, blank=True)
    transferencia_estado_assistencia = models.FloatField(null=True, blank=True)
    outras_transferencias_estado = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "Média Nacional de Receita"
        verbose_name_plural = "Médias Nacionais de Receitas"

    def __str__(self):
        return f"Médias Nacionais - Ano {self.ano_referencia}"
    

class MediaUfReceita(models.Model):
    """
    Entidade de registro unico para armazenamento das medias nacionais pre-calculadas.
    Estrutura projetada para centralizar metricas agregadas e reduzir processamento em tempo de execucao.
    """
    ano_referencia = models.IntegerField(unique=False)
    uf = models.CharField(max_length=2)
    
    # Metricas de Nivel 1 - Conta Detalhada
    imposto_taxas_contribuicoes = models.FloatField(null=True, blank=True)
    contribuicoes = models.FloatField(null=True, blank=True)
    transferencias_correntes = models.FloatField(null=True, blank=True)
    outras_receita = models.FloatField(null=True, blank=True)

    # Metricas de Nivel 2 - Conta Especifica
    imposto = models.FloatField(null=True, blank=True)
    taxas = models.FloatField(null=True, blank=True)
    contribuicoes_melhoria = models.FloatField(null=True, blank=True)
    contribuicoes_sociais = models.FloatField(null=True, blank=True)
    contribuicoes_iluminacao_publica = models.FloatField(null=True, blank=True)
    outras_contribuicoes = models.FloatField(null=True, blank=True)
    tranferencias_uniao = models.FloatField(null=True, blank=True)
    tranferencias_estados = models.FloatField(null=True, blank=True)
    outras_tranferencias = models.FloatField(null=True, blank=True)
    receita_patrimonial = models.FloatField(null=True, blank=True)
    receita_agropecuaria = models.FloatField(null=True, blank=True)
    receita_industrial = models.FloatField(null=True, blank=True)
    receita_servicos = models.FloatField(null=True, blank=True)
    outras_receitas = models.FloatField(null=True, blank=True)
    
    # Metricas de Nivel 3 - Conta Mais Especifica
    iptu = models.FloatField(null=True, blank=True)
    itbi = models.FloatField(null=True, blank=True)
    iss = models.FloatField(null=True, blank=True)
    imposto_renda = models.FloatField(null=True, blank=True)
    outros_impostos = models.FloatField(null=True, blank=True)
    taxa_policia = models.FloatField(null=True, blank=True)
    taxa_prestacao_servico = models.FloatField(null=True, blank=True)
    outras_taxas = models.FloatField(null=True, blank=True)
    contribuicao_melhoria_pavimento_obras = models.FloatField(null=True, blank=True)
    contribuicao_melhoria_agua_potavel = models.FloatField(null=True, blank=True)
    contribuicao_melhoria_iluminacao_publica = models.FloatField(null=True, blank=True)
    outras_contribuicoes_melhoria = models.FloatField(null=True, blank=True)
    transferencia_uniao_fpm = models.FloatField(null=True, blank=True)
    transferencia_uniao_exploracao = models.FloatField(null=True, blank=True)
    transferencia_uniao_sus = models.FloatField(null=True, blank=True)
    transferencia_uniao_fnde = models.FloatField(null=True, blank=True)
    transferencia_uniao_fundeb = models.FloatField(null=True, blank=True)
    transferencia_uniao_fnas = models.FloatField(null=True, blank=True)
    outras_transferencias_uniao = models.FloatField(null=True, blank=True)
    transferencia_estado_icms = models.FloatField(null=True, blank=True)
    transferencia_estado_ipva = models.FloatField(null=True, blank=True)
    transferencia_estado_exploracao = models.FloatField(null=True, blank=True)
    transferencia_estado_sus = models.FloatField(null=True, blank=True)
    transferencia_estado_assistencia = models.FloatField(null=True, blank=True)
    outras_transferencias_estado = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "Média UF de Receita"
        verbose_name_plural = "Médias UF de Receitas"

    def __str__(self):
        return f"Médias {self.uf} - Ano {self.ano_referencia}"
    
class MediaPorteReceita(models.Model):
    """
    Entidade de registro unico para armazenamento das medias nacionais pre-calculadas.
    Estrutura projetada para centralizar metricas agregadas e reduzir processamento em tempo de execucao.
    """
    ano_referencia = models.IntegerField(unique=False)
    porte = models.CharField(max_length=50000)
    
    # Metricas de Nivel 1 - Conta Detalhada
    imposto_taxas_contribuicoes = models.FloatField(null=True, blank=True)
    contribuicoes = models.FloatField(null=True, blank=True)
    transferencias_correntes = models.FloatField(null=True, blank=True)
    outras_receita = models.FloatField(null=True, blank=True)

    # Metricas de Nivel 2 - Conta Especifica
    imposto = models.FloatField(null=True, blank=True)
    taxas = models.FloatField(null=True, blank=True)
    contribuicoes_melhoria = models.FloatField(null=True, blank=True)
    contribuicoes_sociais = models.FloatField(null=True, blank=True)
    contribuicoes_iluminacao_publica = models.FloatField(null=True, blank=True)
    outras_contribuicoes = models.FloatField(null=True, blank=True)
    tranferencias_uniao = models.FloatField(null=True, blank=True)
    tranferencias_estados = models.FloatField(null=True, blank=True)
    outras_tranferencias = models.FloatField(null=True, blank=True)
    receita_patrimonial = models.FloatField(null=True, blank=True)
    receita_agropecuaria = models.FloatField(null=True, blank=True)
    receita_industrial = models.FloatField(null=True, blank=True)
    receita_servicos = models.FloatField(null=True, blank=True)
    outras_receitas = models.FloatField(null=True, blank=True)
    
    # Metricas de Nivel 3 - Conta Mais Especifica
    iptu = models.FloatField(null=True, blank=True)
    itbi = models.FloatField(null=True, blank=True)
    iss = models.FloatField(null=True, blank=True)
    imposto_renda = models.FloatField(null=True, blank=True)
    outros_impostos = models.FloatField(null=True, blank=True)
    taxa_policia = models.FloatField(null=True, blank=True)
    taxa_prestacao_servico = models.FloatField(null=True, blank=True)
    outras_taxas = models.FloatField(null=True, blank=True)
    contribuicao_melhoria_pavimento_obras = models.FloatField(null=True, blank=True)
    contribuicao_melhoria_agua_potavel = models.FloatField(null=True, blank=True)
    contribuicao_melhoria_iluminacao_publica = models.FloatField(null=True, blank=True)
    outras_contribuicoes_melhoria = models.FloatField(null=True, blank=True)
    transferencia_uniao_fpm = models.FloatField(null=True, blank=True)
    transferencia_uniao_exploracao = models.FloatField(null=True, blank=True)
    transferencia_uniao_sus = models.FloatField(null=True, blank=True)
    transferencia_uniao_fnde = models.FloatField(null=True, blank=True)
    transferencia_uniao_fundeb = models.FloatField(null=True, blank=True)
    transferencia_uniao_fnas = models.FloatField(null=True, blank=True)
    outras_transferencias_uniao = models.FloatField(null=True, blank=True)
    transferencia_estado_icms = models.FloatField(null=True, blank=True)
    transferencia_estado_ipva = models.FloatField(null=True, blank=True)
    transferencia_estado_exploracao = models.FloatField(null=True, blank=True)
    transferencia_estado_sus = models.FloatField(null=True, blank=True)
    transferencia_estado_assistencia = models.FloatField(null=True, blank=True)
    outras_transferencias_estado = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "Média Porte de Receita"
        verbose_name_plural = "Médias Porte de Receitas"

    def __str__(self):
        return f"Médias {self.porte} - Ano {self.ano_referencia}"
    



class MedianaNacionalReceita(models.Model):
    """
    Entidade de registro unico para armazenamento das medias nacionais pre-calculadas.
    Estrutura projetada para centralizar metricas agregadas e reduzir processamento em tempo de execucao.
    """
    ano_referencia = models.IntegerField(unique=False)
    
    # Metricas de Nivel 1 - Conta Detalhada
    imposto_taxas_contribuicoes = models.FloatField(null=True, blank=True)
    contribuicoes = models.FloatField(null=True, blank=True)
    transferencias_correntes = models.FloatField(null=True, blank=True)
    outras_receita = models.FloatField(null=True, blank=True)

    # Metricas de Nivel 2 - Conta Especifica
    imposto = models.FloatField(null=True, blank=True)
    taxas = models.FloatField(null=True, blank=True)
    contribuicoes_melhoria = models.FloatField(null=True, blank=True)
    contribuicoes_sociais = models.FloatField(null=True, blank=True)
    contribuicoes_iluminacao_publica = models.FloatField(null=True, blank=True)
    outras_contribuicoes = models.FloatField(null=True, blank=True)
    tranferencias_uniao = models.FloatField(null=True, blank=True)
    tranferencias_estados = models.FloatField(null=True, blank=True)
    outras_tranferencias = models.FloatField(null=True, blank=True)
    receita_patrimonial = models.FloatField(null=True, blank=True)
    receita_agropecuaria = models.FloatField(null=True, blank=True)
    receita_industrial = models.FloatField(null=True, blank=True)
    receita_servicos = models.FloatField(null=True, blank=True)
    outras_receitas = models.FloatField(null=True, blank=True)
    
    # Metricas de Nivel 3 - Conta Mais Especifica
    iptu = models.FloatField(null=True, blank=True)
    itbi = models.FloatField(null=True, blank=True)
    iss = models.FloatField(null=True, blank=True)
    imposto_renda = models.FloatField(null=True, blank=True)
    outros_impostos = models.FloatField(null=True, blank=True)
    taxa_policia = models.FloatField(null=True, blank=True)
    taxa_prestacao_servico = models.FloatField(null=True, blank=True)
    outras_taxas = models.FloatField(null=True, blank=True)
    contribuicao_melhoria_pavimento_obras = models.FloatField(null=True, blank=True)
    contribuicao_melhoria_agua_potavel = models.FloatField(null=True, blank=True)
    contribuicao_melhoria_iluminacao_publica = models.FloatField(null=True, blank=True)
    outras_contribuicoes_melhoria = models.FloatField(null=True, blank=True)
    transferencia_uniao_fpm = models.FloatField(null=True, blank=True)
    transferencia_uniao_exploracao = models.FloatField(null=True, blank=True)
    transferencia_uniao_sus = models.FloatField(null=True, blank=True)
    transferencia_uniao_fnde = models.FloatField(null=True, blank=True)
    transferencia_uniao_fundeb = models.FloatField(null=True, blank=True)
    transferencia_uniao_fnas = models.FloatField(null=True, blank=True)
    outras_transferencias_uniao = models.FloatField(null=True, blank=True)
    transferencia_estado_icms = models.FloatField(null=True, blank=True)
    transferencia_estado_ipva = models.FloatField(null=True, blank=True)
    transferencia_estado_exploracao = models.FloatField(null=True, blank=True)
    transferencia_estado_sus = models.FloatField(null=True, blank=True)
    transferencia_estado_assistencia = models.FloatField(null=True, blank=True)
    outras_transferencias_estado = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "Média Nacional de Receita"
        verbose_name_plural = "Médias Nacionais de Receitas"

    def __str__(self):
        return f"Médias Nacionais - Ano {self.ano_referencia}"
    

class MedianaUfReceita(models.Model):
    """
    Entidade de registro unico para armazenamento das medias nacionais pre-calculadas.
    Estrutura projetada para centralizar metricas agregadas e reduzir processamento em tempo de execucao.
    """
    ano_referencia = models.IntegerField(unique=False)
    uf = models.CharField(max_length=2)
    
    # Metricas de Nivel 1 - Conta Detalhada
    imposto_taxas_contribuicoes = models.FloatField(null=True, blank=True)
    contribuicoes = models.FloatField(null=True, blank=True)
    transferencias_correntes = models.FloatField(null=True, blank=True)
    outras_receita = models.FloatField(null=True, blank=True)

    # Metricas de Nivel 2 - Conta Especifica
    imposto = models.FloatField(null=True, blank=True)
    taxas = models.FloatField(null=True, blank=True)
    contribuicoes_melhoria = models.FloatField(null=True, blank=True)
    contribuicoes_sociais = models.FloatField(null=True, blank=True)
    contribuicoes_iluminacao_publica = models.FloatField(null=True, blank=True)
    outras_contribuicoes = models.FloatField(null=True, blank=True)
    tranferencias_uniao = models.FloatField(null=True, blank=True)
    tranferencias_estados = models.FloatField(null=True, blank=True)
    outras_tranferencias = models.FloatField(null=True, blank=True)
    receita_patrimonial = models.FloatField(null=True, blank=True)
    receita_agropecuaria = models.FloatField(null=True, blank=True)
    receita_industrial = models.FloatField(null=True, blank=True)
    receita_servicos = models.FloatField(null=True, blank=True)
    outras_receitas = models.FloatField(null=True, blank=True)
    
    # Metricas de Nivel 3 - Conta Mais Especifica
    iptu = models.FloatField(null=True, blank=True)
    itbi = models.FloatField(null=True, blank=True)
    iss = models.FloatField(null=True, blank=True)
    imposto_renda = models.FloatField(null=True, blank=True)
    outros_impostos = models.FloatField(null=True, blank=True)
    taxa_policia = models.FloatField(null=True, blank=True)
    taxa_prestacao_servico = models.FloatField(null=True, blank=True)
    outras_taxas = models.FloatField(null=True, blank=True)
    contribuicao_melhoria_pavimento_obras = models.FloatField(null=True, blank=True)
    contribuicao_melhoria_agua_potavel = models.FloatField(null=True, blank=True)
    contribuicao_melhoria_iluminacao_publica = models.FloatField(null=True, blank=True)
    outras_contribuicoes_melhoria = models.FloatField(null=True, blank=True)
    transferencia_uniao_fpm = models.FloatField(null=True, blank=True)
    transferencia_uniao_exploracao = models.FloatField(null=True, blank=True)
    transferencia_uniao_sus = models.FloatField(null=True, blank=True)
    transferencia_uniao_fnde = models.FloatField(null=True, blank=True)
    transferencia_uniao_fundeb = models.FloatField(null=True, blank=True)
    transferencia_uniao_fnas = models.FloatField(null=True, blank=True)
    outras_transferencias_uniao = models.FloatField(null=True, blank=True)
    transferencia_estado_icms = models.FloatField(null=True, blank=True)
    transferencia_estado_ipva = models.FloatField(null=True, blank=True)
    transferencia_estado_exploracao = models.FloatField(null=True, blank=True)
    transferencia_estado_sus = models.FloatField(null=True, blank=True)
    transferencia_estado_assistencia = models.FloatField(null=True, blank=True)
    outras_transferencias_estado = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "Média UF de Receita"
        verbose_name_plural = "Médias UF de Receitas"

    def __str__(self):
        return f"Médias {self.uf} - Ano {self.ano_referencia}"
    
class MedianaPorteReceita(models.Model):
    """
    Entidade de registro unico para armazenamento das medianas nacionais pre-calculadas.
    Estrutura projetada para centralizar metricas agregadas e reduzir processamento em tempo de execucao.
    """
    ano_referencia = models.IntegerField(unique=False)
    porte = models.CharField(max_length=50000)
    
    # Metricas de Nivel 1 - Conta Detalhada
    imposto_taxas_contribuicoes = models.FloatField(null=True, blank=True)
    contribuicoes = models.FloatField(null=True, blank=True)
    transferencias_correntes = models.FloatField(null=True, blank=True)
    outras_receita = models.FloatField(null=True, blank=True)

    # Metricas de Nivel 2 - Conta Especifica
    imposto = models.FloatField(null=True, blank=True)
    taxas = models.FloatField(null=True, blank=True)
    contribuicoes_melhoria = models.FloatField(null=True, blank=True)
    contribuicoes_sociais = models.FloatField(null=True, blank=True)
    contribuicoes_iluminacao_publica = models.FloatField(null=True, blank=True)
    outras_contribuicoes = models.FloatField(null=True, blank=True)
    tranferencias_uniao = models.FloatField(null=True, blank=True)
    tranferencias_estados = models.FloatField(null=True, blank=True)
    outras_tranferencias = models.FloatField(null=True, blank=True)
    receita_patrimonial = models.FloatField(null=True, blank=True)
    receita_agropecuaria = models.FloatField(null=True, blank=True)
    receita_industrial = models.FloatField(null=True, blank=True)
    receita_servicos = models.FloatField(null=True, blank=True)
    outras_receitas = models.FloatField(null=True, blank=True)
    
    # Metricas de Nivel 3 - Conta Mais Especifica
    iptu = models.FloatField(null=True, blank=True)
    itbi = models.FloatField(null=True, blank=True)
    iss = models.FloatField(null=True, blank=True)
    imposto_renda = models.FloatField(null=True, blank=True)
    outros_impostos = models.FloatField(null=True, blank=True)
    taxa_policia = models.FloatField(null=True, blank=True)
    taxa_prestacao_servico = models.FloatField(null=True, blank=True)
    outras_taxas = models.FloatField(null=True, blank=True)
    contribuicao_melhoria_pavimento_obras = models.FloatField(null=True, blank=True)
    contribuicao_melhoria_agua_potavel = models.FloatField(null=True, blank=True)
    contribuicao_melhoria_iluminacao_publica = models.FloatField(null=True, blank=True)
    outras_contribuicoes_melhoria = models.FloatField(null=True, blank=True)
    transferencia_uniao_fpm = models.FloatField(null=True, blank=True)
    transferencia_uniao_exploracao = models.FloatField(null=True, blank=True)
    transferencia_uniao_sus = models.FloatField(null=True, blank=True)
    transferencia_uniao_fnde = models.FloatField(null=True, blank=True)
    transferencia_uniao_fundeb = models.FloatField(null=True, blank=True)
    transferencia_uniao_fnas = models.FloatField(null=True, blank=True)
    outras_transferencias_uniao = models.FloatField(null=True, blank=True)
    transferencia_estado_icms = models.FloatField(null=True, blank=True)
    transferencia_estado_ipva = models.FloatField(null=True, blank=True)
    transferencia_estado_exploracao = models.FloatField(null=True, blank=True)
    transferencia_estado_sus = models.FloatField(null=True, blank=True)
    transferencia_estado_assistencia = models.FloatField(null=True, blank=True)
    outras_transferencias_estado = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "Média Porte de Receita"
        verbose_name_plural = "Médias Porte de Receitas"

    def __str__(self):
        return f"Médias {self.porte} - Ano {self.ano_referencia}"    
    
class CrescimentoMedioUf(models.Model):
    """
    Entidade de registro unico para armazenamento dos crescimentos médios pre-calculados.
    Estrutura projetada para centralizar metricas agregadas e reduzir processamento em tempo de execucao.
    """
    ano_referencia = models.IntegerField(unique=False)
    uf = models.CharField(max_length=2)
    
    # Metricas de Nivel 1 - Conta Detalhada
    receita = models.FloatField(null=True, blank=True)
    populacao = models.FloatField(null=True, blank=True)


class CrescimentoMedioPorte(models.Model):
    """
    Entidade de registro unico para armazenamento dos crescimentos médios pre-calculados.
    Estrutura projetada para centralizar metricas agregadas e reduzir processamento em tempo de execucao.
    """
    ano_referencia = models.IntegerField(unique=False)
    porte = models.CharField(max_length=50000)

    # Metricas de Nivel 1 - Conta Detalhada
    receita = models.FloatField(null=True, blank=True)
    populacao = models.FloatField(null=True, blank=True)