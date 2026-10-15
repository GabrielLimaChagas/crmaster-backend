"""Rotas da API para consulta e gerenciamento de Notificações registradas."""

from flask import Blueprint, jsonify, request
from models.notification import Notification, db

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

        notifications = query.order_by(Notification.id.desc()).all()
        return jsonify([n.to_dict() for n in notifications]), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@notification_bp.route("/<int:notification_id>", methods=["DELETE"])
def delete_notification(notification_id):
    """Exclui uma notificação específica pelo ID."""
    try:
        notification = Notification.query.get(notification_id)
        if not notification:
            return jsonify({"success": False, "error": "Notificação não encontrada."}), 404

        db.session.delete(notification)
        db.session.commit()
        return jsonify({"success": True, "message": "Notificação excluída com sucesso."}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 500


@notification_bp.route("", methods=["DELETE"])
@notification_bp.route("/clear", methods=["DELETE"])
def clear_company_notifications():
    """Limpa todas as notificações de uma determinada empresa."""
    try:
        company_id = request.args.get("company_id", type=int)
        if company_id is None:
            return jsonify({
                "success": False,
                "error": "Parâmetro company_id é obrigatório para limpeza de notificações."
            }), 400

        deleted_count = Notification.query.filter_by(company_id=company_id).delete()
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Notificações excluídas com sucesso.",
            "deleted_count": deleted_count
        }), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 500
