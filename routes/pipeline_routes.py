"""Rotas da API para gerenciamento de Pipelines e Fechamento de Vendas via Facade."""

from flask import Blueprint, jsonify, request
from models.pipeline import Pipeline
from patterns.facade import SaleCheckoutFacade

pipeline_bp = Blueprint("pipeline_bp", __name__, url_prefix="/api/pipelines")


@pipeline_bp.route("/<int:pipeline_id>/close", methods=["POST"])
def close_pipeline_sale(pipeline_id: int):
    """Fecha uma oportunidade de venda utilizando o padrão Facade (SaleCheckoutFacade).

    Payload opcional (JSON):
        { "note": "Venda finalizada com sucesso" }

    Retorno:
        200: Venda fechada com sucesso {"success": True, "message": "..."}
        404: Pipeline não encontrada
        500: Erro interno / falha transacional
    """
    payload = request.get_json(silent=True) or {}
    closing_note = payload.get("note")

    facade = SaleCheckoutFacade()

    try:
        success = facade.close_sale(pipeline_id=pipeline_id, closing_note=closing_note)
        return jsonify({
            "success": success,
            "message": f"Venda da pipeline {pipeline_id} concluída com sucesso.",
            "pipeline_id": pipeline_id,
        }), 200
    except ValueError as ve:
        return jsonify({
            "success": False,
            "error": str(ve),
        }), 404
    except Exception as exc:
        return jsonify({
            "success": False,
            "error": f"Erro interno ao processar o fechamento da venda: {str(exc)}",
        }), 500


@pipeline_bp.route("", methods=["GET"])
def list_pipelines():
    """Lista todas as pipelines cadastradas."""
    try:
        pipelines = Pipeline.query.order_by(Pipeline.id.asc()).all()
        return jsonify([p.to_dict() for p in pipelines]), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@pipeline_bp.route("/<int:pipeline_id>", methods=["GET"])
def get_pipeline_detail(pipeline_id: int):
    """Retorna os dados detalhados de uma pipeline específica."""
    pipeline = Pipeline.query.get(pipeline_id)
    if not pipeline:
        return jsonify({"success": False, "error": "Pipeline não encontrada."}), 404
    return jsonify(pipeline.to_dict()), 200
