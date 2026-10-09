"""Módulo com a especialização concreta do importador de clientes para formato CSV.

Implementa CSVCustomerImporter que extrai dados delimitados por vírgula ou ponto-e-vírgula.
"""

import csv
import io
from typing import Any

from patterns.template_method.base_importer import BaseCustomerImporter


class CSVCustomerImporter(BaseCustomerImporter):
    """Importador concreto para arquivos CSV contendo registros de clientes.

    Sobrescreve o passo abstrato `extract_data` para interpretar conteúdo CSV,
    suportando separadores por vírgula (,) e ponto-e-vírgula (;) e cabeçalhos em
    inglês ou português.
    """

    # Mapeamento para normalizar variações de cabeçalhos
    HEADER_MAPPING: dict[str, str] = {
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
        """Extrai registros brutos a partir de dados em formato CSV.

        Args:
            file_data: Conteúdo do arquivo CSV em formato string ou bytes.

        Returns:
            Lista de dicionários brutos com as chaves normalizadas.
        """
        content_str = self._decode_file_data(file_data)
        content_str = content_str.strip()

        if not content_str:
            return []

        delimiter = self._detect_delimiter(content_str)
        stream = io.StringIO(content_str)
        reader = csv.DictReader(stream, delimiter=delimiter)

        extracted_records: list[dict[str, Any]] = []

        for row in reader:
            # Ignora linhas totalmente vazias
            if not row or all(v is None or not str(v).strip() for v in row.values()):
                continue

            normalized_row: dict[str, Any] = {}
            for col_name, col_value in row.items():
                if col_name is None:
                    continue
                clean_key = col_name.strip().lower()
                target_key = self.HEADER_MAPPING.get(clean_key, clean_key)
                normalized_row[target_key] = col_value

            extracted_records.append(normalized_row)

        return extracted_records

    @staticmethod
    def _decode_file_data(file_data: str | bytes) -> str:
        """Converte bytes para string suportando UTF-8, UTF-8 com BOM e Latin-1."""
        if isinstance(file_data, str):
            return file_data

        # Suporta UTF-8 com ou sem BOM
        try:
            return file_data.decode("utf-8-sig")
        except UnicodeDecodeError:
            # Fallback para codificação compatível com Excel Windows brasileiro
            return file_data.decode("latin-1")

    @staticmethod
    def _detect_delimiter(content: str) -> str:
        """Identifica dinamicamente se o delimitador é ';' ou ','."""
        first_line = content.splitlines()[0] if content else ""
        semicolon_count = first_line.count(";")
        comma_count = first_line.count(",")

        if semicolon_count > comma_count:
            return ";"
        return ","
