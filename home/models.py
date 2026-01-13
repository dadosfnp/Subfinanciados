from django.db import models
import uuid

class RegiaoMetropolitana(models.Model):
    
    nome = models.CharField(max_length=255, unique=True, help_text="Nome único da Região Metropolitana")

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Região Metropolitana"
        verbose_name_plural = "Regiões Metropolitanas"




class Municipio(models.Model):
    cod_ibge = models.CharField(max_length=7, unique=True)# unique=True é uma boa prática
    name_muni = models.CharField(max_length=255)
    name_muni_uf = models.CharField(max_length=255)
    uf = models.CharField(max_length=2)
    coordx = models.FloatField()
    coordy = models.FloatField()
    populacao23 = models.IntegerField(null=True) # Usando nomes padrão do Python
    populacao00 = models.IntegerField(null=True) # Usando nomes padrão do Python
    rc_2023 = models.FloatField(null=True)
    rc_23_pc = models.FloatField(null=True)
    rc_00_pc = models.FloatField(null=True) # Usando nomes padrão do Python
    populacao23 = models.IntegerField(null=True) # Usando nomes padrão do Python
    quintil23 = models.CharField(max_length=50, null=True)
    decil23 = models.CharField(max_length=50, null=True)
    quintil00 = models.CharField(max_length=50, null=True)
    decil00 = models.CharField(max_length=50, null=True)
    percentil = models.CharField(max_length=50, null=True)
    percentil_n = models.IntegerField(null=True, blank=True)
    regiao = models.CharField(max_length=255)
    rank_nacional = models.IntegerField(null=True, blank=True)
    total_nacional = models.IntegerField(null=True, blank=True)
    rank_estadual = models.IntegerField(null=True, blank=True)
    total_estadual = models.IntegerField(null=True, blank=True)
    rank_faixa = models.IntegerField(null=True, blank=True)
    total_faixa = models.IntegerField(null=True, blank=True)
    rm = models.ForeignKey(
        RegiaoMetropolitana, 
        on_delete=models.SET_NULL, # Se uma RM for deletada, os municípios não serão. O campo ficará nulo.
        null=True,                # Permite que um município não pertença a nenhuma RM (valor nulo no banco).
        blank=True,               # Permite que o campo fique em branco em formulários do Django.
        related_name='municipios' # Permite fazer RM.municipios.all() para ver todos os municípios de uma RM.
    )
    



    def __str__(self):
        return f"{self.name_muni} ({self.uf})"

class ContaDetalhada(models.Model):
    # Troque ForeignKey por OneToOneField
    municipio = models.OneToOneField(
        Municipio,
        to_field='cod_ibge',
        on_delete=models.CASCADE,
        primary_key=True,  # Altamente recomendado!
        # Sugestão: renomeie para um nome no singular, fica mais intuitivo
        related_name='conta_detalhada'
    )
    imposto_taxas_contribuicoes = models.FloatField()
    contribuicoes = models.FloatField()
    transferencias_correntes = models.FloatField()
    outras_receita = models.FloatField()

    def _calcular_pc(self, valor):
        """Método auxiliar para evitar repetição e tratar divisão por zero."""
        if self.municipio.populacao23 and self.municipio.populacao23 > 0:
            return valor / self.municipio.populacao23
        return 0
    
    @property
    def imposto_taxas_contribuicoes_pc(self):
        return self._calcular_pc(self.imposto_taxas_contribuicoes)

    @property
    def contribuicoes_pc(self):
        return self._calcular_pc(self.contribuicoes)

    @property
    def transferencias_correntes_pc(self):
        return self._calcular_pc(self.transferencias_correntes)
        
    @property
    def outras_receita_pc(self):
        return self._calcular_pc(self.outras_receita)
    

    def __str__(self):
        return f"Receita Detalhada de {self.municipio.name_muni_uf}"
    


class ContaDetalhadaPercentil(models.Model):
    municipio = models.OneToOneField(
        Municipio,
        to_field='cod_ibge',
        on_delete=models.CASCADE,
        primary_key=True,  # Altamente recomendado!
        # Sugestão: renomeie para um nome no singular, fica mais intuitivo
        related_name='conta_detalhada_percentil'
    )

    # Nacional
    imposto_taxas_contribuicoes_nacional = models.FloatField()
    contribuicoes_nacional = models.FloatField()
    transferencias_correntes_nacional = models.FloatField()
    outras_receita_nacional = models.FloatField()

    # Regional
    imposto_taxas_contribuicoes_regional = models.FloatField()
    contribuicoes_regional = models.FloatField()
    transferencias_correntes_regional = models.FloatField()
    outras_receita_regional = models.FloatField()

    # Estadual
    imposto_taxas_contribuicoes_estadual = models.FloatField()
    contribuicoes_estadual = models.FloatField()
    transferencias_correntes_estadual = models.FloatField()
    outras_receita_estadual = models.FloatField()


    def __str__(self):
        return f"Receita Detalhada Percentil de {self.municipio.name_muni_uf}"




class ContaEspecifica(models.Model):
    # Troque ForeignKey por OneToOneField
    municipio = models.OneToOneField(
        Municipio,
        to_field='cod_ibge',
        on_delete=models.CASCADE,
        primary_key=True,  # Altamente recomendado!
        # Sugestão: renomeie para um nome no singular, fica mais intuitivo
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
        """Método auxiliar para evitar repetição e tratar divisão por zero."""
        if self.municipio.populacao23 and self.municipio.populacao23 > 0:
            return valor / self.municipio.populacao23
        return 0

    @property
    def imposto_pc(self):
        return self._calcular_pc(self.imposto)

    @property
    def taxas_pc(self):
        return self._calcular_pc(self.taxas)

    @property
    def contribuicoes_melhoria_pc(self):
        return self._calcular_pc(self.contribuicoes_melhoria)
        
    @property
    def contribuicoes_sociais_pc(self):
        return self._calcular_pc(self.contribuicoes_sociais)
    
    @property
    def contribuicoes_iluminacao_publica_pc(self):
        return self._calcular_pc(self.contribuicoes_iluminacao_publica)
    
    @property
    def outras_contribuicoes_pc(self):
        return self._calcular_pc(self.outras_contribuicoes)

    @property
    def tranferencias_uniao_pc(self):
        return self._calcular_pc(self.tranferencias_uniao)

    @property
    def tranferencias_estados_pc(self):
        return self._calcular_pc(self.tranferencias_estados)
        
    @property
    def outras_tranferencias_pc(self):
        return self._calcular_pc(self.outras_tranferencias)
    
    @property
    def receita_patrimonial_pc(self):
        return self._calcular_pc(self.receita_patrimonial)

    @property
    def receita_agropecuaria_pc(self):
        return self._calcular_pc(self.receita_agropecuaria)

    @property
    def receita_industrial_pc(self):
        return self._calcular_pc(self.receita_industrial)
    
    @property
    def receita_servicos_pc(self):
        return self._calcular_pc(self.receita_servicos)
        
    @property
    def outras_receitas_pc(self):
        return self._calcular_pc(self.outras_receitas)

    
    def __str__(self):
        return f"Receita Específica de {self.municipio.name_muni_uf}"


class ContaEspecificaPercentil(models.Model):
    # Troque ForeignKey por OneToOneField
    municipio = models.OneToOneField(
        Municipio,
        to_field='cod_ibge',
        on_delete=models.CASCADE,
        primary_key=True,  # Altamente recomendado!
        # Sugestão: renomeie para um nome no singular, fica mais intuitivo
        related_name='conta_especifica_percentil'
    )

    # Nacional
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


    # Regional
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

    # Estadual
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
    # Troque ForeignKey por OneToOneField
    municipio = models.OneToOneField(
        Municipio,
        to_field='cod_ibge',
        on_delete=models.CASCADE,
        primary_key=True,  # Altamente recomendado!
        # Sugestão: renomeie para um nome no singular, fica mais intuitivo
        related_name='conta_mais_especifica'
    )
    # Imposto
    iptu = models.FloatField()
    itbi = models.FloatField()
    iss = models.FloatField()
    outros_impostos = models.FloatField()
    # Taxa
    taxa_policia = models.FloatField()
    taxa_prestacao_servico = models.FloatField()
    outras_taxas = models.FloatField()
    # Contribuicao Melhoria
    contribuicao_melhoria_pavimento_obras = models.FloatField()
    contribuicao_melhoria_agua_potavel = models.FloatField()
    contribuicao_melhoria_iluminacao_publica = models.FloatField()
    outras_contribuicoes_melhoria = models.FloatField()
    # Transferencia Uniao
    transferencia_uniao_fpm = models.FloatField()
    transferencia_uniao_exploracao = models.FloatField()
    transferencia_uniao_sus = models.FloatField()
    transferencia_uniao_fnde = models.FloatField()
    transferencia_uniao_fnas = models.FloatField()
    outras_transferencias_uniao = models.FloatField()
    # Transferencia Estado
    transferencia_estado_icms = models.FloatField()
    transferencia_estado_ipva = models.FloatField()
    transferencia_estado_exploracao = models.FloatField()
    transferencia_estado_sus = models.FloatField()
    transferencia_estado_assistencia = models.FloatField()
    outras_transferencias_estado = models.FloatField()



    def _calcular_pc(self, valor):
        """Método auxiliar para evitar repetição e tratar divisão por zero."""
        if self.municipio.populacao23 and self.municipio.populacao23 > 0:
            return valor / self.municipio.populacao23
        return 0
    
    # Imposto
    @property
    def iptu_pc(self):
        return self._calcular_pc(self.iptu)

    @property
    def itbi_pc(self):
        return self._calcular_pc(self.itbi)

    @property
    def iss_pc(self):
        return self._calcular_pc(self.iss)
        
    @property
    def outros_impostos_pc(self):
        return self._calcular_pc(self.outros_impostos)
    
    # Taxa
    @property
    def taxa_policia_pc(self):
        return self._calcular_pc(self.taxa_policia)

    @property
    def taxa_prestacao_servico_pc(self):
        return self._calcular_pc(self.taxa_prestacao_servico)

    @property
    def outras_taxas_pc(self):
        return self._calcular_pc(self.outras_taxas)
    
    # Contribuicao Melhoria
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
    
    # Transferencia União
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
    def transferencia_uniao_fnas_pc(self):
        return self._calcular_pc(self.transferencia_uniao_fnas)
    
    @property
    def outras_transferencias_uniao_pc(self):
        return self._calcular_pc(self.outras_transferencias_uniao)
    
    # Transferencia Estado
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
    # Troque ForeignKey por OneToOneField
    municipio = models.OneToOneField(
        Municipio,
        to_field='cod_ibge',
        on_delete=models.CASCADE,
        primary_key=True,  # Altamente recomendado!
        # Sugestão: renomeie para um nome no singular, fica mais intuitivo
        related_name='conta_mais_especifica_percentil'
    )

    # Nacional
    iptu_nacional = models.FloatField()
    itbi_nacional = models.FloatField()
    iss_nacional = models.FloatField()
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
    transferencia_uniao_fnas_nacional = models.FloatField()
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
    transferencia_uniao_fnas_regional = models.FloatField()
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
    transferencia_uniao_fnas_estadual = models.FloatField()
    outras_transferencias_uniao_estadual = models.FloatField()
    transferencia_estado_icms_estadual = models.FloatField()
    transferencia_estado_ipva_estadual = models.FloatField()
    transferencia_estado_exploracao_estadual = models.FloatField()
    transferencia_estado_sus_estadual = models.FloatField()
    transferencia_estado_assistencia_estadual = models.FloatField()
    outras_transferencias_estado_estadual = models.FloatField()


    
    def __str__(self):
        return f"Receita Mais Específica Percentil de {self.municipio.name_muni_uf}"