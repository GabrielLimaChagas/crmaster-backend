"""Rotas da API para gerenciamento de Produtos."""

import json
from flask import Blueprint, jsonify, request, Response
from models.product import Product
from patterns.singleton.db_connection import DBConnection
from patterns.template_method import ProductImporter, ProductExporter

db = DBConnection().db
product_bp = Blueprint("product_bp", __name__, url_prefix="/api/products")


def format_product_for_list(product: Product) -> dict:
    """Formata o produto para a listagem na tabela."""
    numeric_price = product.get_numeric_price()
    # Para o formatCentAsReal do front (valor em centavos, ex: 1499.00 -> 149900):
    cents = int(round(numeric_price * 100))
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description or "",
        "price": cents,
        "raw_price": product.price,
        "numeric_price": numeric_price,
    }


def format_product_for_detail(product: Product) -> dict:
    """Formata o produto para o formulário de visualização/edição."""
    numeric_price = product.get_numeric_price()
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description or "",
        "price": str(product.price) if product.price is not None else "",
        "numeric_price": numeric_price,
    }


@product_bp.route("", methods=["GET"])
def list_products():
    """Retorna a lista de produtos cadastrados."""
    try:
        products = Product.query.order_by(Product.id.desc()).all()
        return jsonify([format_product_for_list(p) for p in products]), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@product_bp.route("/<int:product_id>", methods=["GET"])
def get_product(product_id: int):
    """Retorna os dados de um produto específico por ID."""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"success": False, "error": "Produto não encontrado."}), 404
    return jsonify(format_product_for_detail(product)), 200


@product_bp.route("", methods=["POST"])
def create_product():
    """Cria um novo produto."""
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    price = data.get("price")
    description = data.get("description", "")

    if not name or str(name).strip() == "":
        return jsonify({"success": False, "error": "O campo 'name' é obrigatório."}), 400

    if price is None or str(price).strip() == "":
        return jsonify({"success": False, "error": "O campo 'price' é obrigatório."}), 400

    try:
        new_product = Product(
            name=str(name).strip(),
            price=str(price).strip(),
            description=str(description).strip() if description else None,
        )
        db.session.add(new_product)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Produto criado com sucesso.",
            "product": format_product_for_list(new_product),
        }), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 500


@product_bp.route("/<int:product_id>", methods=["PUT"])
def update_product(product_id: int):
    """Atualiza um produto existente."""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"success": False, "error": "Produto não encontrado."}), 404

    data = request.get_json(silent=True) or {}
    if "name" in data and str(data["name"]).strip():
        product.name = str(data["name"]).strip()
    if "price" in data and str(data["price"]).strip():
        product.price = str(data["price"]).strip()
    if "description" in data:
        product.description = str(data["description"]).strip() if data["description"] else None

    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Produto atualizado com sucesso.",
            "product": format_product_for_list(product),
        }), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 500


@product_bp.route("/<int:product_id>", methods=["DELETE"])
def delete_product(product_id: int):
    """Exclui um produto por ID."""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"success": False, "error": "Produto não encontrado."}), 404

    try:
        db.session.delete(product)
        db.session.commit()
        return jsonify({"success": True, "message": "Produto excluído com sucesso."}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 500


@product_bp.route("/import", methods=["POST"])
def import_products_endpoint():
    """Endpoint unificado para importação em lote de produtos via CSV ou JSON.

    Aceita upload de arquivo multipart/form-data ('file') ou payload JSON direto
    ('data' e 'format').
    """
    file_bytes: bytes | None = None
    file_format: str | None = None

    # Caso 1: Upload multipart
    if "file" in request.files:
        uploaded_file = request.files["file"]
        filename = uploaded_file.filename or ""
        file_bytes = uploaded_file.read()

        if filename.lower().endswith(".csv"):
            file_format = "csv"
        elif filename.lower().endswith(".json"):
            file_format = "json"
        else:
            file_format = request.form.get("format", "").lower()

    # Caso 2: Payload JSON
    elif request.is_json:
        payload = request.get_json(silent=True) or {}
        file_format = payload.get("format", "json").lower()
        raw_data = payload.get("data") or payload.get("content")

        if raw_data is None:
            # Caso o payload seja diretamente uma lista [ {...}, {...} ]
            if isinstance(payload, list):
                raw_data = payload
            else:
                return jsonify({
                    "success": False,
                    "error": "Envie uma lista de produtos ou um objeto contendo 'data'.",
                }), 400

        if isinstance(raw_data, (list, dict)):
            file_bytes = json.dumps(raw_data).encode("utf-8")
        elif isinstance(raw_data, str):
            file_bytes = raw_data.encode("utf-8")

    else:
        return jsonify({
            "success": False,
            "error": "Envie um arquivo via multipart ('file') ou um JSON com 'data' de produtos.",
        }), 400

    if not file_bytes:
        return jsonify({"success": False, "error": "Conteúdo do arquivo vazio ou não informado."}), 400

    if file_format not in ("csv", "json"):
        return jsonify({
            "success": False,
            "error": f"Formato '{file_format}' não suportado. Formatos aceitos: 'csv' e 'json'.",
        }), 400

    try:
        importer = ProductImporter()
        report = importer.import_data(file_bytes, file_format)
        return jsonify(report), 200
    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as exc:
        return jsonify({
            "success": False,
            "error": f"Erro interno ao processar a importação: {str(exc)}",
        }), 500


@product_bp.route("/export", methods=["GET"])
def export_products_endpoint():
    """Endpoint para exportação de produtos nos formatos CSV ou JSON."""
    file_format = request.args.get("format", "csv")
    try:
        exporter = ProductExporter()
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
        return jsonify({"success": False, "error": f"Erro na exportação de produtos: {str(exc)}"}), 500


