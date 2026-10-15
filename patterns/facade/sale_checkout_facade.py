"""Fachada de checkout e fechamento de vendas (GoF Facade Pattern).

Unifica e simplifica a coordenação entre transição de pipeline, persistência
transacional no banco de dados e disparo auditado de notificações via MessageNotificationFacade.
"""

from patterns.facade.message_notification_facade import MessageNotificationFacade
from patterns.facade.pipeline_service import PipelineService
from patterns.singleton.db_connection import DBConnection


class SaleCheckoutFacade:
    """Fachada de alto nível para fechamento de vendas e conclusão de oportunidades.

    Oculta a complexidade de orquestrar a consulta de pipeline, transição de etapa,
    persistência transacional com rollback e delegação de notificações para a MessageNotificationFacade.
    """

    def __init__(self, notification_facade: MessageNotificationFacade | None = None) -> None:
        """Inicializa a fachada com a conexão do banco de dados e a fachada de notificações."""
        self.db = DBConnection().db
        self.notification_facade = notification_facade or MessageNotificationFacade()

    def close_sale(self, pipeline_id: int, closing_note: str | None = None) -> bool:
        """Executa o fechamento completo da venda.

        Etapas orquestradas:
            1. Consulta e validação da existência da pipeline.
            2. Transição de etapa para CLOSING, anexação da nota e cálculo do total via PipelineService.
            3. Commit atômico no banco com rollback em caso de falha.
            4. Recuperação do company_id associado.
            5. Disparo de notificações estruturadas via MessageNotificationFacade.

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

        # 4. Recuperação do company_id
        company_id = (
            getattr(customer, "company_id", None)
            or getattr(employee, "company_id", None)
            or 1
        )

        # 5. Invocação exclusiva da Fachada de Notificações (sem acesso direto a EmailService/GmailService)
        self.notification_facade.send_sale_won_notifications(
            company_id=company_id,
            customer=customer,
            employee=employee,
            total_amount=total_amount,
        )

        return True
