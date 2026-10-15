"""Rotas de autenticação (Login e Logout)."""

from flask import Blueprint, jsonify, request
from models.user import User
from patterns.singleton.db_connection import DBConnection

db = DBConnection().db
auth_bp = Blueprint("auth_bp", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=["POST"])
def auth_login():
    """Endpoint de autenticação de usuários via e-mail/usuário e senha."""
    try:
        payload = request.get_json(silent=True) or {}
        identifier = str(payload.get("username") or payload.get("email") or "").strip()
        password = str(payload.get("password") or "").strip()

        if not identifier or not password:
            return jsonify({
                "success": False,
                "error": "Informe o usuário/e-mail e a senha."
            }), 400

        user = User.query.filter(
            (db.func.lower(User.email) == identifier.lower()) | (User.name == identifier)
        ).first()

        if not user or user.password != password:
            return jsonify({
                "success": False,
                "error": "Usuário ou senha inválidos."
            }), 401

        return jsonify({
            "success": True,
            "message": "Login realizado com sucesso.",
            "user": user.to_dict()
        }), 200
    except Exception as exc:
        return jsonify({
            "success": False,
            "error": "Não foi possível concluir a ação. Tente novamente."
        }), 500


@auth_bp.route("/logout", methods=["POST"])
def auth_logout():
    """Logout do usuário."""
    return jsonify({
        "success": True,
        "message": "Logout realizado com sucesso."
    }), 200
