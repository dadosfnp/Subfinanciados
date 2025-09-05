# detail/serializers.py
from rest_framework import serializers
from home.models import (
    Municipio,
    ContaDetalhadaPercentil,
    ContaEspecifica,
    ContaEspecificaPercentil,
    ContaMaisEspecifica,
    ContaMaisEspecificaPercentil
)

class ContaMaisEspecificaSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo ContaMaisEspecifica, incluindo valores brutos e formatados.
    """
    # Campos de valor brutos
    iptu_abs = serializers.FloatField(source='iptu')
    itbi_abs = serializers.FloatField(source='itbi')
    iss_abs = serializers.FloatField(source='iss')
    outros_impostos_abs = serializers.FloatField(source='outros_impostos')
    taxa_policia_abs = serializers.FloatField(source='taxa_policia')
    taxa_prestacao_servico_abs = serializers.FloatField(source='taxa_prestacao_servico')
    outras_taxas_abs = serializers.FloatField(source='outras_taxas')
    contribuicao_melhoria_pavimento_obras_abs = serializers.FloatField(source='contribuicao_melhoria_pavimento_obras')
    contribuicao_melhoria_agua_potavel_abs = serializers.FloatField(source='contribuicao_melhoria_agua_potavel')
    contribuicao_melhoria_iluminacao_publica_abs = serializers.FloatField(source='contribuicao_melhoria_iluminacao_publica')
    outras_contribuicoes_melhoria_abs = serializers.FloatField(source='outras_contribuicoes_melhoria')
    transferencia_uniao_fpm_abs = serializers.FloatField(source='transferencia_uniao_fpm')
    transferencia_uniao_exploracao_abs = serializers.FloatField(source='transferencia_uniao_exploracao')
    transferencia_uniao_sus_abs = serializers.FloatField(source='transferencia_uniao_sus')
    transferencia_uniao_fnde_abs = serializers.FloatField(source='transferencia_uniao_fnde')
    transferencia_uniao_fnas_abs = serializers.FloatField(source='transferencia_uniao_fnas')
    outras_transferencias_uniao_abs = serializers.FloatField(source='outras_transferencias_uniao')
    transferencia_estado_icms_abs = serializers.FloatField(source='transferencia_estado_icms')
    transferencia_estado_ipva_abs = serializers.FloatField(source='transferencia_estado_ipva')
    transferencia_estado_exploracao_abs = serializers.FloatField(source='transferencia_estado_exploracao')
    transferencia_estado_sus_abs = serializers.FloatField(source='transferencia_estado_sus')
    transferencia_estado_assistencia_abs = serializers.FloatField(source='transferencia_estado_assistencia')
    outras_transferencias_estado_abs = serializers.FloatField(source='outras_transferencias_estado')

    # Campos per capita, usando as @properties do modelo
    iptu_pc = serializers.FloatField()
    itbi_pc = serializers.FloatField()
    iss_pc = serializers.FloatField()
    outros_impostos_pc = serializers.FloatField()
    taxa_policia_pc = serializers.FloatField()
    taxa_prestacao_servico_pc = serializers.FloatField()
    outras_taxas_pc = serializers.FloatField()
    contribuicao_melhoria_pavimento_obras_pc = serializers.FloatField()
    contribuicao_melhoria_agua_potavel_pc = serializers.FloatField()
    contribuicao_melhoria_iluminacao_publica_pc = serializers.FloatField()
    outras_contribuicoes_melhoria_pc = serializers.FloatField()
    transferencia_uniao_fpm_pc = serializers.FloatField()
    transferencia_uniao_exploracao_pc = serializers.FloatField()
    transferencia_uniao_sus_pc = serializers.FloatField()
    transferencia_uniao_fnde_pc = serializers.FloatField()
    transferencia_uniao_fnas_pc = serializers.FloatField()
    outras_transferencias_uniao_pc = serializers.FloatField()
    transferencia_estado_icms_pc = serializers.FloatField()
    transferencia_estado_ipva_pc = serializers.FloatField()
    transferencia_estado_exploracao_pc = serializers.FloatField()
    transferencia_estado_sus_pc = serializers.FloatField()
    transferencia_estado_assistencia_pc = serializers.FloatField()
    outras_transferencias_estado_pc = serializers.FloatField()

    class Meta:
        model = ContaMaisEspecifica
        # Usamos fields '__all__' para puxar todos os campos do modelo,
        # e os SerializerMethodField e @properties garantem a inclusão dos campos formatados/calculados.
        fields = '__all__'


class ContaEspecificaSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo ContaEspecifica, incluindo o serializer aninhado.
    """
    # Aninha o serializer de ContaMaisEspecifica
    conta_mais_especifica = ContaMaisEspecificaSerializer(read_only=True)

    # Campos de valor brutos
    imposto_abs = serializers.FloatField(source='imposto')
    taxas_abs = serializers.FloatField(source='taxas')
    contribuicoes_abs = serializers.FloatField(source='contribuicoes')
    contribuicoes_sociais_abs = serializers.FloatField(source='contribuicoes_sociais')
    contribuicoes_iluminacao_publica_abs = serializers.FloatField(source='contribuicoes_iluminacao_publica')
    outras_contribuicoes_abs = serializers.FloatField(source='outras_contribuicoes')
    tranferencias_uniao_abs = serializers.FloatField(source='tranferencias_uniao')
    tranferencias_estados_abs = serializers.FloatField(source='tranferencias_estados')
    outras_tranferencias_abs = serializers.FloatField(source='outras_tranferencias')
    receita_patrimonial_abs = serializers.FloatField(source='receita_patrimonial')
    receita_agropecuaria_abs = serializers.FloatField(source='receita_agropecuaria')
    receita_industrial_abs = serializers.FloatField(source='receita_industrial')
    receita_servicos_abs = serializers.FloatField(source='receita_servicos')
    outras_receitas_abs = serializers.FloatField(source='outras_receitas')

    # Campos per capita, usando as @properties do modelo
    imposto_pc = serializers.FloatField()
    taxas_pc = serializers.FloatField()
    contribuicoes_pc = serializers.FloatField()
    contribuicoes_sociais_pc = serializers.FloatField()
    contribuicoes_iluminacao_publica_pc = serializers.FloatField()
    tranferencias_uniao_pc = serializers.FloatField()
    tranferencias_estados_pc = serializers.FloatField()
    outras_tranferencias_pc = serializers.FloatField()
    receita_patrimonial_pc = serializers.FloatField()
    receita_agropecuaria_pc = serializers.FloatField()
    receita_industrial_pc = serializers.FloatField()
    receita_servicos_pc = serializers.FloatField()
    outras_receitas_pc = serializers.FloatField()

    class Meta:
        model = ContaEspecifica
        fields = '__all__'


class ContaMaisEspecificaPercentilSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo ContaMaisEspecificaPercentil.
    """
    class Meta:
        model = ContaMaisEspecificaPercentil
        # Puxa todos os campos de percentil que você listou no seu modelo
        fields = '__all__'


class ContaEspecificaPercentilSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo ContaEspecificaPercentil.
    """
    # Aninha o serializer do próximo nível
    conta_mais_especifica_percentil = ContaMaisEspecificaPercentilSerializer(read_only=True)
    
    class Meta:
        model = ContaEspecificaPercentil
        fields = '__all__'


class ContaDetalhadaPercentilSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo ContaDetalhadaPercentil.
    """
    # Aninha o serializer do próximo nível
    conta_especifica_percentil = ContaEspecificaPercentilSerializer(read_only=True)
    
    class Meta:
        model = ContaDetalhadaPercentil
        fields = '__all__'


class MunicipioPercentilSerializer(serializers.ModelSerializer):
    """
    Serializer principal para o modelo Municipio, unindo todos os dados.
    """
    # Adiciona os serializers aninhados
    conta_mais_especifica_percentil = ContaMaisEspecificaPercentilSerializer(read_only=True, source='conta_mais_especifica_percentil')
    conta_detalhada_percentil = ContaDetalhadaPercentilSerializer(read_only=True)
    conta_especifica_percentil = ContaEspecificaPercentilSerializer(read_only=True)
    
    # Adiciona os dados de valor (brutos e per capita)
    conta_mais_especifica = ContaMaisEspecificaSerializer(read_only=True)
    conta_especifica = ContaEspecificaSerializer(read_only=True)

    # Campos de ranking e quintil
    rank_nacional = serializers.IntegerField(source='rank_nacional', default=0)
    total_nacional = serializers.IntegerField(source='total_nacional', default=0)
    rank_estadual = serializers.IntegerField(source='rank_estadual', default=0)
    total_estadual = serializers.IntegerField(source='total_estadual', default=0)
    rank_faixa = serializers.IntegerField(source='rank_faixa', default=0)
    total_faixa = serializers.IntegerField(source='total_faixa', default=0)

    # RC per capita e quintil do município (diretamente do modelo Municipio)
    rc_23_pc = serializers.FloatField()
    quintil23 = serializers.CharField()
    
    class Meta:
        model = Municipio
        # Lista todos os campos brutos e aninhados que você quer no JSON final
        fields = [
            'id', 'nome', 'populacao23',
            'rc_23_pc', 'quintil23',
            'rank_nacional', 'total_nacional',
            'rank_estadual', 'total_estadual',
            'rank_faixa', 'total_faixa',
            'conta_detalhada_percentil',
            'conta_especifica',
            'conta_mais_especifica',
            'conta_especifica_percentil',
            'conta_mais_especifica_percentil'
        ]