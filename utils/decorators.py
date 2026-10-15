"""Decorators de controle de acesso e validação de regras de negócio."""

from functools import wraps
from flask import jsonify, request
from models.company_plugin import CompanyPlugin
from models.plugin import Plugin
from models.notification import Notification
from models.user import User
from patterns.singleton.db_connection import DBConnection

db = DBConnection().db

PLUGIN_NAME_ALIASES: dict[str, list[str]] = {
    "notifications_plugin": [
        "notifications_plugin",
        "Notificações",
        "Notificacoes",
        "notificacoes",
        "notificações",
        "Integração WhatsApp & Mensageria",
        "Integracao WhatsApp & Mensageria",
    ],
    "import_export_plugin": [
        "import_export_plugin",
        "Importação e Exportação",
        "Importacao e Exportacao",
        "import_export",
        "importacao_exportacao",
    ],
}


def get_request_company_id() -> int | None:
    """Extrai o company_id a partir dos cabeçalhos, parâmetros, corpo ou contexto da requisição."""
    # 1. Cabeçalhos HTTP explícitos (enviados pelo cliente / frontend)
    cid_header = request.headers.get("X-Company-ID") or request.headers.get("Company-ID")
    if cid_header and str(cid_header).strip().isdigit():
        return int(cid_header.strip())

    # 2. Query string (?company_id=...)
    cid_query = request.args.get("company_id")
    if cid_query and str(cid_query).strip().isdigit():
        return int(cid_query.strip())

    # 3. Form-data multipart (ex.: uploads de arquivo de importação)
    if request.form and "company_id" in request.form:
        cid_form = request.form.get("company_id")
        if cid_form and str(cid_form).strip().isdigit():
            return int(cid_form.strip())

    # 4. JSON body (se aplicável e seguro)
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        if isinstance(payload, dict) and "company_id" in payload:
            cid_json = payload.get("company_id")
            if cid_json and str(cid_json).strip().isdigit():
                return int(cid_json)

    # 5. Parâmetros da rota (view_args)
    if request.view_args:
        if "company_id" in request.view_args:
            try:
                return int(request.view_args["company_id"])
            except (ValueError, TypeError):
                pass

        # Contexto específico para notificações individuais (/api/notifications/<id>)
        if "notification_id" in request.view_args:
            try:
                notif_id = int(request.view_args["notification_id"])
                notif = Notification.query.get(notif_id)
                if notif and notif.company_id:
                    return int(notif.company_id)
            except Exception:
                pass

    # 6. Cabeçalho de usuário logado (X-User-ID)
    user_header = request.headers.get("X-User-ID")
    if user_header and str(user_header).strip().isdigit():
        user = User.query.get(int(user_header.strip()))
        if user and user.company_id:
            return int(user.company_id)

    return None


def company_has_plugin(company_id: int, plugin_name: str) -> bool:
    """Verifica na tabela associativa company_plugin se o módulo está ativo para a empresa."""
    aliases = PLUGIN_NAME_ALIASES.get(plugin_name, [plugin_name])
    if plugin_name not in aliases:
        aliases.append(plugin_name)

    link = (
        db.session.query(CompanyPlugin)
        .join(Plugin, CompanyPlugin.plugin_id == Plugin.id)
        .filter(CompanyPlugin.company_id == company_id)
        .filter(
            (Plugin.name == plugin_name)
            | (db.func.lower(Plugin.name) == plugin_name.lower())
            | (Plugin.name.in_(aliases))
        )
        .first()
    )
    return link is not None


def require_plugin(plugin_name: str):
    """Decorator para validar se a empresa possui o plugin contratado.

    Aborta com HTTP 403 Forbidden caso a empresa não possua o vínculo ativo.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            company_id = get_request_company_id()
            if not company_id or not company_has_plugin(company_id, plugin_name):
                return jsonify({"error": "Módulo não contratado para esta empresa."}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
