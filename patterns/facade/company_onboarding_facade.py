"""Fachada de Onboarding e Cadastro de Novas Empresas (GoF Facade Pattern).

Orquestra atomicamente a validação, o provisionamento de Empresa, Plugins e Usuário
Administrador, a persistência transacional e o disparo do e-mail de boas-vindas.
"""

from typing import Any
from models.user import User
from patterns.facade.company_provisioning_service import CompanyProvisioningService
from patterns.facade.email_service import EmailService
from patterns.singleton.db_connection import DBConnection


class CompanyOnboardingFacade:
    """Fachada de alto nível para o fluxo de Onboarding de novas empresas.

    Simplifica para os controladores e clientes a complexidade de cadastrar a empresa,
    associar plugins selecionados, criar o usuário administrador com perfil COMPANY,
    garantir a atomicidade no banco de dados e notificar o usuário com suas credenciais.
    """

    def __init__(self) -> None:
        """Inicializa a fachada com a conexão do banco e o serviço de provisionamento."""
        self.db = DBConnection().db
        self.provisioning_service = CompanyProvisioningService(self.db.session)

    def register_company(
        self,
        company_name: str,
        cnpj: str,
        user_name: str,
        user_email: str,
        password: str,
        plugin_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """Cadastra e inicializa uma nova empresa completa no ecossistema CRMaster.

        Args:
            company_name: Razão social ou nome fantasia da empresa.
            cnpj: Documento CNPJ da empresa.
            user_name: Nome completo do usuário administrador.
            user_email: E-mail do usuário para acesso.
            password: Senha inicial para o usuário.
            plugin_ids: Lista de IDs dos plugins a serem liberados.

        Returns:
            dict contendo resumo da empresa criada, usuário e plugins ativos.

        Raises:
            ValueError: Se campos obrigatórios estiverem ausentes ou o e-mail já existir.
            Exception: Se houver falha na persistência com rollback.
        """
        # 1. Validação de preenchimento dos campos obrigatórios
        required_fields = {
            "company_name": company_name,
            "cnpj": cnpj,
            "user_name": user_name,
            "user_email": user_email,
            "password": password,
        }
        for field, val in required_fields.items():
            if not val or not str(val).strip():
                raise ValueError(f"O campo '{field}' é obrigatório e não pode ser vazio.")

        clean_email = str(user_email).strip().lower()
        clean_company_name = str(company_name).strip()
        clean_cnpj = str(cnpj).strip()
        clean_user_name = str(user_name).strip()
        clean_password = str(password).strip()

        # Validação de unicidade do e-mail do usuário
        existing_user = User.query.filter_by(email=clean_email).first()
        if existing_user:
            raise ValueError(f"O e-mail '{clean_email}' já está em uso por outro usuário.")

        # 2. Executa o provisionamento através do subsistema CompanyProvisioningService
        company_data = {"name": clean_company_name, "cnpj": clean_cnpj}
        user_data = {"name": clean_user_name, "email": clean_email, "password": clean_password}

        try:
            company, user, plugin_names = self.provisioning_service.provision_company(
                company_data=company_data,
                user_data=user_data,
                plugin_ids=plugin_ids or [],
            )
            # 3. Confirmação atômica no banco de dados
            self.db.session.commit()
        except Exception as exc:
            self.db.session.rollback()
            raise exc

        # 4. Disparo do e-mail de boas-vindas com credenciais através do EmailService
        EmailService.send_company_welcome_email(
            user_email=clean_email,
            user_name=clean_user_name,
            company_name=clean_company_name,
            plugins_list=plugin_names,
            password=clean_password,
        )

        # 5. Retorno estruturado e consolidado
        user_role_str = user.role.value if hasattr(user.role, "value") else str(user.role)

        return {
            "success": True,
            "company": {
                "id": company.id,
                "name": company.name,
                "cnpj": company.cnpj,
            },
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user_role_str,
            },
            "plugins": plugin_names,
        }
