"""Rotas da API para gerenciamento de Produtos."""

from flask import Blueprint, jsonify, request
from models.product import Product
from patterns.singleton.db_connection import DBConnection

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
