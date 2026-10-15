"""Fachada de Mensagens e Notificações (GoF Facade Pattern).

Centraliza a orquestração de disparos de e-mails via EmailService e a
auditoria/persistência do histórico de notificações via NotificationRecordService.
"""

from typing import TYPE_CHECKING
from patterns.facade.email_service import EmailService
from patterns.facade.notification_record_service import NotificationRecordService

if TYPE_CHECKING:
    from models.customer import Customer
    from models.user import User


class MessageNotificationFacade:
    """Fachada unificada para envio e auditoria de notificações no sistema CRMaster."""

    def __init__(
        self,
        email_service: EmailService | None = None,
        record_service: NotificationRecordService | None = None,
    ) -> None:
        """Inicializa a fachada instanciando os subsistemas técnicos."""
        self.email_service = email_service or EmailService()
        self.record_service = record_service or NotificationRecordService()

    def notify_and_record(
        self, company_id: int, recipient_email: str, title: str, content: str
    ) -> bool:
        """Dispara o e-mail via EmailService e grava o registro na tabela notifications.

        Args:
            company_id: ID da empresa associada.
            recipient_email: Endereço de e-mail do destinatário.
            title: Assunto/título da notificação.
            content: Corpo textual da mensagem.

        Returns:
            True se o e-mail foi disparado com sucesso pelo SMTP, False caso contrário.
        """
        # 1. Disparo de e-mail através do subsistema EmailService
        email_sent = self.email_service.send_smtp(
            recipient_email=recipient_email,
            subject=title,
            message_body=content,
        )

        # 2. Auditoria e persistência através do subsistema NotificationRecordService
        self.record_service.save_notification(
            company_id=company_id,
            recipient=recipient_email,
            title=title,
            content=content,
        )

        return email_sent

    def send_welcome_company_notification(
        self,
        company_id: int,
        user_email: str,
        user_name: str,
        company_name: str,
        plugins_list: list[str],
        password: str,
    ) -> bool:
        """Monta a mensagem de boas-vindas e credenciais da nova empresa, delegando para notify_and_record."""
        plugins_formatted = (
            "\n".join(f"  • {p}" for p in plugins_list)
            if plugins_list
            else "  • Nenhum plugin adicional selecionado"
        )

        title = f"Bem-vindo ao CRMaster! Acesso da empresa {company_name}"
        content = (
            f"Olá {user_name},\n\n"
            f"Seja muito bem-vindo à plataforma CRMaster!\n\n"
            f"Sua empresa foi cadastrada com sucesso:\n"
            f"Nome da Empresa: {company_name}\n\n"
            f"Módulos e Plugins Liberados:\n"
            f"{plugins_formatted}\n\n"
            f"Credenciais de Primeiro Acesso:\n"
            f"E-mail (Login): {user_email}\n"
            f"Senha Temporária: {password}\n\n"
            f"Recomendamos que você altere sua senha após o primeiro login.\n\n"
            f"Atenciosamente,\n"
            f"Equipe de Sucesso do Cliente CRMaster"
        )

        return self.notify_and_record(
            company_id=company_id,
            recipient_email=user_email,
            title=title,
            content=content,
        )

    def send_sale_won_notifications(
        self,
        company_id: int,
        customer: "Customer | None",
        employee: "User | None",
        total_amount: float,
    ) -> None:
        """Dispara e audita as mensagens de confirmação do cliente e comemoração do vendedor."""
        # 1. Notificação do Cliente
        if customer and customer.email:
            customer_name = customer.name or "Cliente"
            customer_title = f"Compra Confirmada! Parabéns, {customer_name}"
            customer_content = (
                f"Olá {customer_name},\n\n"
                f"Sua compra foi confirmada com sucesso!\n"
                f"Valor Total: R$ {total_amount:,.2f}\n\n"
                f"Obrigado pela confiança!\n"
                f"Equipe CRMaster"
            )
            self.notify_and_record(
                company_id=company_id,
                recipient_email=customer.email,
                title=customer_title,
                content=customer_content,
            )

        # 2. Notificação do Vendedor
        if employee and employee.email:
            employee_name = employee.name or "Vendedor"
            customer_name = customer.name if customer else "Cliente"
            employee_title = f"Parabéns! Negócio Fechado com {customer_name}"
            employee_content = (
                f"Olá {employee_name},\n\n"
                f"Parabéns pelo fechamento de mais uma venda no CRMaster!\n\n"
                f"Cliente: {customer_name}\n"
                f"Valor Gerado: R$ {total_amount:,.2f}\n\n"
                f"Continue com o excelente trabalho!\n"
                f"Gestão Comercial CRMaster"
            )
            self.notify_and_record(
                company_id=company_id,
                recipient_email=employee.email,
                title=employee_title,
                content=employee_content,
            )
