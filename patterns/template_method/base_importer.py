"""Módulo base para o padrão Template Method de importação de clientes.

Define a classe abstrata BaseCustomerImporter com o esqueleto do algoritmo
de extração, validação, persistência com controle transacional e hook pós-importação.
"""

from abc import ABC, abstractmethod
from datetime import date, datetime
import os
from typing import Any

from models.customer import Customer
from patterns.singleton.db_connection import DBConnection


class BaseCustomerImporter(ABC):
    """Classe base abstrata (Template Method) para importação em lote de clientes.

    Define os passos invariantes do ciclo de vida de importação e delega a extração
    dos dados brutos às subclasses especializadas (CSV, JSON, etc.).
    """

    def __init__(
        self,
        company_id: int,
        file_path_or_content: str | bytes | None = None,
    ) -> None:
        """Inicializa o importador de clientes.

        Args:
            company_id: Identificador da empresa à qual os clientes serão associados.
            file_path_or_content: Opcional, conteúdo bruto ou caminho do arquivo no disco.
        """
        self.company_id: int = company_id
        self.file_path_or_content: str | bytes | None = file_path_or_content
        self.errors: list[dict[str, Any]] = []
        self.db = DBConnection().db

    def import_customers(self, file_data: str | bytes | None = None) -> dict[str, Any]:
        """Template Method: Define a estrutura invariante do algoritmo de importação.

        Passos executados:
            1. raw_records = self.extract_data(file_data) (Passo abstrato/hook)
            2. validated_customers = self.process_records(raw_records) (Passo concreto reutilizável)
            3. saved_count = self.save_to_database(validated_customers) (Passo concreto com transação)
            4. self.post_import_hook(saved_count) (Hook opcional, default vazio)
            5. Retorna o relatório final consolidado.

        Args:
            file_data: Conteúdo do arquivo em string ou bytes (opcional se fornecido no construtor).

        Returns:
            dict contendo status de sucesso, contagem de registros e lista de erros.
        """
        data_to_process = file_data if file_data is not None else self.file_path_or_content
        if data_to_process is None:
            raise ValueError("Nenhum dado ou caminho de arquivo foi fornecido para importação.")

        # Se for um caminho de arquivo em disco, lê o conteúdo
        if isinstance(data_to_process, str) and os.path.isfile(data_to_process):
            with open(data_to_process, "rb") as f:
                data_to_process = f.read()

        # Reinicia a lista de erros para a execução atual
        self.errors = []

        # 1. Extração dos registros brutos (Passo primitivo / abstrato delegado à subclasse)
        raw_records = self.extract_data(data_to_process)

        # 2. Processamento, sanitização e validação dos registros (Passo concreto)
        validated_customers = self.process_records(raw_records)

        # 3. Persistência transacional no banco de dados via SQLAlchemy (Passo concreto)
        saved_count = self.save_to_database(validated_customers)

        # 4. Hook pós-importação opcional (pode ser sobrescrito por subclasses)
        self.post_import_hook(saved_count)

        # 5. Consolidação e retorno do relatório de importação
        return {
            "success": True,
            "company_id": self.company_id,
            "total_read": len(raw_records),
            "imported_count": saved_count,
            "failed_count": len(self.errors),
            "errors": self.errors,
        }

    @abstractmethod
    def extract_data(self, file_data: str | bytes) -> list[dict[str, Any]]:
        """Passo primitivo abstrato: extrai os dados brutos do arquivo.

        Deve ser implementado pelas subclasses para interpretar formatos específicos
        como CSV, JSON, XML, etc.

        Args:
            file_data: Conteúdo bruto do arquivo em formato string ou bytes.

        Returns:
            Lista de dicionários contendo os registros extraídos.
        """
        raise NotImplementedError

    def process_records(self, raw_records: list[dict[str, Any]]) -> list[Customer]:
        """Passo concreto reutilizável: valida e converte registros brutos em entidades Customer.

        Realiza parsing de datas em múltiplos formatos comuns, valida campos obrigatórios,
        limpa caracteres e descarta linhas inválidas acumulando os erros correspondentes.

        Args:
            raw_records: Lista de dicionários extraídos do arquivo.

        Returns:
            Lista de instâncias validadas de Customer prontas para persistência.
        """
        validated_customers: list[Customer] = []

        for index, record in enumerate(raw_records, start=1):
            if not isinstance(record, dict):
                self.errors.append({
                    "row": index,
                    "error": "Registro inválido: formato de objeto/dicionário esperado.",
                    "data": record,
                })
                continue

            # Validação do campo obrigatório: name
            raw_name = record.get("name")
            name = str(raw_name).strip() if raw_name is not None else ""
            if not name:
                self.errors.append({
                    "row": index,
                    "error": "Campo obrigatório 'name' ausente ou vazio.",
                    "data": record,
                })
                continue

            # Parsing e validação da data de nascimento (birth)
            raw_birth = record.get("birth")
            parsed_birth: datetime | None = None

            if raw_birth is not None and str(raw_birth).strip():
                try:
                    parsed_birth = self._parse_birth_date(raw_birth)
                except ValueError as ve:
                    self.errors.append({
                        "row": index,
                        "error": f"Data de nascimento inválida ('{raw_birth}'): {str(ve)}",
                        "data": record,
                    })
                    continue

            # Sanitização e limitação de tamanho dos campos opcionais
            notes = self._sanitize_string(record.get("notes"), max_length=255)
            cel = self._sanitize_string(record.get("cel"), max_length=64)
            email = self._sanitize_string(record.get("email"), max_length=64)
            address = self._sanitize_string(record.get("address"), max_length=64)

            # Instanciação do modelo Customer vinculado à empresa
            customer = Customer(
                name=name[:255],
                notes=notes,
                cel=cel,
                email=email,
                birth=parsed_birth,
                address=address,
                company_id=self.company_id,
            )
            validated_customers.append(customer)

        return validated_customers

    def save_to_database(self, validated_customers: list[Customer]) -> int:
        """Passo concreto: persiste os clientes validados no banco via SQLAlchemy.

        Executa atomicamente `db.session.add_all()` e `db.session.commit()`.
        Em caso de falha, garante o rollback da transação e registra o erro.

        Args:
            validated_customers: Lista de entidades Customer a serem persistidas.

        Returns:
            Quantidade de registros persistidos com sucesso.
        """
        if not validated_customers:
            return 0

        try:
            self.db.session.add_all(validated_customers)
            self.db.session.commit()
            return len(validated_customers)
        except Exception as exc:
            self.db.session.rollback()
            self.errors.append({
                "row": None,
                "error": f"Falha na transação do banco de dados: {str(exc)}",
                "data": None,
            })
            raise

    def post_import_hook(self, saved_count: int) -> None:
        """Hook opcional executado após a persistência bem-sucedida.

        Pode ser sobrescrito por subclasses para envio de e-mails, emissão de eventos,
        auditoria ou logs operacionais. Padrão vazio.

        Args:
            saved_count: Total de registros salvos no banco.
        """
        pass

    @staticmethod
    def _sanitize_string(value: Any, max_length: int) -> str | None:
        """Auxiliar para limpar strings, remover espaços e truncar se necessário."""
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        return text[:max_length]

    @staticmethod
    def _parse_birth_date(value: Any) -> datetime:
        """Converte diferentes formatos de data e strings em objeto datetime."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())

        text = str(value).strip()
        if not text:
            raise ValueError("Valor de data vazio.")

        # Tenta formatos ISO e convencionais
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            pass

        date_formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue

        raise ValueError(f"Formato não reconhecido para '{text}'. Formatos aceitos: ISO, YYYY-MM-DD, DD/MM/YYYY, etc.")
