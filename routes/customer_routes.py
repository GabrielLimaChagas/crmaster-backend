"""Rotas para importação em lote de clientes utilizando o padrão Template Method."""

import json
from datetime import datetime
from typing import Any
from flask import Blueprint, jsonify, request, Response
from models.customer import Customer
from models.company import Company
from patterns.singleton.db_connection import DBConnection
from patterns.template_method import CustomerImporter, CustomerExporter

db = DBConnection().db
customer_bp = Blueprint("customer_bp", __name__, url_prefix="/api/customers")


def run_customer_importer(
    importer: CustomerImporter,
    content: str | bytes,
    file_format: str = "json",
) -> dict[str, Any]:
    """Função utilitária que executa o importador de clientes através do Template Method.

    Args:
        importer: Instância de CustomerImporter configurada.
        content: Conteúdo do arquivo a ser processado.
        file_format: 'csv' ou 'json'.

    Returns:
        Relatório consolidado de importação.
    """
    return importer.import_data(content, file_format)


@customer_bp.route("/import", methods=["POST"])
def import_customers_endpoint():
    """Endpoint unificado para importação em lote via upload de arquivo ou payload JSON.

    Detecta automaticamente o formato (CSV ou JSON) pelo nome do arquivo,
    Content-Type ou parâmetro `format`, instanciando CustomerImporter.

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

    if file_format not in ("csv", "json"):
        return jsonify({
            "success": False,
            "error": f"Formato '{file_format}' não suportado. Formatos aceitos: 'csv' e 'json'.",
        }), 400

    try:
        importer = CustomerImporter(company_id=company_id)
        report = importer.import_data(file_bytes, file_format)
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

    try:
        importer = CustomerImporter(company_id=company_id)
        report = importer.import_data(content, "csv")
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

    try:
        importer = CustomerImporter(company_id=company_id)
        report = importer.import_data(content, "json")
        return jsonify(report), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@customer_bp.route("/export", methods=["GET"])
def export_customers_endpoint():
    """Endpoint para exportação de clientes nos formatos CSV ou JSON."""
    file_format = request.args.get("format", "csv")
    company_id_raw = request.args.get("company_id")
    company_id: int | None = None

    if company_id_raw:
        try:
            company_id = int(company_id_raw)
        except ValueError:
            return jsonify({"success": False, "error": "'company_id' deve ser um número inteiro."}), 400

    try:
        exporter = CustomerExporter(company_id=company_id)
        content, mimetype, filename = exporter.export_data(file_format)
        return Response(
            content,
            mimetype=mimetype,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": mimetype,
            },
        )
    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as exc:
        return jsonify({"success": False, "error": f"Erro na exportação de clientes: {str(exc)}"}), 500



def format_customer_for_list(customer: Customer) -> dict:
    return {
        "id": customer.id,
        "name": customer.name,
        "pipelinesCount": len(customer.pipelines) if customer.pipelines else 0,
        "phone": customer.cel or "",
        "cel": customer.cel or "",
        "email": customer.email or "",
        "notes": customer.notes or "",
        "birth": customer.birth.strftime("%Y-%m-%d") if customer.birth else "",
        "company_id": customer.company_id,
    }


def format_customer_for_detail(customer: Customer) -> dict:
    return {
        "id": customer.id,
        "name": customer.name,
        "phone": customer.cel or "",
        "cel": customer.cel or "",
        "email": customer.email or "",
        "notes": customer.notes or "",
        "birth": customer.birth.strftime("%Y-%m-%d") if customer.birth else "",
        "address": customer.address or "",
        "company_id": customer.company_id,
        "pipelinesCount": len(customer.pipelines) if customer.pipelines else 0,
    }


def parse_date(date_val):
    if not date_val:
        return None
    if isinstance(date_val, datetime):
        return date_val
    if isinstance(date_val, str):
        date_str = date_val.strip()
        if not date_str:
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(date_str[:19], fmt)
            except ValueError:
                continue
    return None


@customer_bp.route("", methods=["GET"])
def list_customers():
    """Retorna todos os clientes cadastrados com contagem de compras em andamento."""
    try:
        customers = Customer.query.order_by(Customer.id.desc()).all()
        return jsonify([format_customer_for_list(c) for c in customers]), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@customer_bp.route("/<int:customer_id>", methods=["GET"])
def get_customer(customer_id: int):
    """Retorna detalhes de um cliente por ID."""
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"success": False, "error": "Cliente não encontrado."}), 404
    return jsonify(format_customer_for_detail(customer)), 200


@customer_bp.route("", methods=["POST"])
def create_customer():
    """Cria um novo cliente a partir dos dados do formulário."""
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not name or str(name).strip() == "":
        return jsonify({"success": False, "error": "O campo 'name' é obrigatório."}), 400

    company_id = data.get("company_id")
    if not company_id:
        first_company = Company.query.first()
        company_id = first_company.id if first_company else 1

    birth_dt = parse_date(data.get("birth"))
    phone = data.get("phone") or data.get("cel") or None

    try:
        new_customer = Customer(
            name=str(name).strip(),
            notes=str(data.get("notes", "")).strip() if data.get("notes") else None,
            cel=str(phone).strip() if phone else None,
            email=str(data.get("email", "")).strip() if data.get("email") else None,
            birth=birth_dt,
            address=str(data.get("address", "")).strip() if data.get("address") else None,
            company_id=company_id,
        )
        db.session.add(new_customer)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Cliente cadastrado com sucesso.",
            "customer": format_customer_for_detail(new_customer),
        }), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 500


@customer_bp.route("/<int:customer_id>", methods=["PUT"])
def update_customer(customer_id: int):
    """Atualiza dados de um cliente existente."""
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"success": False, "error": "Cliente não encontrado."}), 404

    data = request.get_json(silent=True) or {}
    if "name" in data and str(data["name"]).strip():
        customer.name = str(data["name"]).strip()
    if "notes" in data:
        customer.notes = str(data["notes"]).strip() if data["notes"] else None
    if "phone" in data or "cel" in data:
        phone = data.get("phone") or data.get("cel")
        customer.cel = str(phone).strip() if phone else None
    if "email" in data:
        customer.email = str(data["email"]).strip() if data["email"] else None
    if "birth" in data:
        customer.birth = parse_date(data["birth"])
    if "address" in data:
        customer.address = str(data["address"]).strip() if data["address"] else None
    if "company_id" in data and data["company_id"]:
        try:
            customer.company_id = int(data["company_id"])
        except (ValueError, TypeError):
            pass

    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Cliente atualizado com sucesso.",
            "customer": format_customer_for_detail(customer),
        }), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 500


@customer_bp.route("/<int:customer_id>", methods=["DELETE"])
def delete_customer(customer_id: int):
    """Exclui um cliente por ID."""
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"success": False, "error": "Cliente não encontrado."}), 404

    try:
        db.session.delete(customer)
        db.session.commit()
        return jsonify({"success": True, "message": "Cliente excluído com sucesso."}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 500

