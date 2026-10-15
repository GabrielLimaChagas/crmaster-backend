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

    def close_sale(
        self,
        pipeline_id: int,
        closing_note: str | None = None,
        company_id: int | None = None,
    ) -> bool:
        """Executa o fechamento completo da venda.

        Etapas orquestradas:
            1. Consulta e validação da existência da pipeline.
            2. Transição de etapa para CLOSING, anexação da nota e cálculo do total via PipelineService.
            3. Commit atômico no banco com rollback em caso de falha.
            4. Recuperação e resolução dinâmica do company_id da empresa.
            5. Disparo de notificações estruturadas via MessageNotificationFacade.

        Args:
            pipeline_id: ID da oportunidade a ser fechada.
            closing_note: Anotação opcional de fechamento.
            company_id: ID opcional da empresa passado explicitamente pelo cliente/rota.

        Returns:
            True se a venda foi fechada e persistida com sucesso.

        Raises:
            ValueError: Se a pipeline não existir ou não for possível identificar a empresa vinculada.
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

        # 4. Resolução dinâmica e priorizada do company_id:
        resolved_company_id = company_id

        # 1ª prioridade: payload ou header da requisição enviado pelo frontend
        if not resolved_company_id:
            try:
                from flask import has_request_context, request
                if has_request_context():
                    req_json = request.get_json(silent=True) or {}
                    c_id = (
                        req_json.get("company_id")
                        or request.headers.get("X-Company-Id")
                        or request.headers.get("X-Company-ID")
                        or request.args.get("company_id")
                    )
                    if c_id is not None:
                        try:
                            resolved_company_id = int(c_id)
                        except (ValueError, TypeError):
                            resolved_company_id = None
            except Exception:
                pass

        # 2ª prioridade: vendedor responsável (pipeline.employee.company_id / employee.company.id)
        if not resolved_company_id and employee:
            resolved_company_id = getattr(employee, "company_id", None) or (
                employee.company.id if getattr(employee, "company", None) else None
            )

        # 3ª prioridade: cliente associado (pipeline.customer.company_id / customer.company.id)
        if not resolved_company_id and customer:
            resolved_company_id = getattr(customer, "company_id", None) or (
                customer.company.id if getattr(customer, "company", None) else None
            )

        # Validação estrita: não aceita fallback para 1
        if not resolved_company_id:
            raise ValueError(
                f"Não foi possível identificar a empresa vinculada à pipeline {pipeline_id} para emissão de notificações."
            )

        # 5. Invocação exclusiva da Fachada de Notificações com o company_id dinâmico resolvido
        self.notification_facade.send_sale_won_notifications(
            company_id=resolved_company_id,
            customer=customer,
            employee=employee,
            total_amount=total_amount,
        )

        return True
