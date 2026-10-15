"""Rotas da API para gerenciamento e Onboarding de Empresas via Facade."""

from flask import Blueprint, jsonify, request
from models.company import Company
from patterns.facade import CompanyOnboardingFacade
from patterns.singleton.db_connection import DBConnection

db = DBConnection().db
company_bp = Blueprint("company_bp", __name__, url_prefix="/api/companies")


@company_bp.route("/onboard", methods=["POST"])
@company_bp.route("/register", methods=["POST"])
def onboard_company():
    """Endpoint para cadastro e onboarding completo de uma nova empresa.

    Utiliza o padrão estrutural Facade (CompanyOnboardingFacade) para orquestrar:
    - Cadastro da Empresa
    - Habilitação dos Plugins selecionados
    - Criação do Usuário Administrador (Role COMPANY)
    - Envio do e-mail de boas-vindas com credenciais

    Payload JSON esperado:
        {
            "company_name": "Tech Corp",
            "cnpj": "12.345.678/0001-90",
            "user_name": "Diretor Tech",
            "user_email": "diretor@techcorp.com",
            "password": "senha_temporaria123",
            "plugin_ids": [1, 2]
        }

    Retorno:
        201: Empresa e usuário criados com sucesso
        400: Dados inválidos ou e-mail já existente
        500: Erro interno de persistência
    """
    payload = request.get_json(silent=True) or {}

    company_name = payload.get("company_name")
    cnpj = payload.get("cnpj")
    user_name = payload.get("user_name")
    user_email = payload.get("user_email")
    password = payload.get("password")
    plugin_ids = payload.get("plugin_ids", [])

    facade = CompanyOnboardingFacade()

    try:
        result = facade.register_company(
            company_name=company_name,
            cnpj=cnpj,
            user_name=user_name,
            user_email=user_email,
            password=password,
            plugin_ids=plugin_ids,
        )
        return jsonify(result), 201
    except ValueError as ve:
        return jsonify({
            "success": False,
            "error": str(ve),
        }), 400
    except Exception as exc:
        return jsonify({
            "success": False,
            "error": f"Erro interno ao realizar onboarding da empresa: {str(exc)}",
        }), 500


@company_bp.route("", methods=["GET"])
def list_companies():
    """Retorna a lista de empresas cadastradas no sistema."""
    try:
        companies = Company.query.order_by(Company.id.asc()).all()
        return jsonify([c.to_dict() for c in companies]), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@company_bp.route("/<int:company_id>", methods=["GET"])
def get_company(company_id: int):
    """Retorna os dados de uma empresa específica por ID."""
    company = Company.query.get(company_id)
    if not company:
        return jsonify({"success": False, "error": "Empresa não encontrada."}), 404
    return jsonify(company.to_dict()), 200


@company_bp.route("/<int:company_id>", methods=["PUT"])
def update_company(company_id: int):
    """Atualiza as informações cadastrais da empresa."""
    company = Company.query.get(company_id)
    if not company:
        return jsonify({"success": False, "error": "Empresa não encontrada."}), 404

    payload = request.get_json(silent=True) or {}
    if "name" in payload and str(payload["name"]).strip():
        company.name = str(payload["name"]).strip()
    if "company_name" in payload and str(payload["company_name"]).strip():
        company.name = str(payload["company_name"]).strip()
    if "cnpj" in payload and str(payload["cnpj"]).strip():
        company.cnpj = str(payload["cnpj"]).strip()

    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Empresa atualizada com sucesso.",
            "company": company.to_dict()
        }), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 500


@company_bp.route("/<int:company_id>/plugins", methods=["GET"])
def get_company_plugins(company_id: int):
    """Retorna a lista de plugins ativos da empresa."""
    company = Company.query.get(company_id)
    if not company:
        return jsonify({"success": False, "error": "Empresa não encontrada."}), 404

    plugins = []
    if company.company_plugins:
        for cp in company.company_plugins:
            if cp.plugin:
                plugins.append(cp.plugin.to_dict())

    return jsonify(plugins), 200
