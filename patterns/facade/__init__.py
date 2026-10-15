"""Pacote com a implementação do padrão estrutural Facade (GoF).

Exporta SaleCheckoutFacade, PipelineService e EmailService.
"""

from .email_service import EmailService
from .pipeline_service import PipelineService
from .sale_checkout_facade import SaleCheckoutFacade

__all__ = ["SaleCheckoutFacade", "PipelineService", "EmailService"]
