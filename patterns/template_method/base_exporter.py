"""Módulo base para o padrão Template Method de exportação de dados.

Define a classe abstrata BaseExporter(ABC, Generic[T]) com o esqueleto invariante
do algoritmo de exportação e serialização para CSV e JSON.
"""

from abc import ABC, abstractmethod
import csv
from datetime import datetime
import io
import json
from typing import Any, Generic, TypeVar

from patterns.singleton.db_connection import DBConnection

T = TypeVar("T")


class BaseExporter(ABC, Generic[T]):
    """Classe base abstrata genérica (Template Method) para exportação de dados.

    Orquestra a sequência invariante de passos:
    1. Consulta os dados no banco (query_data).
    2. Converte as entidades em dicionários estruturados com colunas amigáveis (format_records).
    3. Serializa para o formato requisitado: CSV (delimitado por ';', UTF-8-SIG) ou JSON (_serialize_data).
    4. Dispara o hook pós-exportação (post_export_hook).
    5. Retorna o conteúdo, tipo MIME e nome do arquivo sugerido.
    """

    filename_prefix: str = "export"

    def __init__(self) -> None:
        """Inicializa o exportador com a conexão ao banco."""
        self.db = DBConnection().db

    def export_data(self, file_format: str = "csv") -> tuple[bytes | str, str, str]:
        """Template Method: Define a sequência invariante de exportação.

        Passos executados:
            1. records = self.query_data()
            2. formatted_records = self.format_records(records)
            3. content, mimetype = self._serialize_data(formatted_records, file_format)
            4. self.post_export_hook(len(records))
            5. Retorna (content, mimetype, filename)

        Args:
            file_format: Formato desejado ('csv' ou 'json'). Padrão: 'csv'.

        Returns:
            Tupla contendo (conteúdo serializado, mimetype, nome do arquivo).

        Raises:
            ValueError: Se o formato informado não for suportado.
        """
        fmt = (file_format or "csv").lower().strip().lstrip(".")
        if fmt not in ("csv", "json"):
            raise ValueError(f"Formato '{file_format}' não suportado. Formatos aceitos: 'csv' e 'json'.")

        # 1. Consulta dos registros no banco de dados
        records = self.query_data()

        # 2. Formatação dos registros (Passo primitivo abstrato)
        formatted_records = self.format_records(records)

        # 3. Serialização conforme o formato solicitado
        content, mimetype = self._serialize_data(formatted_records, fmt)

        # 4. Hook opcional pós-exportação
        self.post_export_hook(len(records))

        # 5. Geração do nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.filename_prefix}_{timestamp}.{fmt}"

        return content, mimetype, filename

    @abstractmethod
    def query_data(self) -> list[T]:
        """Passo primitivo: executa a consulta ao banco de dados para obter as entidades."""
        raise NotImplementedError

    @abstractmethod
    def format_records(self, records: list[T]) -> list[dict[str, Any]]:
        """Passo primitivo abstrato: converte a lista de entidades em dicionários amigáveis.

        Args:
            records: Lista de entidades obtidas no banco.

        Returns:
            Lista de dicionários formatados prontos para exportação.
        """
        raise NotImplementedError

    def _serialize_data(
        self, formatted_records: list[dict[str, Any]], file_format: str
    ) -> tuple[bytes | str, str]:
        """Serializa a lista de dicionários no formato requisitado (CSV ou JSON)."""
        if file_format == "csv":
            content_bytes = self._serialize_csv(formatted_records)
            return content_bytes, "text/csv; charset=utf-8"
        elif file_format == "json":
            content_str = self._serialize_json(formatted_records)
            return content_str, "application/json; charset=utf-8"
        else:
            raise ValueError(f"Formato '{file_format}' não suportado.")

    def _serialize_csv(self, formatted_records: list[dict[str, Any]]) -> bytes:
        """Serializa em formato CSV delimitado por ';' com encoding UTF-8-SIG (BOM para Excel)."""
        output = io.StringIO()

        if formatted_records:
            fieldnames = list(formatted_records[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=";", extrasaction="ignore")
            writer.writeheader()
            for record in formatted_records:
                writer.writerow(record)
        else:
            # Caso não haja registros, gera arquivo vazio
            output.write("")

        return output.getvalue().encode("utf-8-sig")

    def _serialize_json(self, formatted_records: list[dict[str, Any]]) -> str:
        """Serializa em formato JSON legível (indent=2) com caracteres Unicode preservados."""
        return json.dumps(formatted_records, ensure_ascii=False, indent=2)

    def post_export_hook(self, record_count: int) -> None:
        """Hook opcional executado após a formatação e serialização. Padrão vazio."""
        pass
