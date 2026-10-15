"""Script utilitário para criar ou redefinir o usuário Administrador padrão."""

import os
import sys

# Adiciona o diretório do backend ao sys.path para importação dos módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models.company import Company
from models.company_plugin import CompanyPlugin
from models.enums import UserRole
from models.plugin import Plugin
from models.user import User
from patterns.singleton.db_connection import DBConnection


def seed():
    app = create_app()
    with app.app_context():
        db = DBConnection().db

        # 1. Garante empresa padrão
        company = Company.query.first()
        if not company:
            company = Company(name="Empresa Principal", cnpj="00.000.000/0001-91")
            db.session.add(company)
            db.session.flush()
            print(f"[+] Empresa criada com id {company.id}")
        else:
            print(f"[*] Empresa padrão encontrada: #{company.id} - {company.name}")

        # 2. Garante plugins padrão do sistema
        plugins_seed = ["notifications_plugin", "import_export_plugin"]
        for p_name in plugins_seed:
            plugin = Plugin.query.filter_by(name=p_name).first()
            if not plugin:
                plugin = Plugin(name=p_name)
                db.session.add(plugin)
                db.session.flush()
                print(f"[+] Plugin criado: {p_name}")

            cp = CompanyPlugin.query.filter_by(company_id=company.id, plugin_id=plugin.id).first()
            if not cp:
                cp = CompanyPlugin(company_id=company.id, plugin_id=plugin.id)
                db.session.add(cp)
                print(f"[+] Plugin '{p_name}' vinculado à Empresa #{company.id}")

        # 3. Garante usuário administrador
        admin = User.query.filter_by(email="admin@crmaster.com").first()
        if not admin:
            admin = User(
                name="Administrador",
                email="admin@crmaster.com",
                password="admin",
                role=UserRole.COMPANY,
                company=company.id
            )
            db.session.add(admin)
            print("[+] Usuário admin criado com sucesso!")
        else:
            admin.password = "admin"
            admin.role = UserRole.COMPANY
            admin.company_id = company.id
            print("[*] Usuário admin já existente atualizado com sucesso!")

        db.session.commit()
        print("\n=== CREDENCIAIS DE ACESSO ===")
        print("E-mail/Usuário: admin@crmaster.com ou Administrador")
        print("Senha:          admin")
        print(f"Empresa:        #{company.id} - {company.name}")
        print(f"Cargo:          {admin.role.value if hasattr(admin.role, 'value') else admin.role}")
        print("=============================")


if __name__ == "__main__":
    seed()
