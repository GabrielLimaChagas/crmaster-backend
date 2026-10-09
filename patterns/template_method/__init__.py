"""Pacote contendo o padrão de projeto comportamental Template Method para importação de clientes.

Exporta as classes BaseCustomerImporter, CSVCustomerImporter e JSONCustomerImporter.
"""

from patterns.template_method.base_importer import BaseCustomerImporter
from patterns.template_method.csv_importer import CSVCustomerImporter
from patterns.template_method.json_importer import JSONCustomerImporter

__all__ = [
    "BaseCustomerImporter",
    "CSVCustomerImporter",
    "JSONCustomerImporter",
]
