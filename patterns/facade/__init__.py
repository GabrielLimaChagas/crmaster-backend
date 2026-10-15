"""Pacote com a implementação do padrão estrutural Facade (GoF).

Exporta as fachadas e subsistemas de fechamento de vendas e onboarding de empresas.
"""

from .company_onboarding_facade import CompanyOnboardingFacade
from .company_provisioning_service import CompanyProvisioningService
from .email_service import EmailService
from .pipeline_service import PipelineService
from .sale_checkout_facade import SaleCheckoutFacade

__all__ = [
    "SaleCheckoutFacade",
    "PipelineService",
    "EmailService",
    "CompanyOnboardingFacade",
    "CompanyProvisioningService",
]
