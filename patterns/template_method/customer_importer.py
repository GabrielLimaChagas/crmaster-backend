"""Módulo do importador concreto para a entidade Customer.

Implementa CustomerImporter especializado com validações de dados de clientes,
parsing flexível de datas e associação com a empresa.
"""

from datetime import date, datetime
from typing import Any

from models.customer import Customer
from patterns.template_method.base_importer import BaseImporter


class CustomerImporter(BaseImporter[Customer]):
    """Importador concreto especializado para a entidade Customer.

    Aplica validações de campos obrigatórios, parsing flexível de datas de nascimento,
    sanitização de limites de tamanho e associação à empresa informada.
    """

    KEY_ALIASES: dict[str, str] = {
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
        "fone": "cel",
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

    def __init__(self, company_id: int) -> None:
        """Inicializa o importador de clientes para uma empresa específica.

        Args:
            company_id: ID da empresa associada aos clientes importados.
        """
        super().__init__()
        self.company_id: int = company_id

    def process_records(self, raw_records: list[dict[str, Any]]) -> list[Customer]:
        """Valida e converte registros brutos em instâncias de Customer."""
        validated_customers: list[Customer] = []

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

            # 2. Parsing de birth (data de nascimento)
            raw_birth = record.get("birth")
            parsed_birth: datetime | None = None
            if raw_birth is not None and str(raw_birth).strip():
                try:
                    parsed_birth = self._parse_birth_date(raw_birth)
                except ValueError as ve:
                    self.errors.append({
                        "row": index,
                        "error": f"Data de nascimento inválida ('{raw_birth}'): {str(ve)}",
                        "data": raw_item,
                    })
                    continue

            # 3. Sanitização de campos opcionais
            notes = self._sanitize_string(record.get("notes"), max_length=255)
            cel = self._sanitize_string(record.get("cel"), max_length=64)
            email = self._sanitize_string(record.get("email"), max_length=64)
            address = self._sanitize_string(record.get("address"), max_length=64)

            # 4. Instanciação do modelo Customer
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

    @staticmethod
    def _sanitize_string(value: Any, max_length: int) -> str | None:
        """Limpa espaços e trunca ao comprimento máximo."""
        if value is None:
            return None
        text = str(value).strip()
        return text[:max_length] if text else None

    @staticmethod
    def _parse_birth_date(value: Any) -> datetime:
        """Converte strings e objetos date em datetime suportando múltiplos formatos."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())

        text = str(value).strip()
        if not text:
            raise ValueError("Valor de data vazio.")

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

        raise ValueError("Formato não reconhecido. Formatos suportados: ISO, YYYY-MM-DD, DD/MM/YYYY.")
