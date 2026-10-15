"""Fachada de checkout e fechamento de vendas (GoF Facade Pattern).

Unifica e simplifica a coordenação entre transição de pipeline, persistência
transacional no banco de dados e disparo de notificações por e-mail.
"""

from patterns.facade.email_service import EmailService
from patterns.facade.pipeline_service import PipelineService
from patterns.singleton.db_connection import DBConnection


class SaleCheckoutFacade:
    """Fachada de alto nível para fechamento de vendas e conclusão de oportunidades.

    Oculta a complexidade de orquestrar a consulta de pipeline, transição de etapa,
    persistência transacional com rollback e notificações por e-mail para cliente e vendedor.
    """

    def __init__(self) -> None:
        """Inicializa a fachada com a conexão do banco de dados."""
        self.db = DBConnection().db

    def close_sale(self, pipeline_id: int, closing_note: str | None = None) -> bool:
        """Executa o fechamento completo da venda.

        Etapas orquestradas:
            1. Consulta e validação da existência da pipeline.
            2. Transição de etapa para CLOSING, anexação da nota e cálculo do total.
            3. Commit atômico no banco com rollback em caso de falha.
            4. Disparo de e-mails para cliente e vendedor.

        Args:
            pipeline_id: ID da oportunidade a ser fechada.
            closing_note: Anotação opcional de fechamento.

        Returns:
            True se a venda foi fechada e persistida com sucesso.

        Raises:
            ValueError: Se a pipeline informada não existir.
            Exception: Se houver falha na persistência transacional.
        """
        # 1. Consulta da pipeline através do subsistema PipelineService
        pipeline = PipelineService.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline com ID {pipeline_id} não encontrada.")

        # 2. Transição e cálculo através do subsistema PipelineService
        total_amount, customer, employee = PipelineService.process_closing(
            pipeline=pipeline, closing_note=closing_note
        )

        # 3. Persistência atômica com rollback
        try:
            self.db.session.commit()
        except Exception as exc:
            self.db.session.rollback()
            raise exc

        # 4. Disparo de notificações estruturadas através do subsistema EmailService
        if customer and customer.email:
            EmailService.notify_customer_sale_closed(
                customer_email=customer.email,
                customer_name=customer.name,
                total_amount=total_amount,
            )

        if employee and employee.email:
            EmailService.notify_employee_deal_won(
                employee_email=employee.email,
                employee_name=employee.name,
                customer_name=customer.name if customer else "Cliente",
                total_amount=total_amount,
            )

        return True
