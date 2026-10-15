"""Subsistema de notificação por e-mail para o padrão Facade.

Integra com o singleton GmailService para disparo de e-mails transacionais reais
e registra notificações estruturadas de fechamento de venda e comemoração.
"""

import logging
from patterns.singleton.email_service import GmailService

logger = logging.getLogger("CRMaster.EmailService")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class EmailService:
    """Subsistema responsável por emitir notificações por e-mail no fechamento de vendas."""

    @staticmethod
    def notify_customer_sale_closed(customer_email: str, customer_name: str, total_amount: float) -> None:
        """Emite notificação de confirmação de compra para o cliente via GmailService."""
        msg = (
            f"[NOTIFICAÇÃO CLIENTE] Para: {customer_email} | Cliente: {customer_name} | "
            f"Status: Venda Confirmada | Valor Total: R$ {total_amount:,.2f}"
        )
        logger.info(msg)
        print(f"\n>>> {msg}\n")

        # Disparo de e-mail real via GmailService singleton
        try:
            gmail_service = GmailService()
            subject = f"Compra Confirmada! Parabéns, {customer_name}"
            body = (
                f"Olá {customer_name},\n\n"
                f"Sua compra foi confirmada com sucesso!\n"
                f"Valor Total: R$ {total_amount:,.2f}\n\n"
                f"Obrigado pela confiança!\n"
                f"Equipe CRMaster"
            )
            gmail_service.send_email(
                to_email=customer_email,
                subject=subject,
                body=body,
                is_html=False,
            )
            logger.info(f"[EMAIL ENVIADO] E-mail de confirmação enviado para o cliente: {customer_email}")
        except Exception as exc:
            logger.error(f"[EMAIL FALHA] Não foi possível enviar e-mail para o cliente {customer_email}: {exc}")

    @staticmethod
    def notify_employee_deal_won(
        employee_email: str, employee_name: str, customer_name: str, total_amount: float
    ) -> None:
        """Emite notificação de comemoração de negócio ganho para o vendedor via GmailService."""
        msg = (
            f"[NOTIFICAÇÃO VENDEDOR] Para: {employee_email} | Vendedor: {employee_name} | "
            f"Oportunidade Fechada com {customer_name} | Valor Gerado: R$ {total_amount:,.2f}"
        )
        logger.info(msg)
        print(f"\n>>> {msg}\n")

        # Disparo de e-mail real via GmailService singleton
        try:
            gmail_service = GmailService()
            subject = f"Parabéns! Negócio Fechado com {customer_name}"
            body = (
                f"Olá {employee_name},\n\n"
                f"Parabéns pelo fechamento de mais uma venda no CRMaster!\n\n"
                f"Cliente: {customer_name}\n"
                f"Valor Gerado: R$ {total_amount:,.2f}\n\n"
                f"Continue com o excelente trabalho!\n"
                f"Gestão Comercial CRMaster"
            )
            gmail_service.send_email(
                to_email=employee_email,
                subject=subject,
                body=body,
                is_html=False,
            )
            logger.info(f"[EMAIL ENVIADO] E-mail de celebração enviado para o vendedor: {employee_email}")
        except Exception as exc:
            logger.error(f"[EMAIL FALHA] Não foi possível enviar e-mail para o vendedor {employee_email}: {exc}")

    @staticmethod
    def send_company_welcome_email(
        user_email: str,
        user_name: str,
        company_name: str,
        plugins_list: list[str],
        password: str,
    ) -> bool:
        """Envia e-mail de boas-vindas para o administrador da nova empresa com credenciais e plugins."""
        msg = (
            f"[NOTIFICAÇÃO ONBOARDING] Para: {user_email} | Usuário: {user_name} | "
            f"Empresa: {company_name} | Plugins: {len(plugins_list)}"
        )
        logger.info(msg)
        print(f"\n>>> {msg}\n")

        plugins_formatted = (
            "\n".join(f"  • {p}" for p in plugins_list)
            if plugins_list
            else "  • Nenhum plugin adicional selecionado"
        )

        subject = f"Bem-vindo ao CRMaster! Acesso da empresa {company_name}"
        body = (
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

        try:
            gmail_service = GmailService()
            gmail_service.send_email(
                to_email=user_email,
                subject=subject,
                body=body,
                is_html=False,
            )
            logger.info(f"[EMAIL ENVIADO] E-mail de boas-vindas enviado com sucesso para {user_email}")
            return True
        except Exception as exc:
            logger.error(f"[EMAIL FALHA] Não foi possível enviar e-mail de boas-vindas para {user_email}: {exc}")
            return False

