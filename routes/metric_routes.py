"""Rotas da API para métricas, KPIs analíticos e dashboard."""

from flask import Blueprint, jsonify, request
from patterns.template_method import (
    AverageTicketCalculator,
    BaseMetricCalculator,
    LTVCalculator,
    WinRateCalculator,
)

metric_bp = Blueprint("metric_bp", __name__, url_prefix="/api/metrics")


@metric_bp.route("/dashboard", methods=["GET"])
def get_dashboard_metrics():
    """Retorna os principais KPIs analíticos do dashboard de vendas.

    Executa de forma polimórfica o Template Method em cada calculadora especializada:
    - Ticket Médio (AverageTicketCalculator)
    - Taxa de Conversão (WinRateCalculator)
    - Lifetime Value (LTVCalculator)

    Query Params:
        days: Quantidade de dias para a janela de análise (padrão: 30).
        company_id: ID opcional da empresa para isolamento multi-tenant.
    """
    days_raw = request.args.get("days", "30")
    company_id_raw = request.args.get("company_id")

    try:
        days = int(days_raw)
        if days <= 0:
            days = 30
    except ValueError:
        return jsonify({"success": False, "error": "'days' deve ser um número inteiro positivo."}), 400

    company_id: int | None = None
    if company_id_raw:
        try:
            company_id = int(company_id_raw)
        except ValueError:
            return jsonify({"success": False, "error": "'company_id' deve ser um número inteiro."}), 400

    # Polimorfismo com o Template Method: orquestra a lista de calculadoras
    calculators: list[BaseMetricCalculator] = [
        AverageTicketCalculator(),
        WinRateCalculator(),
        LTVCalculator(),
    ]

    try:
        metrics_results = [
            calc.compute_metric(days=days, company_id=company_id)
            for calc in calculators
        ]

        return jsonify({
            "success": True,
            "period_days": days,
            "company_id": company_id,
            "metrics": metrics_results,
        }), 200
    except Exception as exc:
        return jsonify({
            "success": False,
            "error": f"Erro ao calcular métricas do dashboard: {str(exc)}",
        }), 500
