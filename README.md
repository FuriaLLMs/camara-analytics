# 🏛️ Câmara Analytics

> **Sistema Modular de Análise de Dados da Câmara dos Deputados do Brasil**

Dashboard interativo e conjunto de ferramentas para analisar dados públicos da Câmara dos Deputados, consumindo a [API de Dados Abertos](https://dadosabertos.camara.leg.br) em tempo real.

---

## 📸 Visão Geral

O projeto é composto por **5 módulos independentes**, cada um com uma responsabilidade específica:

| Módulo | Tipo | Descrição |
|--------|------|-----------|
| `parlamentar_dashboard` | 🌐 Web App | Dashboard Streamlit com análise individual de deputados |
| `tracker_gastos` | 🐍 Script | Download e análise local das despesas CEAP em CSV/Parquet |
| `network_analyst` | 🐍 Script | Geração de grafos de redes políticas via frentes parlamentares |
| `legis_notifier` | 🤖 Bot | Monitoramento de proposições legislativas com alertas via Telegram |
| `tema_miner` | 🐍 Script | Mineração de temas em ementas legislativas com NLP |

---

## 🚀 Início Rápido

### Pré-requisitos

- Python **3.12+**
- [Poetry](https://python-poetry.org/docs/#installation) (gerenciador de dependências)

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/FuriaLLMs/camara-analytics.git
cd camara-analytics

# 2. Instale as dependências
poetry install

# 3. Ative o ambiente virtual
poetry shell
```

### Rodando o Dashboard

```bash
poetry run streamlit run modules/parlamentar_dashboard/app.py
```

Acesse em: **http://localhost:8501**

---

## 🌐 Dashboard Parlamentar (`parlamentar_dashboard`)

O módulo principal — uma aplicação web completa para analisar o perfil e a atuação de qualquer um dos **513 deputados federais**.

### Funcionalidades

#### Aba 👥 Deputados
- Lista completa dos 513 deputados com paginação automática
- Filtros por **Estado (UF)** e **Partido**
- Métricas: total de deputados, número de partidos, estados representados
- **Tabela interativa** com nome, partido, UF e e-mail
- **Gráfico donut** com distribuição de deputados por partido

#### Aba 🔍 Análise Individual
Selecione qualquer deputado e visualize:

| Sub-aba | O que mostra |
|---------|--------------|
| 💰 Despesas CEAP | Treemap colorido por categoria de gasto + tabela detalhada |
| 🎙️ Discursos | Histórico mensal de discursos em plenário |
| 📅 Eventos | Distribuição de participações por tipo de sessão |
| 🏛️ Órgãos | Comissões e órgãos dos quais o deputado é membro |
| 🏳️ Frentes | Frentes parlamentares das quais participa |

**6 métricas de atividade:** Gasto CEAP total · Notas fiscais · Discursos · Eventos · Comissões · Frentes

#### Aba ℹ️ Sobre
Documentação dos endpoints utilizados e informações sobre os módulos.

### Endpoints da API Utilizados

| Dado | Endpoint |
|------|----------|
| Lista de deputados | `GET /deputados` |
| Perfil completo | `GET /deputados/{id}` |
| Despesas CEAP | `GET /deputados/{id}/despesas` |
| Discursos em plenário | `GET /deputados/{id}/discursos` |
| Participação em eventos | `GET /deputados/{id}/eventos` |
| Comissões e órgãos | `GET /deputados/{id}/orgaos` |
| Frentes parlamentares | `GET /deputados/{id}/frentes` |
| Lista de partidos | `GET /partidos` |

### Cache Inteligente

| Dado | TTL |
|------|-----|
| Lista de deputados / partidos | 1 hora |
| Análises individuais | 30 minutos |
| Frentes e órgãos | 1 hora |

> Use o botão **🗑️ Limpar Cache** na sidebar para forçar atualização imediata.

---

## 💰 Tracker de Gastos (`tracker_gastos`)

Script para download batch das despesas CEAP de todos os deputados.

```bash
poetry run python -m modules.tracker_gastos.main
```

- Exporta dados em `.csv` e `.parquet`
- Calcula totais por deputado, partido e tipo de despesa
- Gera relatório resumido em texto

**Saída:** `outputs/despesas_YYYY.csv`

---

## 🕸️ Network Analyst (`network_analyst`)

Analisa redes de influência política a partir de frentes parlamentares compartilhadas.

```bash
poetry run python -m modules.network_analyst.main
```

- Cria grafo de co-participação em frentes parlamentares
- Detecta comunidades políticas automaticamente
- Exporta visualização interativa em HTML

**Saída:** `outputs/rede_politica.html`

---

## 🤖 Legis Notifier (`legis_notifier`)

Bot que monitora novas proposições legislativas e envia alertas via **Telegram**.

### Configuração

```bash
# Copie o arquivo de configuração
cp modules/legis_notifier/.env.example modules/legis_notifier/.env

# Edite com seu token do Telegram
TELEGRAM_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
```

```bash
poetry run python -m modules.legis_notifier.main
```

---

## 🔍 Tema Miner (`tema_miner`)

Classifica automaticamente o tema de proposições legislativas usando NLP.

```bash
poetry run python -m modules.tema_miner.main
```

- Busca proposições recentes na API
- Limpa e normaliza o texto das ementas
- Classifica por área temática (saúde, educação, economia, etc.)
- Gera gráficos de distribuição de temas

**Saída:** `outputs/temas_YYYY-MM-DD.csv`

---

## 📁 Estrutura do Projeto

```
camara-analytics/
│
├── modules/
│   ├── parlamentar_dashboard/
│   │   ├── app.py              # Interface Streamlit principal
│   │   ├── data_loader.py      # Funções de acesso à API com cache
│   │   └── charts.py           # Gráficos Plotly (treemap, donut, tabelas)
│   │
│   ├── tracker_gastos/
│   │   ├── main.py
│   │   ├── extractor.py        # Download das despesas
│   │   ├── processor.py        # Processamento e agregação
│   │   └── reporter.py         # Geração de relatórios
│   │
│   ├── network_analyst/
│   │   ├── main.py
│   │   ├── fetcher.py          # Busca frentes e membros
│   │   ├── graph_builder.py    # Constrói o grafo de rede
│   │   └── visualizer.py       # Exporta visualização
│   │
│   ├── legis_notifier/
│   │   ├── main.py
│   │   ├── monitor.py          # Monitora novas proposições
│   │   ├── notifier.py         # Envia alertas via Telegram
│   │   ├── persistence.py      # Salva último ID processado
│   │   └── .env.example        # Template de configuração
│   │
│   └── tema_miner/
│       ├── main.py
│       ├── fetcher.py          # Busca proposições
│       ├── cleaner.py          # Limpa texto das ementas
│       ├── analyzer.py         # Classifica temas
│       └── visualizer.py       # Gráficos de temas
│
├── outputs/                    # Arquivos gerados (gitignored)
├── pyproject.toml              # Dependências Poetry
└── README.md
```

---

## 🛠️ Tecnologias

| Biblioteca | Uso |
|-----------|-----|
| `streamlit` | Interface web do dashboard |
| `plotly` | Gráficos interativos (treemap, donut, tabelas) |
| `pandas` | Manipulação e análise de dados |
| `requests` | Chamadas HTTP à API da Câmara |
| `networkx` | Construção de grafos de rede |
| `python-telegram-bot` | Alertas via Telegram |

---

## 🔌 Fonte de Dados

Todos os dados são obtidos diretamente da **API de Dados Abertos da Câmara dos Deputados**:

- 📖 Documentação: https://dadosabertos.camara.leg.br/swagger/api.html
- 🔗 Base URL: `https://dadosabertos.camara.leg.br/api/v2`
- ✅ Gratuita e sem necessidade de autenticação
- 🔄 Atualizada diariamente pela própria Câmara

---

## 📄 Licença

Este projeto é de uso educacional e de pesquisa. Dados fornecidos pela Câmara dos Deputados sob licença aberta.

---

<div align="center">
  Desenvolvido com ❤️ usando dados públicos da Câmara dos Deputados do Brasil
</div>
