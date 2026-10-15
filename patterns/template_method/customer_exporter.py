"""Módulo do exportador concreto para a entidade Customer.

Implementa CustomerExporter para consulta e formatação dos clientes em CSV e JSON.
"""

from typing import Any

from models.customer import Customer
from patterns.template_method.base_exporter import BaseExporter


class CustomerExporter(BaseExporter[Customer]):
    """Exportador concreto especializado para a entidade Customer.

    Permite filtrar por empresa e formata os dados com colunas em português amigáveis.
    """

    filename_prefix: str = "clientes"

    def __init__(self, company_id: int | None = None) -> None:
        """Inicializa o exportador de clientes.

        Args:
            company_id: ID opcional da empresa para filtragem.
        """
        super().__init__()
        self.company_id: int | None = company_id

    def query_data(self) -> list[Customer]:
        """Consulta os clientes no banco de dados ordenados por ID crescente."""
        query = Customer.query
        if self.company_id is not None:
            query = query.filter_by(company_id=self.company_id)
        return query.order_by(Customer.id.asc()).all()

    def format_records(self, records: list[Customer]) -> list[dict[str, Any]]:
        """Converte as entidades Customer em dicionários formatados."""
        formatted: list[dict[str, Any]] = []
        for c in records:
            birth_str = c.birth.strftime("%Y-%m-%d") if c.birth else ""
            formatted.append({
                "id": c.id,
                "nome": c.name,
                "celular": c.cel or "",
                "email": c.email or "",
                "nascimento": birth_str,
                "endereco": c.address or "",
                "observacoes": c.notes or "",
            })
        return formatted
