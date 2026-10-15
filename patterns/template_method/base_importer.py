"""Módulo base para o padrão Template Method genérico de importação em lote.

Define a classe abstrata BaseImporter(ABC, Generic[T]) com o esqueleto invariante
do algoritmo e extração agnóstica de arquivos CSV e JSON.
"""

from abc import ABC, abstractmethod
import csv
import io
import json
from typing import Any, Generic, TypeVar

from patterns.singleton.db_connection import DBConnection

T = TypeVar("T")


class BaseImporter(ABC, Generic[T]):
    """Classe base abstrata genérica (Template Method) para importação em lote.

    Define os passos invariantes do ciclo de vida da importação e orquestra:
    1. Extração agnóstica de dados (_extract_data para CSV e JSON).
    2. Processamento e validação de domínio específica da entidade (process_records).
    3. Persistência atômica no banco de dados via SQLAlchemy (_save_to_database).
    4. Hook pós-importação (post_import_hook).
    """

    def __init__(self) -> None:
        """Inicializa o importador com a conexão ao banco e lista de erros vazia."""
        self.errors: list[dict[str, Any]] = []
        self.db = DBConnection().db

    def import_data(self, content: str | bytes, file_format: str) -> dict[str, Any]:
        """Template Method: Define a estrutura invariante do algoritmo de importação.

        Passos executados:
            1. raw_records = self._extract_data(content, file_format)
            2. validated_entities = self.process_records(raw_records)
            3. saved_count = self._save_to_database(validated_entities)
            4. self.post_import_hook(saved_count)
            5. Retorna relatório consolidado.

        Args:
            content: Conteúdo do arquivo ou payload em string ou bytes.
            file_format: Formato dos dados ('csv' ou 'json').

        Returns:
            dict contendo status, total lido, total importado, falhas e lista de erros.
        """
        if content is None:
            raise ValueError("O conteúdo para importação não pode ser nulo.")

        # Reinicia a lista de erros para a execução atual
        self.errors = []

        # 1. Extração dos registros brutos conforme o formato
        raw_records = self._extract_data(content, file_format)

        # 2. Processamento, validação e instanciação de entidades (Passo primitivo abstrato)
        validated_entities = self.process_records(raw_records)

        # 3. Persistência atômica no banco com controle transacional
        saved_count = self._save_to_database(validated_entities)

        # 4. Hook pós-importação opcional
        self.post_import_hook(saved_count)

        # 5. Consolidação e retorno do relatório
        return {
            "success": True,
            "total_read": len(raw_records),
            "imported_count": saved_count,
            "failed_count": len(self.errors),
            "errors": self.errors,
        }

    def _extract_data(self, content: str | bytes, file_format: str) -> list[dict[str, Any]]:
        """Extrai registros brutos de formatos suportados (CSV ou JSON).

        Args:
            content: Dados em texto ou bytes.
            file_format: 'csv' ou 'json'.

        Returns:
            Lista de dicionários brutos com chaves em minúsculas e sem espaços.
        """
        fmt = (file_format or "").lower().strip().lstrip(".")

        if fmt in ("csv", "text/csv"):
            return self._extract_csv(content)
        elif fmt in ("json", "application/json"):
            return self._extract_json(content)
        else:
            raise ValueError(
                f"Formato '{file_format}' não suportado. Utilize 'csv' ou 'json'."
            )

    def _extract_csv(self, content: str | bytes) -> list[dict[str, Any]]:
        """Extrai registros a partir de conteúdo CSV delimitado por vírgula ou ponto-e-vírgula."""
        decoded = self._decode_bytes(content).strip()
        if not decoded:
            return []

        # Detecta dinamicamente delimitador ';' ou ','
        first_line = decoded.splitlines()[0]
        delimiter = ";" if first_line.count(";") > first_line.count(",") else ","

        stream = io.StringIO(decoded)
        reader = csv.DictReader(stream, delimiter=delimiter)

        records: list[dict[str, Any]] = []
        for row in reader:
            if not row or all(v is None or not str(v).strip() for v in row.values()):
                continue

            normalized_row = {
                str(k).strip().lower(): v for k, v in row.items() if k is not None
            }
            records.append(normalized_row)

        return records

    def _extract_json(self, content: str | bytes) -> list[dict[str, Any]]:
        """Extrai registros a partir de arrays diretos ou envelopes JSON."""
        decoded = self._decode_bytes(content).strip()
        if not decoded:
            return []

        try:
            parsed = json.loads(decoded)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Conteúdo JSON inválido: {str(exc)}") from exc

        # Suporta envelopes comuns: {"data": [...]}, {"items": [...]}, {"customers": [...]}, etc.
        if isinstance(parsed, dict):
            for key in ("data", "items", "records", "customers", "products", "clientes", "produtos"):
                if key in parsed and isinstance(parsed[key], list):
                    parsed = parsed[key]
                    break
            else:
                # Caso seja um único objeto de entidade, encapsula em lista
                parsed = [parsed]

        if not isinstance(parsed, list):
            raise ValueError("O conteúdo JSON deve representar uma lista de objetos ou um envelope válido.")

        records: list[dict[str, Any]] = []
        for item in parsed:
            if isinstance(item, dict):
                normalized_item = {
                    str(k).strip().lower(): v for k, v in item.items() if k is not None
                }
                records.append(normalized_item)
            else:
                records.append(item)

        return records

    @staticmethod
    def _decode_bytes(content: str | bytes) -> str:
        """Decodifica bytes para string com suporte a UTF-8 (com ou sem BOM) e Latin-1."""
        if isinstance(content, str):
            return content
        try:
            return content.decode("utf-8-sig")
        except UnicodeDecodeError:
            return content.decode("latin-1")

    @abstractmethod
    def process_records(self, raw_records: list[dict[str, Any]]) -> list[T]:
        """Passo primitivo abstrato: valida dados brutos e instancia entidades de domínio T.

        Deve ser implementado pelas subclasses de entidade para aplicar as regras
        de validação e mapeamento específicas do modelo.

        Args:
            raw_records: Lista de dicionários extraídos do arquivo.

        Returns:
            Lista de instâncias da entidade T prontas para o banco.
        """
        raise NotImplementedError

    def _save_to_database(self, validated_entities: list[T]) -> int:
        """Persiste entidades validadas atomicamente via SQLAlchemy com rollback em falha.

        Args:
            validated_entities: Lista de entidades a serem persistidas.

        Returns:
            Quantidade total de registros persistidos com sucesso.
        """
        if not validated_entities:
            return 0

        try:
            self.db.session.add_all(validated_entities)
            self.db.session.commit()
            return len(validated_entities)
        except Exception as exc:
            self.db.session.rollback()
            self.errors.append({
                "row": None,
                "error": f"Falha na transação do banco de dados: {str(exc)}",
                "data": None,
            })
            raise

    def post_import_hook(self, saved_count: int) -> None:
        """Hook opcional executado após a persistência bem-sucedida. Padrão vazio."""
        pass
