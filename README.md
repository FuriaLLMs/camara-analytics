# 🏛️ Sistema Modular de Análise de Dados da Câmara dos Deputados

Ecossistema de scripts e aplicações em Python para consumir, processar e visualizar dados públicos do poder legislativo brasileiro via [API de Dados Abertos da Câmara dos Deputados](https://dadosabertos.camara.leg.br/swagger/api.html).

---

## 📂 Estrutura do Projeto

```
projeto_camara_api/
├── pyproject.toml
├── README.md
└── modules/
    ├── tracker_gastos/        # Módulo 1: Extração de despesas (CEAP)
    ├── network_analyst/       # Módulo 2: Redes de influência
    ├── legis_notifier/        # Módulo 3: Alertas de proposições
    ├── parlamentar_dashboard/ # Módulo 4: Dashboard interativo
    └── tema_miner/            # Módulo 5: NLP em ementas legislativas
```

---

## ⚙️ Configuração do Ambiente

### Pré-requisitos
- Python 3.10+
- [Poetry](https://python-poetry.org/docs/#installation)

### Instalação

```bash
# Clonar/entrar no diretório do projeto
cd "Sistema Modular de Análise de Dados da Câmara dos Deputados"

# Instalar dependências com Poetry
poetry install

# Ativar o ambiente virtual
poetry shell
```

---

## 🔌 Módulos

### 1. `tracker_gastos` — Rastreador de Gastos CEAP
Extrai e consolida despesas dos deputados da cota parlamentar.

```bash
poetry run python -m modules.tracker_gastos.main --id 204554
```

---

### 2. `network_analyst` — Análise de Redes Políticas
Mapeia relações entre deputados e frentes parlamentares via grafos.

```bash
poetry run python -m modules.network_analyst.main
```

---

### 3. `legis_notifier` — Notificador Legislativo
Monitora novas proposições e envia alertas via Telegram.

```bash
# Configurar variáveis de ambiente primiero:
cp modules/legis_notifier/.env.example modules/legis_notifier/.env
# Editar .env com seu TOKEN e CHAT_ID do Telegram

poetry run python -m modules.legis_notifier.main
```

---

### 4. `parlamentar_dashboard` — Dashboard Interativo
Interface web com Streamlit para explorar dados dos parlamentares.

```bash
poetry run streamlit run modules/parlamentar_dashboard/app.py
# Acesse: http://localhost:8501
```

---

### 5. `tema_miner` — Minerador de Temas Legislativos
Aplica NLP em ementas de PLs para identificar pautas em debate.

```bash
poetry run python -m modules.tema_miner.main --ano 2024
```

---

## 🛠️ Tecnologias

| Módulo              | Bibliotecas Principais                      |
|---------------------|---------------------------------------------|
| tracker_gastos      | `requests`, `pandas`                        |
| network_analyst     | `networkx`, `matplotlib`                    |
| legis_notifier      | `python-telegram-bot`, `python-dotenv`      |
| parlamentar_dashboard | `streamlit`, `plotly`                     |
| tema_miner          | `nltk`, `wordcloud`, `re`                   |

---

## 📡 Endpoints da API Utilizados

| Módulo | Endpoint |
|--------|----------|
| tracker_gastos | `GET /deputados/{id}/despesas` |
| network_analyst | `GET /frentes`, `GET /frentes/{id}/membros`, `GET /deputados` |
| legis_notifier | `GET /proposicoes` |
| parlamentar_dashboard | `GET /deputados`, `GET /deputados/{id}/votacoes`, `GET /deputados/{id}/eventos` |
| tema_miner | `GET /proposicoes` |

---

## 📄 Licença

Projeto pessoal para fins educacionais e análise de dados públicos.
