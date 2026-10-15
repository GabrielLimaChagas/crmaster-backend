"""Pacote de rotas da aplicação."""
from routes.company_routes import company_bp
from routes.customer_routes import customer_bp
from routes.metric_routes import metric_bp
from routes.notification_routes import notification_bp
from routes.pipeline_routes import pipeline_bp
from routes.product_routes import product_bp
from routes.user_routes import user_bp
from routes.plugin_routes import plugin_bp
from routes.auth_routes import auth_bp

__all__ = [
    "company_bp",
    "customer_bp",
    "product_bp",
    "metric_bp",
    "pipeline_bp",
    "notification_bp",
    "user_bp",
    "plugin_bp",
    "auth_bp",
]

