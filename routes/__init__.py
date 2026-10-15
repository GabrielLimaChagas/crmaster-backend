"""Pacote de rotas da aplicação."""
from routes.customer_routes import customer_bp
from routes.metric_routes import metric_bp
from routes.pipeline_routes import pipeline_bp
from routes.product_routes import product_bp

__all__ = ["customer_bp", "product_bp", "metric_bp", "pipeline_bp"]
