from datetime import datetime
from flask import Blueprint, jsonify, request
from models.enums import PipelineStep
from models.pipeline import Pipeline
from models.sale_product import SaleProduct
from patterns.facade import SaleCheckoutFacade
from patterns.singleton.db_connection import DBConnection

db = DBConnection().db
pipeline_bp = Blueprint("pipeline_bp", __name__, url_prefix="/api/pipelines")


def parse_pipeline_date(date_val):
    if not date_val:
        return datetime.now()
    if isinstance(date_val, datetime):
        return date_val
    if isinstance(date_val, str):
        date_str = date_val.strip()
        if not date_str:
            return datetime.now()
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"):
            try:
                return datetime.strptime(date_str[:19], fmt)
            except ValueError:
                continue
    return datetime.now()


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
    """Lista todas as pipelines cadastradas, com suporte a filtro por step/status."""
    try:
        query = Pipeline.query
        step_param = request.args.get("step") or request.args.get("status")
        if step_param:
            steps_list = [s.strip().upper() for s in step_param.split(",") if s.strip()]
            valid_enums = [PipelineStep(s) for s in steps_list if s in PipelineStep.__members__]
            if valid_enums:
                query = query.filter(Pipeline.step.in_(valid_enums))

        pipelines = query.order_by(Pipeline.id.asc()).all()
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


@pipeline_bp.route("", methods=["POST"])
def create_pipeline():
    """Cria uma nova oportunidade/pipeline e associa produtos."""
    payload = request.get_json(silent=True) or {}
    customer_id = payload.get("customer_id")
    employee_id = payload.get("employee_id")
    step_str = payload.get("step", PipelineStep.PROPSECTING.value)
    note = payload.get("note") or payload.get("notes")
    date_val = parse_pipeline_date(payload.get("date"))
    products_data = payload.get("products") or []

    try:
        step_enum = PipelineStep(step_str) if step_str in PipelineStep.__members__ else PipelineStep.PROPSECTING
    except Exception:
        step_enum = PipelineStep.PROPSECTING

    try:
        new_pipeline = Pipeline(
            customer_id=customer_id if customer_id else None,
            employee_id=employee_id if employee_id else None,
            step=step_enum,
            note=note,
            date=date_val,
        )
        db.session.add(new_pipeline)
        db.session.flush()

        for item in products_data:
            p_id = item.get("product_id") or item.get("id")
            qty = int(item.get("quantidade", 1))
            if p_id:
                sp = SaleProduct(
                    sale_id=new_pipeline.id,
                    product_id=p_id,
                    quantidade=qty,
                )
                db.session.add(sp)

        db.session.commit()

        # Gatilho da Fachada de Fechamento se a etapa for CLOSING
        if step_enum == PipelineStep.CLOSING:
            try:
                facade = SaleCheckoutFacade()
                facade.close_sale(
                    pipeline_id=new_pipeline.id,
                    closing_note=note or "Fechamento realizado pela interface",
                )
            except Exception as fe:
                print(f"[Aviso] Falha ao disparar SaleCheckoutFacade no create: {fe}")

        return jsonify({
            "success": True,
            "message": "Pipeline criada com sucesso.",
            "pipeline": new_pipeline.to_dict(),
        }), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 500


@pipeline_bp.route("/<int:pipeline_id>", methods=["PUT"])
def update_pipeline(pipeline_id: int):
    """Atualiza dados e produtos de uma pipeline existente."""
    pipeline = Pipeline.query.get(pipeline_id)
    if not pipeline:
        return jsonify({"success": False, "error": "Pipeline não encontrada."}), 404

    payload = request.get_json(silent=True) or {}
    if "customer_id" in payload:
        pipeline.customer_id = payload["customer_id"] if payload["customer_id"] else None
    if "employee_id" in payload:
        pipeline.employee_id = payload["employee_id"] if payload["employee_id"] else None
    if "note" in payload or "notes" in payload:
        pipeline.note = payload.get("note") or payload.get("notes")
    if "date" in payload and payload["date"]:
        pipeline.date = parse_pipeline_date(payload["date"])

    step_changed_to_closing = False
    if "step" in payload and payload["step"]:
        step_str = payload["step"]
        try:
            new_step = PipelineStep(step_str) if step_str in PipelineStep.__members__ else pipeline.step
            if new_step == PipelineStep.CLOSING and pipeline.step != PipelineStep.CLOSING:
                step_changed_to_closing = True
            pipeline.step = new_step
        except Exception:
            pass

    # Atualiza lista de produtos se enviada
    if "products" in payload:
        products_data = payload["products"] or []
        # Remove produtos antigos
        SaleProduct.query.filter_by(sale_id=pipeline.id).delete()
        for item in products_data:
            p_id = item.get("product_id") or item.get("id")
            qty = int(item.get("quantidade", 1))
            if p_id:
                sp = SaleProduct(
                    sale_id=pipeline.id,
                    product_id=p_id,
                    quantidade=qty,
                )
                db.session.add(sp)

    try:
        db.session.commit()

        # Gatilho da Fachada de Fechamento se a etapa for ou passou a ser CLOSING
        if step_changed_to_closing or pipeline.step == PipelineStep.CLOSING:
            try:
                facade = SaleCheckoutFacade()
                facade.close_sale(
                    pipeline_id=pipeline.id,
                    closing_note=payload.get("note") or "Fechamento realizado pela interface",
                )
            except Exception as fe:
                print(f"[Aviso] Falha ao disparar SaleCheckoutFacade no update: {fe}")

        return jsonify({
            "success": True,
            "message": "Pipeline atualizada com sucesso.",
            "pipeline": pipeline.to_dict(),
        }), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 500


@pipeline_bp.route("/<int:pipeline_id>", methods=["DELETE"])
def delete_pipeline(pipeline_id: int):
    """Exclui uma pipeline por ID."""
    pipeline = Pipeline.query.get(pipeline_id)
    if not pipeline:
        return jsonify({"success": False, "error": "Pipeline não encontrada."}), 404

    try:
        db.session.delete(pipeline)
        db.session.commit()
        return jsonify({"success": True, "message": "Pipeline excluída com sucesso."}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 500
