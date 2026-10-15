"""Subsistema de auditoria e persistência de notificações no banco de dados."""

from typing import Any
from models.notification import Notification
from patterns.singleton.db_connection import DBConnection


class NotificationRecordService:
    """Subsistema responsável por persistir o histórico de notificações na tabela 'notifications'."""

    def __init__(self, db_session: Any = None) -> None:
        """Inicializa o serviço de auditoria com a sessão do SQLAlchemy.

        Args:
            db_session: Sessão do SQLAlchemy (opcional; se omitida, usa DBConnection().db.session).
        """
        self.db_session = db_session if db_session is not None else DBConnection().db.session

    def save_notification(
        self, company_id: int, recipient: str, title: str, content: str
    ) -> Notification:
        """Cria e persiste uma nova notificação no banco de dados.

        Args:
            company_id: ID da empresa associada.
            recipient: Destinatário da notificação (ex.: e-mail).
            title: Título ou assunto da notificação.
            content: Conteúdo ou corpo da mensagem.

        Returns:
            Instância persistida de Notification.
        """
        notification = Notification(
            company_id=company_id,
            recipient=str(recipient).strip(),
            title=str(title).strip() if title else None,
            content=str(content).strip(),
        )
        self.db_session.add(notification)
        self.db_session.commit()
        return notification
