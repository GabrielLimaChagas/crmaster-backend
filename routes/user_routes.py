"""Rotas da API para gerenciamento de Usuários e Colaboradores."""

from flask import Blueprint, jsonify, request
from models.user import User
from patterns.singleton.db_connection import DBConnection

db = DBConnection().db
user_bp = Blueprint("user_bp", __name__, url_prefix="/api/users")


@user_bp.route("/login", methods=["POST"])
def login_user():
    """Valida as credenciais do usuário para login."""
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


@user_bp.route("", methods=["GET"])
def list_users():
    """Lista todos os usuários/colaboradores cadastrados.
    
    Query Params opcionais:
        company_id: Filtra por empresa.
        role: Filtra por cargo/papel (EMPLOYEE, COMPANY, MANAGER).
    """
    try:
        query = User.query
        company_id = request.args.get("company_id", type=int)
        if company_id is not None:
            query = query.filter_by(company_id=company_id)

        role = request.args.get("role")
        if role:
            query = query.filter_by(role=role.strip().upper())

        users = query.order_by(User.id.asc()).all()
        return jsonify([u.to_dict() for u in users]), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@user_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id: int):
    """Retorna os dados detalhados de um usuário específico."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "error": "Usuário não encontrado."}), 404
    return jsonify(user.to_dict()), 200


@user_bp.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id: int):
    """Atualiza as informações cadastrais de um usuário."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "error": "Usuário não encontrado."}), 404

    payload = request.get_json(silent=True) or {}
    if "name" in payload and str(payload["name"]).strip():
        user.name = str(payload["name"]).strip()
    if "email" in payload and str(payload["email"]).strip():
        user.email = str(payload["email"]).strip()
    if "password" in payload and str(payload["password"]).strip():
        user.password = str(payload["password"]).strip()

    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Usuário atualizado com sucesso.",
            "user": user.to_dict()
        }), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 500
