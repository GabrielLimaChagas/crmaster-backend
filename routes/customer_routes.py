"""Rotas para importação em lote de clientes utilizando o padrão Template Method."""

import json
from typing import Any
from flask import Blueprint, jsonify, request
from patterns.template_method import (
    BaseCustomerImporter,
    CSVCustomerImporter,
    JSONCustomerImporter,
)

customer_bp = Blueprint("customer_bp", __name__, url_prefix="/api/customers")


def run_customer_importer(
    importer: BaseCustomerImporter,
    content: str | bytes,
) -> dict[str, Any]:
    """Função utilitária polimórfica que executa qualquer importador baseado em BaseCustomerImporter.

    Demonstra o princípio de substituição de Liskov e o polimorfismo do Template Method:
    o chamador depende apenas da interface abstrata `BaseCustomerImporter`, enquanto a
    execução real do passo primitivo `extract_data` varia conforme a classe concreta.

    Args:
        importer: Instância concreta de qualquer subclasse de BaseCustomerImporter.
        content: Conteúdo do arquivo a ser processado.

    Returns:
        Relatório consolidado de importação.
    """
    return importer.import_customers(content)


@customer_bp.route("/import", methods=["POST"])
def import_customers_endpoint():
    """Endpoint unificado para importação em lote via upload de arquivo ou payload JSON.

    Detecta automaticamente o formato (CSV ou JSON) pelo nome do arquivo,
    Content-Type ou parâmetro `format`, instanciando a subclasse polimórfica correspondente.

    Exemplos de uso:
        1. Multipart Form:
           - file: arquivo clientes.csv ou clientes.json
           - company_id: 1
        2. JSON Payload:
           - { "company_id": 1, "format": "json", "data": [...] }
    """
    company_id: int | None = None
    file_bytes: bytes | None = None
    file_format: str | None = None

    # Caso 1: Upload de arquivo via formulário multipart
    if "file" in request.files:
        uploaded_file = request.files["file"]
        company_id_raw = request.form.get("company_id") or request.args.get("company_id")

        if not company_id_raw:
            return jsonify({
                "success": False,
                "error": "O parâmetro 'company_id' é obrigatório no formulário ou query string.",
            }), 400

        try:
            company_id = int(company_id_raw)
        except ValueError:
            return jsonify({"success": False, "error": "'company_id' deve ser um número inteiro."}), 400

        filename = uploaded_file.filename or ""
        file_bytes = uploaded_file.read()

        if filename.lower().endswith(".csv"):
            file_format = "csv"
        elif filename.lower().endswith(".json"):
            file_format = "json"
        else:
            # Fallback para o tipo MIME ou parâmetro 'format'
            file_format = request.form.get("format", "").lower()

    # Caso 2: Payload JSON direto
    elif request.is_json:
        payload = request.get_json(silent=True) or {}
        company_id = payload.get("company_id")
        file_format = payload.get("format", "json").lower()
        raw_data = payload.get("data") or payload.get("content")

        if company_id is None:
            return jsonify({"success": False, "error": "O campo 'company_id' é obrigatório no corpo JSON."}), 400

        try:
            company_id = int(company_id)
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "'company_id' deve ser um número inteiro."}), 400

        if raw_data is None:
            return jsonify({"success": False, "error": "Campo 'data' ou 'content' com os clientes é obrigatório."}), 400

        if isinstance(raw_data, (list, dict)):
            file_bytes = json.dumps(raw_data).encode("utf-8")
        elif isinstance(raw_data, str):
            file_bytes = raw_data.encode("utf-8")

    else:
        return jsonify({
            "success": False,
            "error": "Envie um arquivo via multipart/form-data ('file') ou um JSON contendo 'company_id' e 'data'.",
        }), 400

    if not file_bytes:
        return jsonify({"success": False, "error": "Conteúdo do arquivo vazio ou não informado."}), 400

    # Seleção polimórfica do importador com base no formato
    importer: BaseCustomerImporter
    if file_format == "csv":
        importer = CSVCustomerImporter(company_id=company_id)
    elif file_format == "json":
        importer = JSONCustomerImporter(company_id=company_id)
    else:
        return jsonify({
            "success": False,
            "error": f"Formato '{file_format}' não suportado. Formatos aceitos: 'csv' e 'json'.",
        }), 400

    try:
        # Invocação polimórfica através da função utilitária / Template Method
        report = run_customer_importer(importer, file_bytes)
        return jsonify(report), 200
    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as exc:
        return jsonify({
            "success": False,
            "error": f"Erro interno ao processar a importação: {str(exc)}",
        }), 500


@customer_bp.route("/import/csv", methods=["POST"])
def import_csv_endpoint():
    """Endpoint dedicado para importação de clientes a partir de arquivo ou texto CSV."""
    company_id_raw = request.form.get("company_id") or request.args.get("company_id")
    if not company_id_raw:
        return jsonify({"success": False, "error": "'company_id' é obrigatório."}), 400

    try:
        company_id = int(company_id_raw)
    except ValueError:
        return jsonify({"success": False, "error": "'company_id' deve ser um inteiro."}), 400

    if "file" in request.files:
        content = request.files["file"].read()
    else:
        content = request.get_data()

    if not content:
        return jsonify({"success": False, "error": "Nenhum dado CSV enviado."}), 400

    importer = CSVCustomerImporter(company_id=company_id)
    try:
        report = run_customer_importer(importer, content)
        return jsonify(report), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@customer_bp.route("/import/json", methods=["POST"])
def import_json_endpoint():
    """Endpoint dedicado para importação de clientes a partir de JSON."""
    company_id_raw = request.args.get("company_id")
    payload = request.get_json(silent=True)

    if not company_id_raw and isinstance(payload, dict):
        company_id_raw = payload.get("company_id")

    if not company_id_raw:
        return jsonify({"success": False, "error": "'company_id' é obrigatório."}), 400

    try:
        company_id = int(company_id_raw)
    except ValueError:
        return jsonify({"success": False, "error": "'company_id' deve ser um inteiro."}), 400

    if "file" in request.files:
        content = request.files["file"].read()
    elif isinstance(payload, dict) and "data" in payload:
        content = json.dumps(payload["data"])
    elif payload is not None:
        content = json.dumps(payload)
    else:
        content = request.get_data()

    if not content:
        return jsonify({"success": False, "error": "Nenhum dado JSON enviado."}), 400

    importer = JSONCustomerImporter(company_id=company_id)
    try:
        report = run_customer_importer(importer, content)
        return jsonify(report), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
