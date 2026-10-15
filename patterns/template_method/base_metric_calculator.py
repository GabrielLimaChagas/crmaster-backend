"""Módulo base para o padrão Template Method de cálculo de métricas e KPIs.

Define a classe abstrata BaseMetricCalculator com o ciclo invariante de cálculo:
definição de período homólogo, busca de dados, cálculo, delta percentual e formatação.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any

from patterns.singleton.db_connection import DBConnection


class BaseMetricCalculator(ABC):
    """Classe base abstrata (Template Method) para cálculo de métricas e KPIs analíticos.

    Orquestra a sequência invariante de passos:
    1. Janela Temporal: define período atual (start_date, end_date) e homólogo anterior (prev_start_date, prev_end_date).
    2. Coleta de Dados: invoca o método abstrato fetch_data para ambos os períodos.
    3. Cálculo da Métrica: invoca o método abstrato calculate para ambos os períodos.
    4. Variação & Tendência: computa o delta percentual e a tendência ('up', 'down', 'stable').
    5. Formatação Padronizada: retorna o dicionário consolidado para o front-end.
    """

    metric_key: str = "base_metric"
    metric_name: str = "Métrica Base"

    def __init__(self) -> None:
        """Inicializa a calculadora de métrica com a conexão ao banco."""
        self.db = DBConnection().db

    def compute_metric(self, days: int = 30, company_id: int | None = None) -> dict[str, Any]:
        """Template Method: Define a estrutura invariante do algoritmo de cálculo de métricas.

        Args:
            days: Quantidade de dias da janela de análise (padrão: 30).
            company_id: ID opcional da empresa para filtragem multi-tenant.

        Returns:
            dict padronizado com os valores calculados, variação e tendência.
        """
        # 1. Definição da Janela Temporal (Período Atual e Homólogo Anterior)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        prev_end_date = start_date
        prev_start_date = prev_end_date - timedelta(days=days)

        # 2. Coleta de Dados (Passo abstrato / hook especializado)
        current_data = self.fetch_data(start_date, end_date, company_id)
        previous_data = self.fetch_data(prev_start_date, prev_end_date, company_id)

        # 3. Cálculo da Métrica (Passo abstrato)
        current_value = float(self.calculate(current_data))
        previous_value = float(self.calculate(previous_data))

        # 4. Cálculo de Delta Percentual e Tendência
        delta_percentage, trend = self._calculate_delta_and_trend(current_value, previous_value)

        # 5. Formatação Padronizada do Resultado
        return {
            "metric_key": self.metric_key,
            "metric_name": self.metric_name,
            "current_value": round(current_value, 2),
            "previous_value": round(previous_value, 2),
            "delta_percentage": delta_percentage,
            "trend": trend,
            "period_days": days,
        }

    @abstractmethod
    def fetch_data(
        self, start_date: datetime, end_date: datetime, company_id: int | None
    ) -> Any:
        """Passo primitivo abstrato: busca os dados necessários no banco para o intervalo."""
        raise NotImplementedError

    @abstractmethod
    def calculate(self, raw_data: Any) -> float:
        """Passo primitivo abstrato: processa os dados brutos e calcula o valor numérico da métrica."""
        raise NotImplementedError

    @staticmethod
    def _calculate_delta_and_trend(
        current_val: float, previous_val: float
    ) -> tuple[float, str]:
        """Calcula a variação percentual relativa e a direção da tendência."""
        if previous_val != 0.0:
            delta = round(((current_val - previous_val) / abs(previous_val)) * 100.0, 2)
        else:
            if current_val > 0.0:
                delta = 100.0
            elif current_val < 0.0:
                delta = -100.0
            else:
                delta = 0.0

        if delta > 0.0:
            trend = "up"
        elif delta < 0.0:
            trend = "down"
        else:
            trend = "stable"

        return delta, trend
