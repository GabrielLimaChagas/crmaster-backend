"""Módulo com a especialização concreta do importador de clientes para formato JSON.

Implementa JSONCustomerImporter que extrai dados a partir de arrays ou estruturas JSON.
"""

import json
from typing import Any

from patterns.template_method.base_importer import BaseCustomerImporter


class JSONCustomerImporter(BaseCustomerImporter):
    """Importador concreto para arquivos JSON contendo registros de clientes.

    Sobrescreve o passo abstrato `extract_data` para converter payloads JSON em
    listas de dicionários de clientes para validação pelo Template Method.
    """

    # Mapeamento para normalizar variações de chaves nos objetos JSON
    KEY_MAPPING: dict[str, str] = {
        "name": "name",
        "nome": "name",
        "nome_cliente": "name",
        "email": "email",
        "e-mail": "email",
        "mail": "email",
        "cel": "cel",
        "celular": "cel",
        "telefone": "cel",
        "phone": "cel",
        "address": "address",
        "endereco": "address",
        "endereço": "address",
        "birth": "birth",
        "data_nascimento": "birth",
        "nascimento": "birth",
        "aniversario": "birth",
        "notes": "notes",
        "observacoes": "notes",
        "observações": "notes",
        "obs": "notes",
        "notas": "notes",
    }

    def extract_data(self, file_data: str | bytes) -> list[dict[str, Any]]:
        """Extrai registros brutos a partir de dados em formato JSON.

        Args:
            file_data: Conteúdo do arquivo ou payload JSON em string ou bytes.

        Returns:
            Lista de dicionários brutos com as chaves normalizadas.

        Raises:
            ValueError: Se o conteúdo não for um JSON válido ou não contiver uma lista de clientes.
        """
        content_str = self._decode_file_data(file_data)
        content_str = content_str.strip()

        if not content_str:
            return []

        try:
            parsed = json.loads(content_str)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Conteúdo JSON inválido: {str(exc)}") from exc

        # Suporta tanto uma lista direta [ {...}, {...} ] quanto um envelope {"customers": [...]}
        if isinstance(parsed, dict):
            for key in ("customers", "clientes", "data", "records", "items"):
                if key in parsed and isinstance(parsed[key], list):
                    parsed = parsed[key]
                    break
            else:
                # Se for um único cliente em forma de dicionário, encapsula em lista
                if "name" in parsed or "nome" in parsed:
                    parsed = [parsed]
                else:
                    raise ValueError(
                        "Estrutura JSON inválida: esperada uma lista de clientes ou um objeto com a chave 'customers'."
                    )

        if not isinstance(parsed, list):
            raise ValueError("O conteúdo JSON deve representar uma lista de objetos de clientes.")

        extracted_records: list[dict[str, Any]] = []

        for item in parsed:
            if not isinstance(item, dict):
                # Se houver item não dicionário, inclui bruto para o process_records acusar erro
                extracted_records.append(item)
                continue

            normalized_item: dict[str, Any] = {}
            for key, value in item.items():
                clean_key = str(key).strip().lower()
                target_key = self.KEY_MAPPING.get(clean_key, clean_key)
                normalized_item[target_key] = value

            extracted_records.append(normalized_item)

        return extracted_records

    @staticmethod
    def _decode_file_data(file_data: str | bytes) -> str:
        """Converte bytes para string com suporte a UTF-8 e Latin-1."""
        if isinstance(file_data, str):
            return file_data

        try:
            return file_data.decode("utf-8")
        except UnicodeDecodeError:
            return file_data.decode("latin-1")
