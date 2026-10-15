"""Subsistema de gerenciamento e transição de pipelines de vendas.

Responsável por consultar o negócio, transicionar a etapa para CLOSING,
anexar anotações, calcular o total da venda e carregar cliente e vendedor.
"""

from models.customer import Customer
from models.enums import PipelineStep
from models.pipeline import Pipeline
from models.user import User


class PipelineService:
    """Subsistema especializado em regras de negócio e transições de estado da Pipeline."""

    @staticmethod
    def get_pipeline(pipeline_id: int) -> Pipeline | None:
        """Busca a pipeline de vendas pelo identificador único.

        Args:
            pipeline_id: Identificador da oportunidade.

        Returns:
            Instância de Pipeline ou None se não existir.
        """
        return Pipeline.query.get(pipeline_id)

    @staticmethod
    def process_closing(
        pipeline: Pipeline, closing_note: str | None = None
    ) -> tuple[float, Customer | None, User | None]:
        """Aplica a transição para CLOSING, anexa nota, calcula total e obtém cliente e vendedor.

        Args:
            pipeline: Instância de Pipeline a ser fechada.
            closing_note: Nota opcional de conclusão.

        Returns:
            Tupla contendo (total_amount, customer, employee).
        """
        # 1. Transição de estado para etapa de fechamento
        pipeline.step = PipelineStep.CLOSING

        # 2. Anexação de anotações de encerramento
        if closing_note:
            clean_note = str(closing_note).strip()
            if clean_note:
                if pipeline.note:
                    pipeline.note = f"{pipeline.note} | Conclusão: {clean_note}"
                else:
                    pipeline.note = f"Conclusão: {clean_note}"

        # 3. Cálculo financeiro do negócio
        total_amount = pipeline.calculate_total()

        # 4. Obtenção do cliente associado
        customer = pipeline.customer
        if not customer and pipeline.customer_id:
            customer = Customer.query.get(pipeline.customer_id)

        # 5. Obtenção do empregado/vendedor responsável
        employee = pipeline.employee
        if not employee and pipeline.employee_id:
            employee = User.query.get(pipeline.employee_id)

        return total_amount, customer, employee
