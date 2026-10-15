"""Módulo do exportador concreto para a entidade Product.

Implementa ProductExporter para consulta e formatação dos produtos em CSV e JSON.
"""

from typing import Any

from models.product import Product
from patterns.template_method.base_exporter import BaseExporter


class ProductExporter(BaseExporter[Product]):
    """Exportador concreto especializado para a entidade Product.

    Formata os dados com colunas id, nome, preco e descricao para exportação.
    """

    filename_prefix: str = "produtos"

    def query_data(self) -> list[Product]:
        """Consulta todos os produtos ordenados por ID crescente."""
        return Product.query.order_by(Product.id.asc()).all()

    def format_records(self, records: list[Product]) -> list[dict[str, Any]]:
        """Converte as entidades Product em dicionários formatados."""
        formatted: list[dict[str, Any]] = []
        for p in records:
            formatted.append({
                "id": p.id,
                "nome": p.name,
                "preco": p.price,
                "descricao": p.description or "",
            })
        return formatted
