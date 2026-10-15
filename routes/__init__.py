"""Pacote de rotas da aplicação."""
from routes.customer_routes import customer_bp
from routes.product_routes import product_bp

__all__ = ["customer_bp", "product_bp"]
