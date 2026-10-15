"""Módulo para cálculo do Lifetime Value (LTV) via Template Method.

Implementa LTVCalculator, calculando a receita média gerada por cliente comprador.
"""

from datetime import datetime
from typing import Any

from models.customer import Customer
from models.enums import PipelineStep
from models.pipeline import Pipeline
from patterns.template_method.base_metric_calculator import BaseMetricCalculator


class LTVCalculator(BaseMetricCalculator):
    """Calculadora concreta para o Lifetime Value (LTV) de clientes com compras."""

    metric_key: str = "ltv"
    metric_name: str = "Lifetime Value (LTV)"

    def fetch_data(
        self, start_date: datetime, end_date: datetime, company_id: int | None
    ) -> list[Pipeline]:
        """Busca pipelines em etapas de fechamento associadas a clientes no período."""
        query = Pipeline.query.filter(
            Pipeline.date.isnot(None),
            Pipeline.date >= start_date,
            Pipeline.date <= end_date,
            Pipeline.step.in_([PipelineStep.CLOSING, PipelineStep.FOLLOW_UP]),
            Pipeline.customer_id.isnot(None),
        )
        if company_id is not None:
            query = query.join(Customer).filter(Customer.company_id == company_id)

        return query.all()

    def calculate(self, raw_data: list[Pipeline]) -> float:
        """Calcula a receita total acumulada dividida pela quantidade de clientes únicos."""
        if not raw_data:
            return 0.0

        total_revenue = sum(p.calculate_total() for p in raw_data)
        unique_customers = {p.customer_id for p in raw_data if p.customer_id is not None}

        if not unique_customers:
            return 0.0

        return round(float(total_revenue) / len(unique_customers), 2)
