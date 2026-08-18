"""Métricas Prometheus.

Expõe `/metrics` no formato OpenMetrics/Prometheus (texto plano), que é o
padrão de fato para observabilidade "pull-based" em ambientes cloud-native
e é o que o Prometheus (e, por extensão, o Grafana) esperam raspar.

Além das métricas HTTP padrão (latência, contagem de requisições por rota e
status), expomos um contador de negócio (`iris_predictions_total`) que
particiona as predições por espécie prevista — útil para detectar, por
exemplo, drift na distribuição de classes previstas ao longo do tempo.
"""

from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator

predictions_total = Counter(
    "iris_predictions_total",
    "Número total de predições realizadas, particionado por classe prevista.",
    labelnames=("classe",),
)


def setup_metrics(app) -> None:
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
