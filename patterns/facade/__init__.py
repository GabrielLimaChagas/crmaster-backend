"""Pacote com a implementação do padrão estrutural Facade (GoF).

Exporta as 3 Fachadas e os 4 Subsistemas da arquitetura CRMaster:
Fachadas:
    - CompanyOnboardingFacade
    - SaleCheckoutFacade
    - MessageNotificationFacade

Subsistemas:
    - CompanyProvisioningService
    - PipelineService
    - NotificationRecordService
    - EmailService
"""

from .company_onboarding_facade import CompanyOnboardingFacade
from .company_provisioning_service import CompanyProvisioningService
from .email_service import EmailService
from .message_notification_facade import MessageNotificationFacade
from .notification_record_service import NotificationRecordService
from .pipeline_service import PipelineService
from .sale_checkout_facade import SaleCheckoutFacade

__all__ = [
    "CompanyOnboardingFacade",
    "SaleCheckoutFacade",
    "MessageNotificationFacade",
    "CompanyProvisioningService",
    "PipelineService",
    "NotificationRecordService",
    "EmailService",
]
