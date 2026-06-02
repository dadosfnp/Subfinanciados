# Dicionário de Dados — IFEM/Subfinanciados

> **Gerado automaticamente** por `python manage.py gerar_dicionario`. Não edite à mão — rode o comando novamente após alterar os models.

Legenda: **PK** = chave primária · **Índice** inclui PK/único/`db_index` · **FK →** tabela referenciada.


## App: `home`

### `home_contadetalhada` — ContaDetalhada

| Coluna | Atributo | Tipo | Nulo | Índice | Único | FK → | Descrição |
|---|---|---|---|---|---|---|---|
| `municipio_id` | municipio 🔑 | OneToOneField | — | ✓ | ✓ |  | municipio |
| `imposto_taxas_contribuicoes` | imposto_taxas_contribuicoes | FloatField | — | — | — |  | imposto taxas contribuicoes |
| `contribuicoes` | contribuicoes | FloatField | — | — | — |  | contribuicoes |
| `transferencias_correntes` | transferencias_correntes | FloatField | — | — | — |  | transferencias correntes |
| `outras_receita` | outras_receita | FloatField | — | — | — |  | outras receita |

### `home_contadetalhadapercentil` — ContaDetalhadaPercentil

| Coluna | Atributo | Tipo | Nulo | Índice | Único | FK → | Descrição |
|---|---|---|---|---|---|---|---|
| `municipio_id` | municipio 🔑 | OneToOneField | — | ✓ | ✓ |  | municipio |
| `imposto_taxas_contribuicoes_nacional` | imposto_taxas_contribuicoes_nacional | FloatField | — | — | — |  | imposto taxas contribuicoes nacional |
| `contribuicoes_nacional` | contribuicoes_nacional | FloatField | — | — | — |  | contribuicoes nacional |
| `transferencias_correntes_nacional` | transferencias_correntes_nacional | FloatField | — | — | — |  | transferencias correntes nacional |
| `outras_receita_nacional` | outras_receita_nacional | FloatField | — | — | — |  | outras receita nacional |
| `imposto_taxas_contribuicoes_regional` | imposto_taxas_contribuicoes_regional | FloatField | — | — | — |  | imposto taxas contribuicoes regional |
| `contribuicoes_regional` | contribuicoes_regional | FloatField | — | — | — |  | contribuicoes regional |
| `transferencias_correntes_regional` | transferencias_correntes_regional | FloatField | — | — | — |  | transferencias correntes regional |
| `outras_receita_regional` | outras_receita_regional | FloatField | — | — | — |  | outras receita regional |
| `imposto_taxas_contribuicoes_estadual` | imposto_taxas_contribuicoes_estadual | FloatField | — | — | — |  | imposto taxas contribuicoes estadual |
| `contribuicoes_estadual` | contribuicoes_estadual | FloatField | — | — | — |  | contribuicoes estadual |
| `transferencias_correntes_estadual` | transferencias_correntes_estadual | FloatField | — | — | — |  | transferencias correntes estadual |
| `outras_receita_estadual` | outras_receita_estadual | FloatField | — | — | — |  | outras receita estadual |

### `home_contaespecifica` — ContaEspecifica

| Coluna | Atributo | Tipo | Nulo | Índice | Único | FK → | Descrição |
|---|---|---|---|---|---|---|---|
| `municipio_id` | municipio 🔑 | OneToOneField | — | ✓ | ✓ |  | municipio |
| `imposto` | imposto | FloatField | — | — | — |  | imposto |
| `taxas` | taxas | FloatField | — | — | — |  | taxas |
| `contribuicoes_melhoria` | contribuicoes_melhoria | FloatField | — | — | — |  | contribuicoes melhoria |
| `contribuicoes_sociais` | contribuicoes_sociais | FloatField | — | — | — |  | contribuicoes sociais |
| `contribuicoes_iluminacao_publica` | contribuicoes_iluminacao_publica | FloatField | — | — | — |  | contribuicoes iluminacao publica |
| `outras_contribuicoes` | outras_contribuicoes | FloatField | — | — | — |  | outras contribuicoes |
| `tranferencias_uniao` | tranferencias_uniao | FloatField | — | — | — |  | tranferencias uniao |
| `tranferencias_estados` | tranferencias_estados | FloatField | — | — | — |  | tranferencias estados |
| `outras_tranferencias` | outras_tranferencias | FloatField | — | — | — |  | outras tranferencias |
| `receita_patrimonial` | receita_patrimonial | FloatField | — | — | — |  | receita patrimonial |
| `receita_agropecuaria` | receita_agropecuaria | FloatField | — | — | — |  | receita agropecuaria |
| `receita_industrial` | receita_industrial | FloatField | — | — | — |  | receita industrial |
| `receita_servicos` | receita_servicos | FloatField | — | — | — |  | receita servicos |
| `outras_receitas` | outras_receitas | FloatField | — | — | — |  | outras receitas |

### `home_contaespecificapercentil` — ContaEspecificaPercentil

| Coluna | Atributo | Tipo | Nulo | Índice | Único | FK → | Descrição |
|---|---|---|---|---|---|---|---|
| `municipio_id` | municipio 🔑 | OneToOneField | — | ✓ | ✓ |  | municipio |
| `imposto_nacional` | imposto_nacional | FloatField | — | — | — |  | imposto nacional |
| `taxas_nacional` | taxas_nacional | FloatField | — | — | — |  | taxas nacional |
| `contribuicoes_melhoria_nacional` | contribuicoes_melhoria_nacional | FloatField | — | — | — |  | contribuicoes melhoria nacional |
| `contribuicoes_sociais_nacional` | contribuicoes_sociais_nacional | FloatField | — | — | — |  | contribuicoes sociais nacional |
| `contribuicoes_iluminacao_publica_nacional` | contribuicoes_iluminacao_publica_nacional | FloatField | — | — | — |  | contribuicoes iluminacao publica nacional |
| `outras_contribuicoes_nacional` | outras_contribuicoes_nacional | FloatField | — | — | — |  | outras contribuicoes nacional |
| `tranferencias_uniao_nacional` | tranferencias_uniao_nacional | FloatField | — | — | — |  | tranferencias uniao nacional |
| `tranferencias_estados_nacional` | tranferencias_estados_nacional | FloatField | — | — | — |  | tranferencias estados nacional |
| `outras_tranferencias_nacional` | outras_tranferencias_nacional | FloatField | — | — | — |  | outras tranferencias nacional |
| `receita_patrimonial_nacional` | receita_patrimonial_nacional | FloatField | — | — | — |  | receita patrimonial nacional |
| `receita_agropecuaria_nacional` | receita_agropecuaria_nacional | FloatField | — | — | — |  | receita agropecuaria nacional |
| `receita_industrial_nacional` | receita_industrial_nacional | FloatField | — | — | — |  | receita industrial nacional |
| `receita_servicos_nacional` | receita_servicos_nacional | FloatField | — | — | — |  | receita servicos nacional |
| `outras_receitas_nacional` | outras_receitas_nacional | FloatField | — | — | — |  | outras receitas nacional |
| `imposto_regional` | imposto_regional | FloatField | — | — | — |  | imposto regional |
| `taxas_regional` | taxas_regional | FloatField | — | — | — |  | taxas regional |
| `contribuicoes_melhoria_regional` | contribuicoes_melhoria_regional | FloatField | — | — | — |  | contribuicoes melhoria regional |
| `contribuicoes_sociais_regional` | contribuicoes_sociais_regional | FloatField | — | — | — |  | contribuicoes sociais regional |
| `contribuicoes_iluminacao_publica_regional` | contribuicoes_iluminacao_publica_regional | FloatField | — | — | — |  | contribuicoes iluminacao publica regional |
| `outras_contribuicoes_regional` | outras_contribuicoes_regional | FloatField | — | — | — |  | outras contribuicoes regional |
| `tranferencias_uniao_regional` | tranferencias_uniao_regional | FloatField | — | — | — |  | tranferencias uniao regional |
| `tranferencias_estados_regional` | tranferencias_estados_regional | FloatField | — | — | — |  | tranferencias estados regional |
| `outras_tranferencias_regional` | outras_tranferencias_regional | FloatField | — | — | — |  | outras tranferencias regional |
| `receita_patrimonial_regional` | receita_patrimonial_regional | FloatField | — | — | — |  | receita patrimonial regional |
| `receita_agropecuaria_regional` | receita_agropecuaria_regional | FloatField | — | — | — |  | receita agropecuaria regional |
| `receita_industrial_regional` | receita_industrial_regional | FloatField | — | — | — |  | receita industrial regional |
| `receita_servicos_regional` | receita_servicos_regional | FloatField | — | — | — |  | receita servicos regional |
| `outras_receitas_regional` | outras_receitas_regional | FloatField | — | — | — |  | outras receitas regional |
| `imposto_estadual` | imposto_estadual | FloatField | — | — | — |  | imposto estadual |
| `taxas_estadual` | taxas_estadual | FloatField | — | — | — |  | taxas estadual |
| `contribuicoes_melhoria_estadual` | contribuicoes_melhoria_estadual | FloatField | — | — | — |  | contribuicoes melhoria estadual |
| `contribuicoes_sociais_estadual` | contribuicoes_sociais_estadual | FloatField | — | — | — |  | contribuicoes sociais estadual |
| `contribuicoes_iluminacao_publica_estadual` | contribuicoes_iluminacao_publica_estadual | FloatField | — | — | — |  | contribuicoes iluminacao publica estadual |
| `outras_contribuicoes_estadual` | outras_contribuicoes_estadual | FloatField | — | — | — |  | outras contribuicoes estadual |
| `tranferencias_uniao_estadual` | tranferencias_uniao_estadual | FloatField | — | — | — |  | tranferencias uniao estadual |
| `tranferencias_estados_estadual` | tranferencias_estados_estadual | FloatField | — | — | — |  | tranferencias estados estadual |
| `outras_tranferencias_estadual` | outras_tranferencias_estadual | FloatField | — | — | — |  | outras tranferencias estadual |
| `receita_patrimonial_estadual` | receita_patrimonial_estadual | FloatField | — | — | — |  | receita patrimonial estadual |
| `receita_agropecuaria_estadual` | receita_agropecuaria_estadual | FloatField | — | — | — |  | receita agropecuaria estadual |
| `receita_industrial_estadual` | receita_industrial_estadual | FloatField | — | — | — |  | receita industrial estadual |
| `receita_servicos_estadual` | receita_servicos_estadual | FloatField | — | — | — |  | receita servicos estadual |
| `outras_receitas_estadual` | outras_receitas_estadual | FloatField | — | — | — |  | outras receitas estadual |

### `home_contamaisespecifica` — ContaMaisEspecifica

| Coluna | Atributo | Tipo | Nulo | Índice | Único | FK → | Descrição |
|---|---|---|---|---|---|---|---|
| `municipio_id` | municipio 🔑 | OneToOneField | — | ✓ | ✓ |  | municipio |
| `iptu` | iptu | FloatField | — | — | — |  | iptu |
| `itbi` | itbi | FloatField | — | — | — |  | itbi |
| `iss` | iss | FloatField | — | — | — |  | iss |
| `imposto_renda` | imposto_renda | FloatField | — | — | — |  | imposto renda |
| `imposto_icms` | imposto_icms | FloatField | — | — | — |  | imposto icms |
| `imposto_ipva` | imposto_ipva | FloatField | — | — | — |  | imposto ipva |
| `outros_impostos` | outros_impostos | FloatField | — | — | — |  | outros impostos |
| `taxa_policia` | taxa_policia | FloatField | — | — | — |  | taxa policia |
| `taxa_prestacao_servico` | taxa_prestacao_servico | FloatField | — | — | — |  | taxa prestacao servico |
| `outras_taxas` | outras_taxas | FloatField | — | — | — |  | outras taxas |
| `contribuicao_melhoria_pavimento_obras` | contribuicao_melhoria_pavimento_obras | FloatField | — | — | — |  | contribuicao melhoria pavimento obras |
| `contribuicao_melhoria_agua_potavel` | contribuicao_melhoria_agua_potavel | FloatField | — | — | — |  | contribuicao melhoria agua potavel |
| `contribuicao_melhoria_iluminacao_publica` | contribuicao_melhoria_iluminacao_publica | FloatField | — | — | — |  | contribuicao melhoria iluminacao publica |
| `outras_contribuicoes_melhoria` | outras_contribuicoes_melhoria | FloatField | — | — | — |  | outras contribuicoes melhoria |
| `transferencia_uniao_fpm` | transferencia_uniao_fpm | FloatField | — | — | — |  | transferencia uniao fpm |
| `transferencia_uniao_exploracao` | transferencia_uniao_exploracao | FloatField | — | — | — |  | transferencia uniao exploracao |
| `transferencia_uniao_sus` | transferencia_uniao_sus | FloatField | — | — | — |  | transferencia uniao sus |
| `transferencia_uniao_fnde` | transferencia_uniao_fnde | FloatField | — | — | — |  | transferencia uniao fnde |
| `transferencia_uniao_fundeb` | transferencia_uniao_fundeb | FloatField | — | — | — |  | transferencia uniao fundeb |
| `transferencia_uniao_fnas` | transferencia_uniao_fnas | FloatField | — | — | — |  | transferencia uniao fnas |
| `transferencia_uniao_fpe` | transferencia_uniao_fpe | FloatField | — | — | — |  | transferencia uniao fpe |
| `outras_transferencias_uniao` | outras_transferencias_uniao | FloatField | — | — | — |  | outras transferencias uniao |
| `transferencia_estado_icms` | transferencia_estado_icms | FloatField | — | — | — |  | transferencia estado icms |
| `transferencia_estado_ipva` | transferencia_estado_ipva | FloatField | — | — | — |  | transferencia estado ipva |
| `transferencia_estado_exploracao` | transferencia_estado_exploracao | FloatField | — | — | — |  | transferencia estado exploracao |
| `transferencia_estado_sus` | transferencia_estado_sus | FloatField | — | — | — |  | transferencia estado sus |
| `transferencia_estado_assistencia` | transferencia_estado_assistencia | FloatField | — | — | — |  | transferencia estado assistencia |
| `outras_transferencias_estado` | outras_transferencias_estado | FloatField | — | — | — |  | outras transferencias estado |

### `home_contamaisespecificapercentil` — ContaMaisEspecificaPercentil

| Coluna | Atributo | Tipo | Nulo | Índice | Único | FK → | Descrição |
|---|---|---|---|---|---|---|---|
| `municipio_id` | municipio 🔑 | OneToOneField | — | ✓ | ✓ |  | municipio |
| `iptu_nacional` | iptu_nacional | FloatField | — | — | — |  | iptu nacional |
| `itbi_nacional` | itbi_nacional | FloatField | — | — | — |  | itbi nacional |
| `iss_nacional` | iss_nacional | FloatField | — | — | — |  | iss nacional |
| `imposto_renda_nacional` | imposto_renda_nacional | FloatField | — | — | — |  | imposto renda nacional |
| `imposto_icms_nacional` | imposto_icms_nacional | FloatField | — | — | — |  | imposto icms nacional |
| `imposto_ipva_nacional` | imposto_ipva_nacional | FloatField | — | — | — |  | imposto ipva nacional |
| `outros_impostos_nacional` | outros_impostos_nacional | FloatField | — | — | — |  | outros impostos nacional |
| `taxa_policia_nacional` | taxa_policia_nacional | FloatField | — | — | — |  | taxa policia nacional |
| `taxa_prestacao_servico_nacional` | taxa_prestacao_servico_nacional | FloatField | — | — | — |  | taxa prestacao servico nacional |
| `outras_taxas_nacional` | outras_taxas_nacional | FloatField | — | — | — |  | outras taxas nacional |
| `contribuicao_melhoria_pavimento_obras_nacional` | contribuicao_melhoria_pavimento_obras_nacional | FloatField | — | — | — |  | contribuicao melhoria pavimento obras nacional |
| `contribuicao_melhoria_agua_potavel_nacional` | contribuicao_melhoria_agua_potavel_nacional | FloatField | — | — | — |  | contribuicao melhoria agua potavel nacional |
| `contribuicao_melhoria_iluminacao_publica_nacional` | contribuicao_melhoria_iluminacao_publica_nacional | FloatField | — | — | — |  | contribuicao melhoria iluminacao publica nacional |
| `outras_contribuicoes_melhoria_nacional` | outras_contribuicoes_melhoria_nacional | FloatField | — | — | — |  | outras contribuicoes melhoria nacional |
| `transferencia_uniao_fpm_nacional` | transferencia_uniao_fpm_nacional | FloatField | — | — | — |  | transferencia uniao fpm nacional |
| `transferencia_uniao_exploracao_nacional` | transferencia_uniao_exploracao_nacional | FloatField | — | — | — |  | transferencia uniao exploracao nacional |
| `transferencia_uniao_sus_nacional` | transferencia_uniao_sus_nacional | FloatField | — | — | — |  | transferencia uniao sus nacional |
| `transferencia_uniao_fnde_nacional` | transferencia_uniao_fnde_nacional | FloatField | — | — | — |  | transferencia uniao fnde nacional |
| `transferencia_uniao_fundeb_nacional` | transferencia_uniao_fundeb_nacional | FloatField | — | — | — |  | transferencia uniao fundeb nacional |
| `transferencia_uniao_fnas_nacional` | transferencia_uniao_fnas_nacional | FloatField | — | — | — |  | transferencia uniao fnas nacional |
| `transferencia_uniao_fpe_nacional` | transferencia_uniao_fpe_nacional | FloatField | — | — | — |  | transferencia uniao fpe nacional |
| `outras_transferencias_uniao_nacional` | outras_transferencias_uniao_nacional | FloatField | — | — | — |  | outras transferencias uniao nacional |
| `transferencia_estado_icms_nacional` | transferencia_estado_icms_nacional | FloatField | — | — | — |  | transferencia estado icms nacional |
| `transferencia_estado_ipva_nacional` | transferencia_estado_ipva_nacional | FloatField | — | — | — |  | transferencia estado ipva nacional |
| `transferencia_estado_exploracao_nacional` | transferencia_estado_exploracao_nacional | FloatField | — | — | — |  | transferencia estado exploracao nacional |
| `transferencia_estado_sus_nacional` | transferencia_estado_sus_nacional | FloatField | — | — | — |  | transferencia estado sus nacional |
| `transferencia_estado_assistencia_nacional` | transferencia_estado_assistencia_nacional | FloatField | — | — | — |  | transferencia estado assistencia nacional |
| `outras_transferencias_estado_nacional` | outras_transferencias_estado_nacional | FloatField | — | — | — |  | outras transferencias estado nacional |
| `iptu_regional` | iptu_regional | FloatField | — | — | — |  | iptu regional |
| `itbi_regional` | itbi_regional | FloatField | — | — | — |  | itbi regional |
| `iss_regional` | iss_regional | FloatField | — | — | — |  | iss regional |
| `imposto_renda_regional` | imposto_renda_regional | FloatField | — | — | — |  | imposto renda regional |
| `imposto_icms_regional` | imposto_icms_regional | FloatField | — | — | — |  | imposto icms regional |
| `imposto_ipva_regional` | imposto_ipva_regional | FloatField | — | — | — |  | imposto ipva regional |
| `outros_impostos_regional` | outros_impostos_regional | FloatField | — | — | — |  | outros impostos regional |
| `taxa_policia_regional` | taxa_policia_regional | FloatField | — | — | — |  | taxa policia regional |
| `taxa_prestacao_servico_regional` | taxa_prestacao_servico_regional | FloatField | — | — | — |  | taxa prestacao servico regional |
| `outras_taxas_regional` | outras_taxas_regional | FloatField | — | — | — |  | outras taxas regional |
| `contribuicao_melhoria_pavimento_obras_regional` | contribuicao_melhoria_pavimento_obras_regional | FloatField | — | — | — |  | contribuicao melhoria pavimento obras regional |
| `contribuicao_melhoria_agua_potavel_regional` | contribuicao_melhoria_agua_potavel_regional | FloatField | — | — | — |  | contribuicao melhoria agua potavel regional |
| `contribuicao_melhoria_iluminacao_publica_regional` | contribuicao_melhoria_iluminacao_publica_regional | FloatField | — | — | — |  | contribuicao melhoria iluminacao publica regional |
| `outras_contribuicoes_melhoria_regional` | outras_contribuicoes_melhoria_regional | FloatField | — | — | — |  | outras contribuicoes melhoria regional |
| `transferencia_uniao_fpm_regional` | transferencia_uniao_fpm_regional | FloatField | — | — | — |  | transferencia uniao fpm regional |
| `transferencia_uniao_exploracao_regional` | transferencia_uniao_exploracao_regional | FloatField | — | — | — |  | transferencia uniao exploracao regional |
| `transferencia_uniao_sus_regional` | transferencia_uniao_sus_regional | FloatField | — | — | — |  | transferencia uniao sus regional |
| `transferencia_uniao_fnde_regional` | transferencia_uniao_fnde_regional | FloatField | — | — | — |  | transferencia uniao fnde regional |
| `transferencia_uniao_fundeb_regional` | transferencia_uniao_fundeb_regional | FloatField | — | — | — |  | transferencia uniao fundeb regional |
| `transferencia_uniao_fnas_regional` | transferencia_uniao_fnas_regional | FloatField | — | — | — |  | transferencia uniao fnas regional |
| `transferencia_uniao_fpe_regional` | transferencia_uniao_fpe_regional | FloatField | — | — | — |  | transferencia uniao fpe regional |
| `outras_transferencias_uniao_regional` | outras_transferencias_uniao_regional | FloatField | — | — | — |  | outras transferencias uniao regional |
| `transferencia_estado_icms_regional` | transferencia_estado_icms_regional | FloatField | — | — | — |  | transferencia estado icms regional |
| `transferencia_estado_ipva_regional` | transferencia_estado_ipva_regional | FloatField | — | — | — |  | transferencia estado ipva regional |
| `transferencia_estado_exploracao_regional` | transferencia_estado_exploracao_regional | FloatField | — | — | — |  | transferencia estado exploracao regional |
| `transferencia_estado_sus_regional` | transferencia_estado_sus_regional | FloatField | — | — | — |  | transferencia estado sus regional |
| `transferencia_estado_assistencia_regional` | transferencia_estado_assistencia_regional | FloatField | — | — | — |  | transferencia estado assistencia regional |
| `outras_transferencias_estado_regional` | outras_transferencias_estado_regional | FloatField | — | — | — |  | outras transferencias estado regional |
| `iptu_estadual` | iptu_estadual | FloatField | — | — | — |  | iptu estadual |
| `itbi_estadual` | itbi_estadual | FloatField | — | — | — |  | itbi estadual |
| `iss_estadual` | iss_estadual | FloatField | — | — | — |  | iss estadual |
| `imposto_renda_estadual` | imposto_renda_estadual | FloatField | — | — | — |  | imposto renda estadual |
| `imposto_icms_estadual` | imposto_icms_estadual | FloatField | — | — | — |  | imposto icms estadual |
| `imposto_ipva_estadual` | imposto_ipva_estadual | FloatField | — | — | — |  | imposto ipva estadual |
| `outros_impostos_estadual` | outros_impostos_estadual | FloatField | — | — | — |  | outros impostos estadual |
| `taxa_policia_estadual` | taxa_policia_estadual | FloatField | — | — | — |  | taxa policia estadual |
| `taxa_prestacao_servico_estadual` | taxa_prestacao_servico_estadual | FloatField | — | — | — |  | taxa prestacao servico estadual |
| `outras_taxas_estadual` | outras_taxas_estadual | FloatField | — | — | — |  | outras taxas estadual |
| `contribuicao_melhoria_pavimento_obras_estadual` | contribuicao_melhoria_pavimento_obras_estadual | FloatField | — | — | — |  | contribuicao melhoria pavimento obras estadual |
| `contribuicao_melhoria_agua_potavel_estadual` | contribuicao_melhoria_agua_potavel_estadual | FloatField | — | — | — |  | contribuicao melhoria agua potavel estadual |
| `contribuicao_melhoria_iluminacao_publica_estadual` | contribuicao_melhoria_iluminacao_publica_estadual | FloatField | — | — | — |  | contribuicao melhoria iluminacao publica estadual |
| `outras_contribuicoes_melhoria_estadual` | outras_contribuicoes_melhoria_estadual | FloatField | — | — | — |  | outras contribuicoes melhoria estadual |
| `transferencia_uniao_fpm_estadual` | transferencia_uniao_fpm_estadual | FloatField | — | — | — |  | transferencia uniao fpm estadual |
| `transferencia_uniao_exploracao_estadual` | transferencia_uniao_exploracao_estadual | FloatField | — | — | — |  | transferencia uniao exploracao estadual |
| `transferencia_uniao_sus_estadual` | transferencia_uniao_sus_estadual | FloatField | — | — | — |  | transferencia uniao sus estadual |
| `transferencia_uniao_fnde_estadual` | transferencia_uniao_fnde_estadual | FloatField | — | — | — |  | transferencia uniao fnde estadual |
| `transferencia_uniao_fundeb_estadual` | transferencia_uniao_fundeb_estadual | FloatField | — | — | — |  | transferencia uniao fundeb estadual |
| `transferencia_uniao_fnas_estadual` | transferencia_uniao_fnas_estadual | FloatField | — | — | — |  | transferencia uniao fnas estadual |
| `transferencia_uniao_fpe_estadual` | transferencia_uniao_fpe_estadual | FloatField | — | — | — |  | transferencia uniao fpe estadual |
| `outras_transferencias_uniao_estadual` | outras_transferencias_uniao_estadual | FloatField | — | — | — |  | outras transferencias uniao estadual |
| `transferencia_estado_icms_estadual` | transferencia_estado_icms_estadual | FloatField | — | — | — |  | transferencia estado icms estadual |
| `transferencia_estado_ipva_estadual` | transferencia_estado_ipva_estadual | FloatField | — | — | — |  | transferencia estado ipva estadual |
| `transferencia_estado_exploracao_estadual` | transferencia_estado_exploracao_estadual | FloatField | — | — | — |  | transferencia estado exploracao estadual |
| `transferencia_estado_sus_estadual` | transferencia_estado_sus_estadual | FloatField | — | — | — |  | transferencia estado sus estadual |
| `transferencia_estado_assistencia_estadual` | transferencia_estado_assistencia_estadual | FloatField | — | — | — |  | transferencia estado assistencia estadual |
| `outras_transferencias_estado_estadual` | outras_transferencias_estado_estadual | FloatField | — | — | — |  | outras transferencias estado estadual |

### `home_crescimentomedioporte` — CrescimentoMedioPorte

Entidade de registro unico para armazenamento dos crescimentos médios pre-calculados.
    Estrutura projetada para centralizar metricas agregadas e reduzir processamento em tempo de execucao.


| Coluna | Atributo | Tipo | Nulo | Índice | Único | FK → | Descrição |
|---|---|---|---|---|---|---|---|
| `id` | id 🔑 | BigAutoField | — | ✓ | ✓ |  | ID |
| `ano_referencia` | ano_referencia | IntegerField | — | — | — |  | ano referencia |
| `porte` | porte | CharField(50000) | — | — | — |  | porte |
| `receita` | receita | FloatField | ✓ | — | — |  | receita |
| `populacao` | populacao | FloatField | ✓ | — | — |  | populacao |

### `home_crescimentomediouf` — CrescimentoMedioUf

Entidade de registro unico para armazenamento dos crescimentos médios pre-calculados.
    Estrutura projetada para centralizar metricas agregadas e reduzir processamento em tempo de execucao.


| Coluna | Atributo | Tipo | Nulo | Índice | Único | FK → | Descrição |
|---|---|---|---|---|---|---|---|
| `id` | id 🔑 | BigAutoField | — | ✓ | ✓ |  | ID |
| `ano_referencia` | ano_referencia | IntegerField | — | — | — |  | ano referencia |
| `uf` | uf | CharField(2) | — | — | — |  | uf |
| `receita` | receita | FloatField | ✓ | — | — |  | receita |
| `populacao` | populacao | FloatField | ✓ | — | — |  | populacao |

### `home_medianacionalreceita` — MediaNacionalReceita

Entidade de registro unico para armazenamento das medias nacionais pre-calculadas.
    Estrutura projetada para centralizar metricas agregadas e reduzir processamento em tempo de execucao.


| Coluna | Atributo | Tipo | Nulo | Índice | Único | FK → | Descrição |
|---|---|---|---|---|---|---|---|
| `id` | id 🔑 | BigAutoField | — | ✓ | ✓ |  | ID |
| `ano_referencia` | ano_referencia | IntegerField | — | — | — |  | ano referencia |
| `imposto_taxas_contribuicoes` | imposto_taxas_contribuicoes | FloatField | ✓ | — | — |  | imposto taxas contribuicoes |
| `contribuicoes` | contribuicoes | FloatField | ✓ | — | — |  | contribuicoes |
| `transferencias_correntes` | transferencias_correntes | FloatField | ✓ | — | — |  | transferencias correntes |
| `outras_receita` | outras_receita | FloatField | ✓ | — | — |  | outras receita |
| `imposto` | imposto | FloatField | ✓ | — | — |  | imposto |
| `taxas` | taxas | FloatField | ✓ | — | — |  | taxas |
| `contribuicoes_melhoria` | contribuicoes_melhoria | FloatField | ✓ | — | — |  | contribuicoes melhoria |
| `contribuicoes_sociais` | contribuicoes_sociais | FloatField | ✓ | — | — |  | contribuicoes sociais |
| `contribuicoes_iluminacao_publica` | contribuicoes_iluminacao_publica | FloatField | ✓ | — | — |  | contribuicoes iluminacao publica |
| `outras_contribuicoes` | outras_contribuicoes | FloatField | ✓ | — | — |  | outras contribuicoes |
| `tranferencias_uniao` | tranferencias_uniao | FloatField | ✓ | — | — |  | tranferencias uniao |
| `tranferencias_estados` | tranferencias_estados | FloatField | ✓ | — | — |  | tranferencias estados |
| `outras_tranferencias` | outras_tranferencias | FloatField | ✓ | — | — |  | outras tranferencias |
| `receita_patrimonial` | receita_patrimonial | FloatField | ✓ | — | — |  | receita patrimonial |
| `receita_agropecuaria` | receita_agropecuaria | FloatField | ✓ | — | — |  | receita agropecuaria |
| `receita_industrial` | receita_industrial | FloatField | ✓ | — | — |  | receita industrial |
| `receita_servicos` | receita_servicos | FloatField | ✓ | — | — |  | receita servicos |
| `outras_receitas` | outras_receitas | FloatField | ✓ | — | — |  | outras receitas |
| `iptu` | iptu | FloatField | ✓ | — | — |  | iptu |
| `itbi` | itbi | FloatField | ✓ | — | — |  | itbi |
| `iss` | iss | FloatField | ✓ | — | — |  | iss |
| `imposto_renda` | imposto_renda | FloatField | ✓ | — | — |  | imposto renda |
| `outros_impostos` | outros_impostos | FloatField | ✓ | — | — |  | outros impostos |
| `taxa_policia` | taxa_policia | FloatField | ✓ | — | — |  | taxa policia |
| `taxa_prestacao_servico` | taxa_prestacao_servico | FloatField | ✓ | — | — |  | taxa prestacao servico |
| `outras_taxas` | outras_taxas | FloatField | ✓ | — | — |  | outras taxas |
| `contribuicao_melhoria_pavimento_obras` | contribuicao_melhoria_pavimento_obras | FloatField | ✓ | — | — |  | contribuicao melhoria pavimento obras |
| `contribuicao_melhoria_agua_potavel` | contribuicao_melhoria_agua_potavel | FloatField | ✓ | — | — |  | contribuicao melhoria agua potavel |
| `contribuicao_melhoria_iluminacao_publica` | contribuicao_melhoria_iluminacao_publica | FloatField | ✓ | — | — |  | contribuicao melhoria iluminacao publica |
| `outras_contribuicoes_melhoria` | outras_contribuicoes_melhoria | FloatField | ✓ | — | — |  | outras contribuicoes melhoria |
| `transferencia_uniao_fpm` | transferencia_uniao_fpm | FloatField | ✓ | — | — |  | transferencia uniao fpm |
| `transferencia_uniao_exploracao` | transferencia_uniao_exploracao | FloatField | ✓ | — | — |  | transferencia uniao exploracao |
| `transferencia_uniao_sus` | transferencia_uniao_sus | FloatField | ✓ | — | — |  | transferencia uniao sus |
| `transferencia_uniao_fnde` | transferencia_uniao_fnde | FloatField | ✓ | — | — |  | transferencia uniao fnde |
| `transferencia_uniao_fundeb` | transferencia_uniao_fundeb | FloatField | ✓ | — | — |  | transferencia uniao fundeb |
| `transferencia_uniao_fnas` | transferencia_uniao_fnas | FloatField | ✓ | — | — |  | transferencia uniao fnas |
| `outras_transferencias_uniao` | outras_transferencias_uniao | FloatField | ✓ | — | — |  | outras transferencias uniao |
| `transferencia_estado_icms` | transferencia_estado_icms | FloatField | ✓ | — | — |  | transferencia estado icms |
| `transferencia_estado_ipva` | transferencia_estado_ipva | FloatField | ✓ | — | — |  | transferencia estado ipva |
| `transferencia_estado_exploracao` | transferencia_estado_exploracao | FloatField | ✓ | — | — |  | transferencia estado exploracao |
| `transferencia_estado_sus` | transferencia_estado_sus | FloatField | ✓ | — | — |  | transferencia estado sus |
| `transferencia_estado_assistencia` | transferencia_estado_assistencia | FloatField | ✓ | — | — |  | transferencia estado assistencia |
| `outras_transferencias_estado` | outras_transferencias_estado | FloatField | ✓ | — | — |  | outras transferencias estado |

### `home_mediananacionalreceita` — MedianaNacionalReceita

Entidade de registro unico para armazenamento das medias nacionais pre-calculadas.
    Estrutura projetada para centralizar metricas agregadas e reduzir processamento em tempo de execucao.


| Coluna | Atributo | Tipo | Nulo | Índice | Único | FK → | Descrição |
|---|---|---|---|---|---|---|---|
| `id` | id 🔑 | BigAutoField | — | ✓ | ✓ |  | ID |
| `ano_referencia` | ano_referencia | IntegerField | — | — | — |  | ano referencia |
| `imposto_taxas_contribuicoes` | imposto_taxas_contribuicoes | FloatField | ✓ | — | — |  | imposto taxas contribuicoes |
| `contribuicoes` | contribuicoes | FloatField | ✓ | — | — |  | contribuicoes |
| `transferencias_correntes` | transferencias_correntes | FloatField | ✓ | — | — |  | transferencias correntes |
| `outras_receita` | outras_receita | FloatField | ✓ | — | — |  | outras receita |
| `imposto` | imposto | FloatField | ✓ | — | — |  | imposto |
| `taxas` | taxas | FloatField | ✓ | — | — |  | taxas |
| `contribuicoes_melhoria` | contribuicoes_melhoria | FloatField | ✓ | — | — |  | contribuicoes melhoria |
| `contribuicoes_sociais` | contribuicoes_sociais | FloatField | ✓ | — | — |  | contribuicoes sociais |
| `contribuicoes_iluminacao_publica` | contribuicoes_iluminacao_publica | FloatField | ✓ | — | — |  | contribuicoes iluminacao publica |
| `outras_contribuicoes` | outras_contribuicoes | FloatField | ✓ | — | — |  | outras contribuicoes |
| `tranferencias_uniao` | tranferencias_uniao | FloatField | ✓ | — | — |  | tranferencias uniao |
| `tranferencias_estados` | tranferencias_estados | FloatField | ✓ | — | — |  | tranferencias estados |
| `outras_tranferencias` | outras_tranferencias | FloatField | ✓ | — | — |  | outras tranferencias |
| `receita_patrimonial` | receita_patrimonial | FloatField | ✓ | — | — |  | receita patrimonial |
| `receita_agropecuaria` | receita_agropecuaria | FloatField | ✓ | — | — |  | receita agropecuaria |
| `receita_industrial` | receita_industrial | FloatField | ✓ | — | — |  | receita industrial |
| `receita_servicos` | receita_servicos | FloatField | ✓ | — | — |  | receita servicos |
| `outras_receitas` | outras_receitas | FloatField | ✓ | — | — |  | outras receitas |
| `iptu` | iptu | FloatField | ✓ | — | — |  | iptu |
| `itbi` | itbi | FloatField | ✓ | — | — |  | itbi |
| `iss` | iss | FloatField | ✓ | — | — |  | iss |
| `imposto_renda` | imposto_renda | FloatField | ✓ | — | — |  | imposto renda |
| `outros_impostos` | outros_impostos | FloatField | ✓ | — | — |  | outros impostos |
| `taxa_policia` | taxa_policia | FloatField | ✓ | — | — |  | taxa policia |
| `taxa_prestacao_servico` | taxa_prestacao_servico | FloatField | ✓ | — | — |  | taxa prestacao servico |
| `outras_taxas` | outras_taxas | FloatField | ✓ | — | — |  | outras taxas |
| `contribuicao_melhoria_pavimento_obras` | contribuicao_melhoria_pavimento_obras | FloatField | ✓ | — | — |  | contribuicao melhoria pavimento obras |
| `contribuicao_melhoria_agua_potavel` | contribuicao_melhoria_agua_potavel | FloatField | ✓ | — | — |  | contribuicao melhoria agua potavel |
| `contribuicao_melhoria_iluminacao_publica` | contribuicao_melhoria_iluminacao_publica | FloatField | ✓ | — | — |  | contribuicao melhoria iluminacao publica |
| `outras_contribuicoes_melhoria` | outras_contribuicoes_melhoria | FloatField | ✓ | — | — |  | outras contribuicoes melhoria |
| `transferencia_uniao_fpm` | transferencia_uniao_fpm | FloatField | ✓ | — | — |  | transferencia uniao fpm |
| `transferencia_uniao_exploracao` | transferencia_uniao_exploracao | FloatField | ✓ | — | — |  | transferencia uniao exploracao |
| `transferencia_uniao_sus` | transferencia_uniao_sus | FloatField | ✓ | — | — |  | transferencia uniao sus |
| `transferencia_uniao_fnde` | transferencia_uniao_fnde | FloatField | ✓ | — | — |  | transferencia uniao fnde |
| `transferencia_uniao_fundeb` | transferencia_uniao_fundeb | FloatField | ✓ | — | — |  | transferencia uniao fundeb |
| `transferencia_uniao_fnas` | transferencia_uniao_fnas | FloatField | ✓ | — | — |  | transferencia uniao fnas |
| `outras_transferencias_uniao` | outras_transferencias_uniao | FloatField | ✓ | — | — |  | outras transferencias uniao |
| `transferencia_estado_icms` | transferencia_estado_icms | FloatField | ✓ | — | — |  | transferencia estado icms |
| `transferencia_estado_ipva` | transferencia_estado_ipva | FloatField | ✓ | — | — |  | transferencia estado ipva |
| `transferencia_estado_exploracao` | transferencia_estado_exploracao | FloatField | ✓ | — | — |  | transferencia estado exploracao |
| `transferencia_estado_sus` | transferencia_estado_sus | FloatField | ✓ | — | — |  | transferencia estado sus |
| `transferencia_estado_assistencia` | transferencia_estado_assistencia | FloatField | ✓ | — | — |  | transferencia estado assistencia |
| `outras_transferencias_estado` | outras_transferencias_estado | FloatField | ✓ | — | — |  | outras transferencias estado |

### `home_medianaportereceita` — MedianaPorteReceita

Entidade de registro unico para armazenamento das medianas nacionais pre-calculadas.
    Estrutura projetada para centralizar metricas agregadas e reduzir processamento em tempo de execucao.


| Coluna | Atributo | Tipo | Nulo | Índice | Único | FK → | Descrição |
|---|---|---|---|---|---|---|---|
| `id` | id 🔑 | BigAutoField | — | ✓ | ✓ |  | ID |
| `ano_referencia` | ano_referencia | IntegerField | — | — | — |  | ano referencia |
| `porte` | porte | CharField(50000) | — | — | — |  | porte |
| `imposto_taxas_contribuicoes` | imposto_taxas_contribuicoes | FloatField | ✓ | — | — |  | imposto taxas contribuicoes |
| `contribuicoes` | contribuicoes | FloatField | ✓ | — | — |  | contribuicoes |
| `transferencias_correntes` | transferencias_correntes | FloatField | ✓ | — | — |  | transferencias correntes |
| `outras_receita` | outras_receita | FloatField | ✓ | — | — |  | outras receita |
| `imposto` | imposto | FloatField | ✓ | — | — |  | imposto |
| `taxas` | taxas | FloatField | ✓ | — | — |  | taxas |
| `contribuicoes_melhoria` | contribuicoes_melhoria | FloatField | ✓ | — | — |  | contribuicoes melhoria |
| `contribuicoes_sociais` | contribuicoes_sociais | FloatField | ✓ | — | — |  | contribuicoes sociais |
| `contribuicoes_iluminacao_publica` | contribuicoes_iluminacao_publica | FloatField | ✓ | — | — |  | contribuicoes iluminacao publica |
| `outras_contribuicoes` | outras_contribuicoes | FloatField | ✓ | — | — |  | outras contribuicoes |
| `tranferencias_uniao` | tranferencias_uniao | FloatField | ✓ | — | — |  | tranferencias uniao |
| `tranferencias_estados` | tranferencias_estados | FloatField | ✓ | — | — |  | tranferencias estados |
| `outras_tranferencias` | outras_tranferencias | FloatField | ✓ | — | — |  | outras tranferencias |
| `receita_patrimonial` | receita_patrimonial | FloatField | ✓ | — | — |  | receita patrimonial |
| `receita_agropecuaria` | receita_agropecuaria | FloatField | ✓ | — | — |  | receita agropecuaria |
| `receita_industrial` | receita_industrial | FloatField | ✓ | — | — |  | receita industrial |
| `receita_servicos` | receita_servicos | FloatField | ✓ | — | — |  | receita servicos |
| `outras_receitas` | outras_receitas | FloatField | ✓ | — | — |  | outras receitas |
| `iptu` | iptu | FloatField | ✓ | — | — |  | iptu |
| `itbi` | itbi | FloatField | ✓ | — | — |  | itbi |
| `iss` | iss | FloatField | ✓ | — | — |  | iss |
| `imposto_renda` | imposto_renda | FloatField | ✓ | — | — |  | imposto renda |
| `outros_impostos` | outros_impostos | FloatField | ✓ | — | — |  | outros impostos |
| `taxa_policia` | taxa_policia | FloatField | ✓ | — | — |  | taxa policia |
| `taxa_prestacao_servico` | taxa_prestacao_servico | FloatField | ✓ | — | — |  | taxa prestacao servico |
| `outras_taxas` | outras_taxas | FloatField | ✓ | — | — |  | outras taxas |
| `contribuicao_melhoria_pavimento_obras` | contribuicao_melhoria_pavimento_obras | FloatField | ✓ | — | — |  | contribuicao melhoria pavimento obras |
| `contribuicao_melhoria_agua_potavel` | contribuicao_melhoria_agua_potavel | FloatField | ✓ | — | — |  | contribuicao melhoria agua potavel |
| `contribuicao_melhoria_iluminacao_publica` | contribuicao_melhoria_iluminacao_publica | FloatField | ✓ | — | — |  | contribuicao melhoria iluminacao publica |
| `outras_contribuicoes_melhoria` | outras_contribuicoes_melhoria | FloatField | ✓ | — | — |  | outras contribuicoes melhoria |
| `transferencia_uniao_fpm` | transferencia_uniao_fpm | FloatField | ✓ | — | — |  | transferencia uniao fpm |
| `transferencia_uniao_exploracao` | transferencia_uniao_exploracao | FloatField | ✓ | — | — |  | transferencia uniao exploracao |
| `transferencia_uniao_sus` | transferencia_uniao_sus | FloatField | ✓ | — | — |  | transferencia uniao sus |
| `transferencia_uniao_fnde` | transferencia_uniao_fnde | FloatField | ✓ | — | — |  | transferencia uniao fnde |
| `transferencia_uniao_fundeb` | transferencia_uniao_fundeb | FloatField | ✓ | — | — |  | transferencia uniao fundeb |
| `transferencia_uniao_fnas` | transferencia_uniao_fnas | FloatField | ✓ | — | — |  | transferencia uniao fnas |
| `outras_transferencias_uniao` | outras_transferencias_uniao | FloatField | ✓ | — | — |  | outras transferencias uniao |
| `transferencia_estado_icms` | transferencia_estado_icms | FloatField | ✓ | — | — |  | transferencia estado icms |
| `transferencia_estado_ipva` | transferencia_estado_ipva | FloatField | ✓ | — | — |  | transferencia estado ipva |
| `transferencia_estado_exploracao` | transferencia_estado_exploracao | FloatField | ✓ | — | — |  | transferencia estado exploracao |
| `transferencia_estado_sus` | transferencia_estado_sus | FloatField | ✓ | — | — |  | transferencia estado sus |
| `transferencia_estado_assistencia` | transferencia_estado_assistencia | FloatField | ✓ | — | — |  | transferencia estado assistencia |
| `outras_transferencias_estado` | outras_transferencias_estado | FloatField | ✓ | — | — |  | outras transferencias estado |

### `home_medianaufreceita` — MedianaUfReceita

Entidade de registro unico para armazenamento das medias nacionais pre-calculadas.
    Estrutura projetada para centralizar metricas agregadas e reduzir processamento em tempo de execucao.


| Coluna | Atributo | Tipo | Nulo | Índice | Único | FK → | Descrição |
|---|---|---|---|---|---|---|---|
| `id` | id 🔑 | BigAutoField | — | ✓ | ✓ |  | ID |
| `ano_referencia` | ano_referencia | IntegerField | — | — | — |  | ano referencia |
| `uf` | uf | CharField(2) | — | — | — |  | uf |
| `imposto_taxas_contribuicoes` | imposto_taxas_contribuicoes | FloatField | ✓ | — | — |  | imposto taxas contribuicoes |
| `contribuicoes` | contribuicoes | FloatField | ✓ | — | — |  | contribuicoes |
| `transferencias_correntes` | transferencias_correntes | FloatField | ✓ | — | — |  | transferencias correntes |
| `outras_receita` | outras_receita | FloatField | ✓ | — | — |  | outras receita |
| `imposto` | imposto | FloatField | ✓ | — | — |  | imposto |
| `taxas` | taxas | FloatField | ✓ | — | — |  | taxas |
| `contribuicoes_melhoria` | contribuicoes_melhoria | FloatField | ✓ | — | — |  | contribuicoes melhoria |
| `contribuicoes_sociais` | contribuicoes_sociais | FloatField | ✓ | — | — |  | contribuicoes sociais |
| `contribuicoes_iluminacao_publica` | contribuicoes_iluminacao_publica | FloatField | ✓ | — | — |  | contribuicoes iluminacao publica |
| `outras_contribuicoes` | outras_contribuicoes | FloatField | ✓ | — | — |  | outras contribuicoes |
| `tranferencias_uniao` | tranferencias_uniao | FloatField | ✓ | — | — |  | tranferencias uniao |
| `tranferencias_estados` | tranferencias_estados | FloatField | ✓ | — | — |  | tranferencias estados |
| `outras_tranferencias` | outras_tranferencias | FloatField | ✓ | — | — |  | outras tranferencias |
| `receita_patrimonial` | receita_patrimonial | FloatField | ✓ | — | — |  | receita patrimonial |
| `receita_agropecuaria` | receita_agropecuaria | FloatField | ✓ | — | — |  | receita agropecuaria |
| `receita_industrial` | receita_industrial | FloatField | ✓ | — | — |  | receita industrial |
| `receita_servicos` | receita_servicos | FloatField | ✓ | — | — |  | receita servicos |
| `outras_receitas` | outras_receitas | FloatField | ✓ | — | — |  | outras receitas |
| `iptu` | iptu | FloatField | ✓ | — | — |  | iptu |
| `itbi` | itbi | FloatField | ✓ | — | — |  | itbi |
| `iss` | iss | FloatField | ✓ | — | — |  | iss |
| `imposto_renda` | imposto_renda | FloatField | ✓ | — | — |  | imposto renda |
| `outros_impostos` | outros_impostos | FloatField | ✓ | — | — |  | outros impostos |
| `taxa_policia` | taxa_policia | FloatField | ✓ | — | — |  | taxa policia |
| `taxa_prestacao_servico` | taxa_prestacao_servico | FloatField | ✓ | — | — |  | taxa prestacao servico |
| `outras_taxas` | outras_taxas | FloatField | ✓ | — | — |  | outras taxas |
| `contribuicao_melhoria_pavimento_obras` | contribuicao_melhoria_pavimento_obras | FloatField | ✓ | — | — |  | contribuicao melhoria pavimento obras |
| `contribuicao_melhoria_agua_potavel` | contribuicao_melhoria_agua_potavel | FloatField | ✓ | — | — |  | contribuicao melhoria agua potavel |
| `contribuicao_melhoria_iluminacao_publica` | contribuicao_melhoria_iluminacao_publica | FloatField | ✓ | — | — |  | contribuicao melhoria iluminacao publica |
| `outras_contribuicoes_melhoria` | outras_contribuicoes_melhoria | FloatField | ✓ | — | — |  | outras contribuicoes melhoria |
| `transferencia_uniao_fpm` | transferencia_uniao_fpm | FloatField | ✓ | — | — |  | transferencia uniao fpm |
| `transferencia_uniao_exploracao` | transferencia_uniao_exploracao | FloatField | ✓ | — | — |  | transferencia uniao exploracao |
| `transferencia_uniao_sus` | transferencia_uniao_sus | FloatField | ✓ | — | — |  | transferencia uniao sus |
| `transferencia_uniao_fnde` | transferencia_uniao_fnde | FloatField | ✓ | — | — |  | transferencia uniao fnde |
| `transferencia_uniao_fundeb` | transferencia_uniao_fundeb | FloatField | ✓ | — | — |  | transferencia uniao fundeb |
| `transferencia_uniao_fnas` | transferencia_uniao_fnas | FloatField | ✓ | — | — |  | transferencia uniao fnas |
| `outras_transferencias_uniao` | outras_transferencias_uniao | FloatField | ✓ | — | — |  | outras transferencias uniao |
| `transferencia_estado_icms` | transferencia_estado_icms | FloatField | ✓ | — | — |  | transferencia estado icms |
| `transferencia_estado_ipva` | transferencia_estado_ipva | FloatField | ✓ | — | — |  | transferencia estado ipva |
| `transferencia_estado_exploracao` | transferencia_estado_exploracao | FloatField | ✓ | — | — |  | transferencia estado exploracao |
| `transferencia_estado_sus` | transferencia_estado_sus | FloatField | ✓ | — | — |  | transferencia estado sus |
| `transferencia_estado_assistencia` | transferencia_estado_assistencia | FloatField | ✓ | — | — |  | transferencia estado assistencia |
| `outras_transferencias_estado` | outras_transferencias_estado | FloatField | ✓ | — | — |  | outras transferencias estado |

### `home_mediaportereceita` — MediaPorteReceita

Entidade de registro unico para armazenamento das medias nacionais pre-calculadas.
    Estrutura projetada para centralizar metricas agregadas e reduzir processamento em tempo de execucao.


| Coluna | Atributo | Tipo | Nulo | Índice | Único | FK → | Descrição |
|---|---|---|---|---|---|---|---|
| `id` | id 🔑 | BigAutoField | — | ✓ | ✓ |  | ID |
| `ano_referencia` | ano_referencia | IntegerField | — | — | — |  | ano referencia |
| `porte` | porte | CharField(50000) | — | — | — |  | porte |
| `imposto_taxas_contribuicoes` | imposto_taxas_contribuicoes | FloatField | ✓ | — | — |  | imposto taxas contribuicoes |
| `contribuicoes` | contribuicoes | FloatField | ✓ | — | — |  | contribuicoes |
| `transferencias_correntes` | transferencias_correntes | FloatField | ✓ | — | — |  | transferencias correntes |
| `outras_receita` | outras_receita | FloatField | ✓ | — | — |  | outras receita |
| `imposto` | imposto | FloatField | ✓ | — | — |  | imposto |
| `taxas` | taxas | FloatField | ✓ | — | — |  | taxas |
| `contribuicoes_melhoria` | contribuicoes_melhoria | FloatField | ✓ | — | — |  | contribuicoes melhoria |
| `contribuicoes_sociais` | contribuicoes_sociais | FloatField | ✓ | — | — |  | contribuicoes sociais |
| `contribuicoes_iluminacao_publica` | contribuicoes_iluminacao_publica | FloatField | ✓ | — | — |  | contribuicoes iluminacao publica |
| `outras_contribuicoes` | outras_contribuicoes | FloatField | ✓ | — | — |  | outras contribuicoes |
| `tranferencias_uniao` | tranferencias_uniao | FloatField | ✓ | — | — |  | tranferencias uniao |
| `tranferencias_estados` | tranferencias_estados | FloatField | ✓ | — | — |  | tranferencias estados |
| `outras_tranferencias` | outras_tranferencias | FloatField | ✓ | — | — |  | outras tranferencias |
| `receita_patrimonial` | receita_patrimonial | FloatField | ✓ | — | — |  | receita patrimonial |
| `receita_agropecuaria` | receita_agropecuaria | FloatField | ✓ | — | — |  | receita agropecuaria |
| `receita_industrial` | receita_industrial | FloatField | ✓ | — | — |  | receita industrial |
| `receita_servicos` | receita_servicos | FloatField | ✓ | — | — |  | receita servicos |
| `outras_receitas` | outras_receitas | FloatField | ✓ | — | — |  | outras receitas |
| `iptu` | iptu | FloatField | ✓ | — | — |  | iptu |
| `itbi` | itbi | FloatField | ✓ | — | — |  | itbi |
| `iss` | iss | FloatField | ✓ | — | — |  | iss |
| `imposto_renda` | imposto_renda | FloatField | ✓ | — | — |  | imposto renda |
| `outros_impostos` | outros_impostos | FloatField | ✓ | — | — |  | outros impostos |
| `taxa_policia` | taxa_policia | FloatField | ✓ | — | — |  | taxa policia |
| `taxa_prestacao_servico` | taxa_prestacao_servico | FloatField | ✓ | — | — |  | taxa prestacao servico |
| `outras_taxas` | outras_taxas | FloatField | ✓ | — | — |  | outras taxas |
| `contribuicao_melhoria_pavimento_obras` | contribuicao_melhoria_pavimento_obras | FloatField | ✓ | — | — |  | contribuicao melhoria pavimento obras |
| `contribuicao_melhoria_agua_potavel` | contribuicao_melhoria_agua_potavel | FloatField | ✓ | — | — |  | contribuicao melhoria agua potavel |
| `contribuicao_melhoria_iluminacao_publica` | contribuicao_melhoria_iluminacao_publica | FloatField | ✓ | — | — |  | contribuicao melhoria iluminacao publica |
| `outras_contribuicoes_melhoria` | outras_contribuicoes_melhoria | FloatField | ✓ | — | — |  | outras contribuicoes melhoria |
| `transferencia_uniao_fpm` | transferencia_uniao_fpm | FloatField | ✓ | — | — |  | transferencia uniao fpm |
| `transferencia_uniao_exploracao` | transferencia_uniao_exploracao | FloatField | ✓ | — | — |  | transferencia uniao exploracao |
| `transferencia_uniao_sus` | transferencia_uniao_sus | FloatField | ✓ | — | — |  | transferencia uniao sus |
| `transferencia_uniao_fnde` | transferencia_uniao_fnde | FloatField | ✓ | — | — |  | transferencia uniao fnde |
| `transferencia_uniao_fundeb` | transferencia_uniao_fundeb | FloatField | ✓ | — | — |  | transferencia uniao fundeb |
| `transferencia_uniao_fnas` | transferencia_uniao_fnas | FloatField | ✓ | — | — |  | transferencia uniao fnas |
| `outras_transferencias_uniao` | outras_transferencias_uniao | FloatField | ✓ | — | — |  | outras transferencias uniao |
| `transferencia_estado_icms` | transferencia_estado_icms | FloatField | ✓ | — | — |  | transferencia estado icms |
| `transferencia_estado_ipva` | transferencia_estado_ipva | FloatField | ✓ | — | — |  | transferencia estado ipva |
| `transferencia_estado_exploracao` | transferencia_estado_exploracao | FloatField | ✓ | — | — |  | transferencia estado exploracao |
| `transferencia_estado_sus` | transferencia_estado_sus | FloatField | ✓ | — | — |  | transferencia estado sus |
| `transferencia_estado_assistencia` | transferencia_estado_assistencia | FloatField | ✓ | — | — |  | transferencia estado assistencia |
| `outras_transferencias_estado` | outras_transferencias_estado | FloatField | ✓ | — | — |  | outras transferencias estado |

### `home_mediaufreceita` — MediaUfReceita

Entidade de registro unico para armazenamento das medias nacionais pre-calculadas.
    Estrutura projetada para centralizar metricas agregadas e reduzir processamento em tempo de execucao.


| Coluna | Atributo | Tipo | Nulo | Índice | Único | FK → | Descrição |
|---|---|---|---|---|---|---|---|
| `id` | id 🔑 | BigAutoField | — | ✓ | ✓ |  | ID |
| `ano_referencia` | ano_referencia | IntegerField | — | — | — |  | ano referencia |
| `uf` | uf | CharField(2) | — | — | — |  | uf |
| `imposto_taxas_contribuicoes` | imposto_taxas_contribuicoes | FloatField | ✓ | — | — |  | imposto taxas contribuicoes |
| `contribuicoes` | contribuicoes | FloatField | ✓ | — | — |  | contribuicoes |
| `transferencias_correntes` | transferencias_correntes | FloatField | ✓ | — | — |  | transferencias correntes |
| `outras_receita` | outras_receita | FloatField | ✓ | — | — |  | outras receita |
| `imposto` | imposto | FloatField | ✓ | — | — |  | imposto |
| `taxas` | taxas | FloatField | ✓ | — | — |  | taxas |
| `contribuicoes_melhoria` | contribuicoes_melhoria | FloatField | ✓ | — | — |  | contribuicoes melhoria |
| `contribuicoes_sociais` | contribuicoes_sociais | FloatField | ✓ | — | — |  | contribuicoes sociais |
| `contribuicoes_iluminacao_publica` | contribuicoes_iluminacao_publica | FloatField | ✓ | — | — |  | contribuicoes iluminacao publica |
| `outras_contribuicoes` | outras_contribuicoes | FloatField | ✓ | — | — |  | outras contribuicoes |
| `tranferencias_uniao` | tranferencias_uniao | FloatField | ✓ | — | — |  | tranferencias uniao |
| `tranferencias_estados` | tranferencias_estados | FloatField | ✓ | — | — |  | tranferencias estados |
| `outras_tranferencias` | outras_tranferencias | FloatField | ✓ | — | — |  | outras tranferencias |
| `receita_patrimonial` | receita_patrimonial | FloatField | ✓ | — | — |  | receita patrimonial |
| `receita_agropecuaria` | receita_agropecuaria | FloatField | ✓ | — | — |  | receita agropecuaria |
| `receita_industrial` | receita_industrial | FloatField | ✓ | — | — |  | receita industrial |
| `receita_servicos` | receita_servicos | FloatField | ✓ | — | — |  | receita servicos |
| `outras_receitas` | outras_receitas | FloatField | ✓ | — | — |  | outras receitas |
| `iptu` | iptu | FloatField | ✓ | — | — |  | iptu |
| `itbi` | itbi | FloatField | ✓ | — | — |  | itbi |
| `iss` | iss | FloatField | ✓ | — | — |  | iss |
| `imposto_renda` | imposto_renda | FloatField | ✓ | — | — |  | imposto renda |
| `outros_impostos` | outros_impostos | FloatField | ✓ | — | — |  | outros impostos |
| `taxa_policia` | taxa_policia | FloatField | ✓ | — | — |  | taxa policia |
| `taxa_prestacao_servico` | taxa_prestacao_servico | FloatField | ✓ | — | — |  | taxa prestacao servico |
| `outras_taxas` | outras_taxas | FloatField | ✓ | — | — |  | outras taxas |
| `contribuicao_melhoria_pavimento_obras` | contribuicao_melhoria_pavimento_obras | FloatField | ✓ | — | — |  | contribuicao melhoria pavimento obras |
| `contribuicao_melhoria_agua_potavel` | contribuicao_melhoria_agua_potavel | FloatField | ✓ | — | — |  | contribuicao melhoria agua potavel |
| `contribuicao_melhoria_iluminacao_publica` | contribuicao_melhoria_iluminacao_publica | FloatField | ✓ | — | — |  | contribuicao melhoria iluminacao publica |
| `outras_contribuicoes_melhoria` | outras_contribuicoes_melhoria | FloatField | ✓ | — | — |  | outras contribuicoes melhoria |
| `transferencia_uniao_fpm` | transferencia_uniao_fpm | FloatField | ✓ | — | — |  | transferencia uniao fpm |
| `transferencia_uniao_exploracao` | transferencia_uniao_exploracao | FloatField | ✓ | — | — |  | transferencia uniao exploracao |
| `transferencia_uniao_sus` | transferencia_uniao_sus | FloatField | ✓ | — | — |  | transferencia uniao sus |
| `transferencia_uniao_fnde` | transferencia_uniao_fnde | FloatField | ✓ | — | — |  | transferencia uniao fnde |
| `transferencia_uniao_fundeb` | transferencia_uniao_fundeb | FloatField | ✓ | — | — |  | transferencia uniao fundeb |
| `transferencia_uniao_fnas` | transferencia_uniao_fnas | FloatField | ✓ | — | — |  | transferencia uniao fnas |
| `outras_transferencias_uniao` | outras_transferencias_uniao | FloatField | ✓ | — | — |  | outras transferencias uniao |
| `transferencia_estado_icms` | transferencia_estado_icms | FloatField | ✓ | — | — |  | transferencia estado icms |
| `transferencia_estado_ipva` | transferencia_estado_ipva | FloatField | ✓ | — | — |  | transferencia estado ipva |
| `transferencia_estado_exploracao` | transferencia_estado_exploracao | FloatField | ✓ | — | — |  | transferencia estado exploracao |
| `transferencia_estado_sus` | transferencia_estado_sus | FloatField | ✓ | — | — |  | transferencia estado sus |
| `transferencia_estado_assistencia` | transferencia_estado_assistencia | FloatField | ✓ | — | — |  | transferencia estado assistencia |
| `outras_transferencias_estado` | outras_transferencias_estado | FloatField | ✓ | — | — |  | outras transferencias estado |

### `home_municipio` — Municipio

| Coluna | Atributo | Tipo | Nulo | Índice | Único | FK → | Descrição |
|---|---|---|---|---|---|---|---|
| `id` | id 🔑 | BigAutoField | — | ✓ | ✓ |  | ID |
| `cod_ibge` | cod_ibge | CharField(7) | — | ✓ | ✓ |  | cod ibge |
| `name_muni` | name_muni | CharField(255) | — | — | — |  | name muni |
| `name_muni_uf` | name_muni_uf | CharField(255) | — | — | — |  | name muni uf |
| `uf` | uf | CharField(2) | — | ✓ | — |  | uf |
| `coordx` | coordx | FloatField | — | — | — |  | coordx |
| `coordy` | coordy | FloatField | — | — | — |  | coordy |
| `populacao24` | populacao24 | IntegerField | ✓ | ✓ | — |  | populacao24 |
| `populacao24_rank_nacional` | populacao24_rank_nacional | IntegerField | ✓ | — | — |  | populacao24 rank nacional |
| `populacao24_total_nacional` | populacao24_total_nacional | IntegerField | ✓ | — | — |  | populacao24 total nacional |
| `populacao24_rank_estadual` | populacao24_rank_estadual | IntegerField | ✓ | — | — |  | populacao24 rank estadual |
| `populacao24_total_estadual` | populacao24_total_estadual | IntegerField | ✓ | — | — |  | populacao24 total estadual |
| `populacao24_rank_faixa` | populacao24_rank_faixa | IntegerField | ✓ | — | — |  | populacao24 rank faixa |
| `populacao24_total_faixa` | populacao24_total_faixa | IntegerField | ✓ | — | — |  | populacao24 total faixa |
| `populacao00` | populacao00 | IntegerField | ✓ | — | — |  | populacao00 |
| `rc_2024` | rc_2024 | FloatField | ✓ | — | — |  | rc 2024 |
| `rc_2000` | rc_2000 | FloatField | ✓ | — | — |  | rc 2000 |
| `rc_24_pc` | rc_24_pc | FloatField | ✓ | ✓ | — |  | rc 24 pc |
| `rc_00_pc` | rc_00_pc | FloatField | ✓ | — | — |  | rc 00 pc |
| `quintil24` | quintil24 | CharField(50) | ✓ | ✓ | — |  | quintil24 |
| `decil24` | decil24 | CharField(50) | ✓ | ✓ | — |  | decil24 |
| `quintil00` | quintil00 | CharField(50) | ✓ | — | — |  | quintil00 |
| `decil00` | decil00 | CharField(50) | ✓ | — | — |  | decil00 |
| `percentil24` | percentil24 | CharField(50) | ✓ | — | — |  | percentil24 |
| `percentil24_n` | percentil24_n | IntegerField | ✓ | — | — |  | percentil24 n |
| `percentil00` | percentil00 | CharField(50) | ✓ | — | — |  | percentil00 |
| `percentil00_n` | percentil00_n | IntegerField | ✓ | — | — |  | percentil00 n |
| `regiao` | regiao | CharField(255) | — | ✓ | — |  | regiao |
| `rank_nacional` | rank_nacional | IntegerField | ✓ | — | — |  | rank nacional |
| `total_nacional` | total_nacional | IntegerField | ✓ | — | — |  | total nacional |
| `rank_nacional_00` | rank_nacional_00 | IntegerField | ✓ | — | — |  | rank nacional 00 |
| `total_nacional_00` | total_nacional_00 | IntegerField | ✓ | — | — |  | total nacional 00 |
| `rank_estadual` | rank_estadual | IntegerField | ✓ | — | — |  | rank estadual |
| `total_estadual` | total_estadual | IntegerField | ✓ | — | — |  | total estadual |
| `rank_faixa` | rank_faixa | IntegerField | ✓ | — | — |  | rank faixa |
| `total_faixa` | total_faixa | IntegerField | ✓ | — | — |  | total faixa |
| `sus_dependente` | sus_dependente | FloatField | ✓ | — | — |  | sus dependente |
| `cadunico` | cadunico | IntegerField | ✓ | — | — |  | cadunico |
| `cadunico_rank_nacional` | cadunico_rank_nacional | IntegerField | ✓ | — | — |  | cadunico rank nacional |
| `cadunico_total_nacional` | cadunico_total_nacional | IntegerField | ✓ | — | — |  | cadunico total nacional |
| `cadunico_rank_estadual` | cadunico_rank_estadual | IntegerField | ✓ | — | — |  | cadunico rank estadual |
| `cadunico_total_estadual` | cadunico_total_estadual | IntegerField | ✓ | — | — |  | cadunico total estadual |
| `cadunico_rank_faixa` | cadunico_rank_faixa | IntegerField | ✓ | — | — |  | cadunico rank faixa |
| `cadunico_total_faixa` | cadunico_total_faixa | IntegerField | ✓ | — | — |  | cadunico total faixa |
| `rm_id` | rm | ForeignKey | ✓ | ✓ | — | `home_regiaometropolitana` | rm |

### `home_noticia` — Noticia

| Coluna | Atributo | Tipo | Nulo | Índice | Único | FK → | Descrição |
|---|---|---|---|---|---|---|---|
| `id` | id 🔑 | BigAutoField | — | ✓ | ✓ |  | ID |
| `titulo` | titulo | CharField(200) | — | — | — |  | Título da Matéria |
| `data` | data | DateField | — | — | — |  | Data de Publicação |
| `imagem_url` | imagem_url | CharField(500) | ✓ | — | — |  | Cole o link de compartilhamento da imagem. Funciona com Google Drive (o arquivo precisa estar como 'Qualquer pessoa com o link'), Imgur ou qualquer URL pública direta (.jpg/.png). |
| `tag` | tag | CharField(50) | — | — | — |  | Categoria (Tag) |
| `link` | link | CharField(500) | ✓ | — | — |  | Link de Destino |

### `home_percentis` — Percentis

| Coluna | Atributo | Tipo | Nulo | Índice | Único | FK → | Descrição |
|---|---|---|---|---|---|---|---|
| `id` | id 🔑 | BigAutoField | — | ✓ | ✓ |  | ID |
| `percentil` | percentil | IntegerField | — | ✓ | ✓ |  | Valor do percentil (0-100) |
| `valor` | valor | FloatField | — | — | — |  | valor |

### `home_regiaometropolitana` — RegiaoMetropolitana

| Coluna | Atributo | Tipo | Nulo | Índice | Único | FK → | Descrição |
|---|---|---|---|---|---|---|---|
| `id` | id 🔑 | BigAutoField | — | ✓ | ✓ |  | ID |
| `nome` | nome | CharField(255) | — | ✓ | ✓ |  | Nome único da Região Metropolitana |

