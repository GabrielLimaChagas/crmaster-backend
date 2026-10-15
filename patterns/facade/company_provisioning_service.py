"""Subsistema de provisionamento transacional de novas empresas, plugins e usuários administradores."""

from typing import Any
from models.company import Company
from models.company_plugin import CompanyPlugin
from models.enums import UserRole
from models.plugin import Plugin
from models.user import User
from patterns.singleton.db_connection import DBConnection


class CompanyProvisioningService:
    """Subsistema responsável por persistir as entidades vinculadas ao onboarding da empresa."""

    def __init__(self, db_session: Any = None) -> None:
        """Inicializa o serviço de provisionamento com a sessão do SQLAlchemy.

        Args:
            db_session: Sessão do SQLAlchemy (opcional; se omitida, usa DBConnection().db.session).
        """
        self.db_session = db_session if db_session is not None else DBConnection().db.session

    def provision_company(
        self,
        company_data: dict[str, str],
        user_data: dict[str, str],
        plugin_ids: list[int] | None = None,
    ) -> tuple[Company, User, list[str]]:
        """Provisiona atomicamente a empresa, o usuário administrador e os plugins habilitados.

        Args:
            company_data: Dicionário contendo 'name' e 'cnpj'.
            user_data: Dicionário contendo 'name', 'email' e 'password'.
            plugin_ids: Lista de identificadores de plugins a serem vinculados.

        Returns:
            Tupla contendo (empresa_criada, usuario_administrador, nomes_dos_plugins).
        """
        if plugin_ids is None:
            plugin_ids = []

        # 1. Cria e adiciona a nova Empresa
        company = Company(
            name=str(company_data["name"]).strip(),
            cnpj=str(company_data["cnpj"]).strip(),
        )
        self.db_session.add(company)
        self.db_session.flush()

        # 2. Vincula os plugins habilitados
        plugin_names: list[str] = []
        default_plugin_catalog: dict[int, str] = {
            1: "Módulo Vendas & Pipeline Pro",
            2: "Integração WhatsApp & Mensageria",
            3: "Analytics & Dashboard Executivo",
            4: "Automação de Marketing",
        }

        for p_id in plugin_ids:
            # Garante a existência do plugin para integridade de Foreign Key
            plugin = self.db_session.get(Plugin, p_id)
            if not plugin:
                name = default_plugin_catalog.get(p_id, f"Módulo Adicional #{p_id}")
                plugin = Plugin(id=p_id, name=name)
                self.db_session.add(plugin)
                self.db_session.flush()

            plugin_names.append(plugin.name)

            company_plugin = CompanyPlugin(
                company_id=company.id,
                plugin_id=plugin.id,
            )
            self.db_session.add(company_plugin)

        # 3. Cria e adiciona o Usuário Administrador da Empresa (Role COMPANY)
        user = User(
            name=str(user_data["name"]).strip(),
            email=str(user_data["email"]).strip(),
            password=str(user_data["password"]).strip(),
            role=UserRole.COMPANY,
            company=company.id,
        )
        self.db_session.add(user)
        self.db_session.flush()

        return company, user, plugin_names
