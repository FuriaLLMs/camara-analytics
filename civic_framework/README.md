# 🏛️ Civic Framework — Transparência Municipal Escalável

> *"Dados não tornam o governo transparente. Interpretação consistente e pública dos dados torna."*

Framework modular de coleta, normalização, análise e visualização de dados parlamentares municipais. Começa por Florianópolis/SC, mas foi projetado para escalar para qualquer câmara brasileira.

## Arquitetura

```
civic_framework/
├── adapters/
│   ├── base.py          ← Contrato ABC (MunicipalDataSource)
│   ├── florianopolis.py ← FlorianopolisAdapter (CMF JSON-Web)
│   └── __init__.py
├── collector.py         ← Coleta paginada + histórico JSON versionado
├── database.py          ← SQLite histórico multi-cidade (WAL mode)
├── metrics.py           ← IAL, Z-Score, ICG (Herfindahl)
└── __init__.py
```

## Como usar

```python
from civic_framework.adapters import FlorianopolisAdapter
from civic_framework.collector import DataCollector
from civic_framework.database import init_db

# 1. Inicializa o banco histórico
init_db()

# 2. Coleta dados de Florianópolis
adapter = FlorianopolisAdapter()
collector = DataCollector(adapter)
resultado = collector.collect_all()   # salva em data/raw/florianopolis/

# 3. Calcula IAL
from civic_framework.metrics import calcular_ial
df_ial = calcular_ial(df_vereadores, df_proposicoes, df_pautas)
print(df_ial.head(10))
```

## Adicionar uma nova cidade

```python
# civic_framework/adapters/curitiba.py
from .base import MunicipalDataSource

class CuritibaAdapter(MunicipalDataSource):
    @property
    def cidade(self): return "curitiba"

    @property
    def uf(self): return "PR"

    def fetch_vereadores(self): ...   # implementar para a API de Curitiba
    def fetch_proposicoes(self, pagina=1, tipo=None): ...
    def fetch_pautas(self, pagina=1): ...
    def fetch_noticias(self, pagina=1): ...
```

## Coleta automática (cron)

```bash
# Diariamente às 06h
0 6 * * * cd /caminho/camara-analytics && poetry run python -m civic_framework.collector --cidade florianopolis
```

## Métricas implementadas

| Métrica | Descrição | Metodologia |
|---------|-----------|-------------|
| **IAL** | Índice de Atividade Legislativa | Média ponderada (proposições + participação + relatorias), normalizado [0,100] |
| **Z-Score** | Anomalia de atividade no tempo | Desvio padrão sobre histórico próprio do vereador |
| **ICG** | Concentração geográfica | Índice Herfindahl-Hirschman sobre bairros |

> ⚠️ **Transparência algorítmica**: os pesos do IAL são parâmetros explícitos, versionados e públicos. Qualquer alteração metodológica deve ser documentada com data e justificativa.

## Princípio fundamental

Transparência é processo contínuo. Os dados abertos são o ponto de partida — a ferramenta que os transforma em **compreensão acessível** é o produto real.
