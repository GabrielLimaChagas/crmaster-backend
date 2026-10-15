"""Modelo de dados para persistência e auditoria de Notificações enviadas."""

from datetime import datetime
from patterns.singleton.db_connection import DBConnection

db = DBConnection().db


class Notification(db.Model):
    """Entidade que armazena o histórico e auditoria de notificações enviadas."""

    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False
    )
    recipient = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    company = db.relationship('Company', backref=db.backref('notifications', lazy=True, cascade='all, delete-orphan'))

    def to_dict(self):
        """Converte o modelo para dicionário serializável."""
        return {
            'id': self.id,
            'company_id': self.company_id,
            'recipient': self.recipient,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
