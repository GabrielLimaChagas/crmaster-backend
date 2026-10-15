"""Rotas da API para consulta de Notificações registradas."""

from flask import Blueprint, jsonify, request
from models.notification import Notification

notification_bp = Blueprint("notification_bp", __name__, url_prefix="/api/notifications")


@notification_bp.route("", methods=["GET"])
def list_notifications():
    """Lista as notificações registradas na base de dados para auditoria.

    Query parameters opcionais:
        company_id (int): Filtra por empresa.
        recipient (str): Filtra por e-mail do destinatário.

    Retorno:
        200: Lista de notificações em formato JSON
        500: Erro interno do servidor
    """
    try:
        query = Notification.query

        company_id = request.args.get("company_id", type=int)
        if company_id is not None:
            query = query.filter_by(company_id=company_id)

        recipient = request.args.get("recipient", type=str)
        if recipient:
            query = query.filter_by(recipient=recipient.strip())

        notifications = query.order_by(Notification.created_at.desc()).all()
        return jsonify([n.to_dict() for n in notifications]), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
