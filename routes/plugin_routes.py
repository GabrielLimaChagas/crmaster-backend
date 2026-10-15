"""Rotas da API para consulta de Plugins e Módulos disponíveis."""

from flask import Blueprint, jsonify
from models.plugin import Plugin

plugin_bp = Blueprint("plugin_bp", __name__, url_prefix="/api/plugins")


@plugin_bp.route("", methods=["GET"])
def list_plugins():
    """Retorna todos os plugins cadastrados na plataforma."""
    try:
        plugins = Plugin.query.order_by(Plugin.id.asc()).all()
        return jsonify([p.to_dict() for p in plugins]), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
