from patterns.singleton.db_connection import DBConnection

db = DBConnection().db


class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    cnpj = db.Column(db.String(255), nullable=False)
    campany_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id', ondelete='SET NULL', onupdate='CASCADE'),
        nullable=True
    )

    # Self-referential relationship
    parent = db.relationship('Company', remote_side=[id], backref=db.backref('subsidiaries', lazy=True))

    # Relationships
    users = db.relationship('User', back_populates='company', lazy=True)
    customers = db.relationship('Customer', back_populates='company', lazy=True)
    company_plugins = db.relationship('CompanyPlugin', back_populates='company', cascade='all, delete-orphan', lazy=True)

    def get_active_plugin_slugs(self) -> list[str]:
        slugs = []
        if self.company_plugins:
            for cp in self.company_plugins:
                if cp.plugin:
                    raw_name = cp.plugin.name
                    if raw_name not in slugs:
                        slugs.append(raw_name)
                    lower_name = raw_name.lower()
                    if "notif" in lower_name or "mensageria" in lower_name:
                        if "notifications_plugin" not in slugs:
                            slugs.append("notifications_plugin")
                    if "import" in lower_name or "export" in lower_name:
                        if "import_export_plugin" not in slugs:
                            slugs.append("import_export_plugin")
        return slugs

    def to_dict(self):
        plugins = []
        if self.company_plugins:
            for cp in self.company_plugins:
                if cp.plugin:
                    plugins.append({
                        'id': cp.plugin.id,
                        'name': cp.plugin.name
                    })
        active_slugs = self.get_active_plugin_slugs()
        return {
            'id': self.id,
            'name': self.name,
            'cnpj': self.cnpj,
            'campany_id': self.campany_id,
            'plugins': plugins,
            'plugin_ids': [p['id'] for p in plugins],
            'active_plugins': active_slugs,
        }
