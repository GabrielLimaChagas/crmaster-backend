"""Subsistema técnico de envio de e-mails via SMTP/Gmail (Facade Pattern)."""

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
    """Subsistema responsável exclusivamente pelo disparo técnico de e-mails via GmailService (SMTP)."""

    def __init__(self) -> None:
        """Inicializa o subsistema com o singleton GmailService."""
        self.gmail_service = GmailService()

    @staticmethod
    def send_smtp(recipient_email: str, subject: str, message_body: str) -> bool:
        """Dispara e-mail via SMTP utilizando o singleton GmailService.

        Args:
            recipient_email: E-mail de destino.
            subject: Assunto da mensagem.
            message_body: Corpo textual do e-mail.

        Returns:
            True se o e-mail foi enviado com sucesso, False em caso de falha.
        """
        try:
            logger.info(f"[EMAIL SENDING] Destinatário: {recipient_email} | Assunto: {subject}")
            gmail = GmailService()
            success = gmail.send_email(
                to_email=recipient_email,
                subject=subject,
                body=message_body,
                is_html=False,
            )
            if success:
                logger.info(f"[EMAIL SENT] E-mail enviado com sucesso para {recipient_email}")
            else:
                logger.warning(f"[EMAIL WARNING] Falha ou recusa no envio de e-mail para {recipient_email}")
            return bool(success)
        except Exception as exc:
            logger.error(f"[EMAIL ERROR] Erro ao disparar e-mail para {recipient_email}: {exc}")
            return False
