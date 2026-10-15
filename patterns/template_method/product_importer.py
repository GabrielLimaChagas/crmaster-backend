"""Módulo do importador concreto para a entidade Product.

Implementa ProductImporter especializado com validações de dados de produtos,
obrigatoriedade de nome e preço e sanitização de descrição.
"""

from typing import Any

from models.product import Product
from patterns.template_method.base_importer import BaseImporter


class ProductImporter(BaseImporter[Product]):
    """Importador concreto especializado para a entidade Product.

    Aplica validações de campos obrigatórios ('name' e 'price'), sanitização
    de descrições e conversão para o modelo de Produto.
    """

    KEY_ALIASES: dict[str, str] = {
        "name": "name",
        "nome": "name",
        "produto": "name",
        "nome_produto": "name",
        "title": "name",
        "price": "price",
        "preco": "price",
        "preço": "price",
        "valor": "price",
        "valor_unitario": "price",
        "description": "description",
        "descricao": "description",
        "descrição": "description",
        "detalhes": "description",
        "notes": "description",
        "obs": "description",
    }

    def process_records(self, raw_records: list[dict[str, Any]]) -> list[Product]:
        """Valida e converte registros brutos em instâncias de Product."""
        validated_products: list[Product] = []

        for index, raw_item in enumerate(raw_records, start=1):
            if not isinstance(raw_item, dict):
                self.errors.append({
                    "row": index,
                    "error": "Registro inválido: esperado objeto/dicionário.",
                    "data": raw_item,
                })
                continue

            # Mapeia chaves para o padrão do modelo
            record: dict[str, Any] = {}
            for k, v in raw_item.items():
                target_key = self.KEY_ALIASES.get(k, k)
                record[target_key] = v

            # 1. Validação de campo obrigatório: name
            raw_name = record.get("name")
            name = str(raw_name).strip() if raw_name is not None else ""
            if not name:
                self.errors.append({
                    "row": index,
                    "error": "Campo obrigatório 'name' ausente ou vazio.",
                    "data": raw_item,
                })
                continue

            # 2. Validação de campo obrigatório: price
            raw_price = record.get("price")
            if raw_price is None or str(raw_price).strip() == "":
                self.errors.append({
                    "row": index,
                    "error": "Campo obrigatório 'price' ausente ou vazio.",
                    "data": raw_item,
                })
                continue

            price_str = str(raw_price).strip()[:255]

            # 3. Sanitização de description (opcional)
            raw_desc = record.get("description")
            description: str | None = None
            if raw_desc is not None and str(raw_desc).strip():
                description = str(raw_desc).strip()[:255]

            # 4. Instanciação da entidade Product
            product = Product(
                name=name[:255],
                price=price_str,
                description=description,
            )
            validated_products.append(product)

        return validated_products
