"""Módulo para cálculo da Taxa de Conversão (Win Rate) via Template Method.

Implementa WinRateCalculator, computando o percentual de negócios convertidos.
"""

from datetime import datetime
from typing import Any

from models.customer import Customer
from models.enums import PipelineStep
from models.pipeline import Pipeline
from patterns.template_method.base_metric_calculator import BaseMetricCalculator


class WinRateCalculator(BaseMetricCalculator):
    """Calculadora concreta para a Taxa de Conversão (Win Rate) do funil de vendas."""

    metric_key: str = "win_rate"
    metric_name: str = "Taxa de Conversão"

    def fetch_data(
        self, start_date: datetime, end_date: datetime, company_id: int | None
    ) -> list[Pipeline]:
        """Busca todas as oportunidades de pipeline abertas no período informado."""
        query = Pipeline.query.filter(
            Pipeline.date.isnot(None),
            Pipeline.date >= start_date,
            Pipeline.date <= end_date,
        )
        if company_id is not None:
            query = query.join(Customer).filter(Customer.company_id == company_id)

        return query.all()

    def calculate(self, raw_data: list[Pipeline]) -> float:
        """Calcula o percentual de pipelines que atingiram etapas de fechamento."""
        if not raw_data:
            return 0.0

        closing_steps = {PipelineStep.CLOSING, PipelineStep.FOLLOW_UP}
        won_count = sum(1 for p in raw_data if p.step in closing_steps)
        return round((won_count / len(raw_data)) * 100.0, 2)
