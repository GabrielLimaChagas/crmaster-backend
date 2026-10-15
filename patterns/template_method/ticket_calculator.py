"""Módulo para cálculo do Ticket Médio via Template Method.

Implementa AverageTicketCalculator, calculando a receita média por venda ganha.
"""

from datetime import datetime
from typing import Any

from models.customer import Customer
from models.enums import PipelineStep
from models.pipeline import Pipeline
from patterns.template_method.base_metric_calculator import BaseMetricCalculator


class AverageTicketCalculator(BaseMetricCalculator):
    """Calculadora concreta para o Ticket Médio das vendas ganhas."""

    metric_key: str = "ticket_medio"
    metric_name: str = "Ticket Médio"

    def fetch_data(
        self, start_date: datetime, end_date: datetime, company_id: int | None
    ) -> list[Pipeline]:
        """Busca pipelines em etapas de fechamento no período informado."""
        query = Pipeline.query.filter(
            Pipeline.date.isnot(None),
            Pipeline.date >= start_date,
            Pipeline.date <= end_date,
            Pipeline.step.in_([PipelineStep.CLOSING, PipelineStep.FOLLOW_UP]),
        )
        if company_id is not None:
            query = query.join(Customer).filter(Customer.company_id == company_id)

        return query.all()

    def calculate(self, raw_data: list[Pipeline]) -> float:
        """Calcula o valor financeiro médio por negócio fechado com sucesso."""
        if not raw_data:
            return 0.0

        total_revenue = sum(p.calculate_total() for p in raw_data)
        return round(float(total_revenue) / len(raw_data), 2)
