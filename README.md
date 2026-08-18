# API de Classificação de Espécies de Flores Iris

API em **FastAPI** que classifica a espécie de uma flor Iris (`setosa`,
`versicolor`, `virginica`) a partir de medidas de sépala e pétala, usando um
`RandomForestClassifier` (scikit-learn) treinado sobre o dataset clássico
Iris.

## Sumário

- [Arquitetura](#arquitetura)
- [Requisitos](#requisitos)
- [Rodando localmente](#rodando-localmente)
- [Rodando com Docker](#rodando-com-docker)
- [Autenticação](#autenticação)
- [Endpoints](#endpoints)
- [Exemplos de uso](#exemplos-de-uso)
- [Observabilidade](#observabilidade)
- [Testes](#testes)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Retreinando o modelo](#retreinando-o-modelo)

## Arquitetura

```
app/
├── main.py                 # criação da app, middlewares, lifespan
├── core/
│   ├── config.py            # Settings (pydantic-settings), lidas de env/.env
│   ├── security.py          # emissão/validação de JWT, hash de senha
│   └── logging.py           # logging estruturado em JSON
├── models/
│   └── schemas.py            # contratos Pydantic de request/response
├── ml/
│   ├── model.py               # wrapper de carregamento/inferência do modelo
│   └── artifacts/              # modelo_iris.pkl, classes_iris.pkl
├── api/
│   ├── deps.py                 # dependências compartilhadas (ex: get_model)
│   └── routes/
│       ├── health.py            # GET / e GET /health
│       ├── auth.py              # POST /auth/login
│       └── predict.py           # POST /predict e /predict/batch
└── observability/
    ├── middleware.py            # request-id + log de acesso estruturado
    └── metrics.py                # métricas Prometheus (/metrics)
scripts/train_model.py       # treina o modelo e gera os artefatos .pkl
tests/                        # testes automatizados (pytest)
observability/                # provisionamento Prometheus + Grafana
```

A separação em camadas (`api` → `ml`/`core` → `models`) segue o princípio de
que rotas HTTP não devem conter lógica de negócio: elas apenas validam
entrada (via Pydantic), delegam para a camada de domínio (`IrisModel`) e
formatam a saída.

## Requisitos

- Python 3.12+ (testado com 3.14)
- Docker + Docker Compose (opcional, para rodar com observabilidade completa)

## Rodando localmente

```bash
python -m venv .venv
.venv/Scripts/activate       # Windows
pip install -r requirements-dev.txt
cp .env.example .env         # ajuste os valores se necessário
uvicorn app.main:app --reload
```

A API sobe em `http://127.0.0.1:8000`. Documentação interativa em
`http://127.0.0.1:8000/docs`.

## Rodando com Docker

```bash
docker compose up --build
```

Isso sobe três serviços:

| Serviço      | URL                      | Descrição                          |
|--------------|--------------------------|-------------------------------------|
| `api`        | http://localhost:8000    | A API (docs em `/docs`)             |
| `prometheus` | http://localhost:9090    | Coleta métricas da API a cada 5s    |
| `grafana`    | http://localhost:3000    | Dashboard pré-provisionado (`admin`/`admin`, ou acesso anônimo como Viewer) |

O dashboard "Iris API - Overview" já vem carregado no Grafana (requisições/s,
latência p95, erros 5xx, predições por espécie).

Para rodar só a API, sem observabilidade:

```bash
docker build -t iris-api .
docker run -p 8000:8000 iris-api
```

## Autenticação

A autenticação é **mockada**: não existe banco de usuários, apenas um único
usuário de demonstração (usuário `demo`, senha `demo123`, configuráveis via
`MOCK_USERNAME` / `MOCK_PASSWORD_HASH`). O fluxo, porém, é o mesmo de uma
autenticação JWT real:

1. `POST /auth/login` com `username`/`password` (form-urlencoded) → recebe um
   `access_token` (JWT, HS256, expira em 30 min por padrão).
2. Envie o token em `Authorization: Bearer <token>` nas rotas protegidas
   (`/predict` e `/predict/batch`).

Para virar autenticação real, troque `authenticate_user` em
[`app/core/security.py`](app/core/security.py) por uma consulta a uma tabela
de usuários — o restante do fluxo (emissão/validação do JWT) não muda.

## Endpoints

| Método | Rota             | Autenticação | Descrição                                  |
|--------|------------------|:------------:|---------------------------------------------|
| GET    | `/`              | não          | Informações gerais da API                    |
| GET    | `/health`        | não          | Status da API e do modelo                    |
| GET    | `/docs`          | não          | Swagger UI                                   |
| GET    | `/metrics`       | não          | Métricas Prometheus                          |
| POST   | `/auth/login`    | não          | Login e emissão de JWT                       |
| POST   | `/predict`       | sim (Bearer) | Predição de uma única amostra                |
| POST   | `/predict/batch` | sim (Bearer) | Predição de várias amostras (até 100/req.)   |

## Exemplos de uso

```bash
# 1. login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d "username=demo&password=demo123" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# 2. predição individual
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'

# 3. predição em lote
curl -s -X POST http://localhost:8000/predict/batch \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"items":[
        {"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2},
        {"sepal_length":6.7,"sepal_width":3.0,"petal_length":5.2,"petal_width":2.3}
      ]}'
```

## Observabilidade

- **Logs estruturados (JSON)**: cada requisição gera uma linha JSON com
  `request_id`, método, rota, status e latência (`app/observability/middleware.py`).
  O `request_id` é propagado por `ContextVar`, então qualquer log emitido
  durante o processamento da requisição carrega o mesmo identificador —
  facilita correlação em ferramentas como Grafana Loki, Datadog ou ELK.
- **Métricas Prometheus** em `/metrics`: latência, contagem de requisições por
  rota/status (via `prometheus-fastapi-instrumentator`) e uma métrica de
  negócio, `iris_predictions_total{classe=...}`, para acompanhar a
  distribuição de predições ao longo do tempo.
- **Dashboard Grafana** pré-provisionado em `observability/grafana/`.

## Testes

```bash
pytest
```

13 testes cobrindo saúde da API, autenticação (credenciais válidas/ inválidas)
e predição (individual e em lote, com e sem token, validação de entrada).

## Variáveis de ambiente

Ver [`.env.example`](.env.example) para a lista completa. As mais relevantes:

| Variável                          | Padrão                  | Descrição                                    |
|-----------------------------------|--------------------------|-----------------------------------------------|
| `JWT_SECRET_KEY`                  | chave de dev             | **Troque em produção.** Gere com `secrets.token_hex(32)` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                     | Validade do token                             |
| `MOCK_USERNAME` / `MOCK_PASSWORD_HASH` | `demo` / hash de `demo123` | Credenciais do usuário mockado           |
| `LOG_JSON`                        | `true`                   | `false` para logs em texto simples (dev local)|
| `CORS_ALLOW_ORIGINS`              | `["*"]`                  | Origens permitidas para CORS                  |

## Retreinando o modelo

```bash
python scripts/train_model.py
```

Gera `app/ml/artifacts/modelo_iris.pkl` e `classes_iris.pkl`. O notebook
`train_model.ipynb` faz o mesmo processo de forma interativa/exploratória.
