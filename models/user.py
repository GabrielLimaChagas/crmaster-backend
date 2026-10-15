from patterns.singleton.db_connection import DBConnection
from .enums import UserRole

db = DBConnection().db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(
        'company',
        db.Integer,
        db.ForeignKey('companies.id', ondelete='SET NULL', onupdate='CASCADE'),
        nullable=True
    )
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    # Relationships
    company = db.relationship('Company', back_populates='users')
    pipelines = db.relationship('Pipeline', back_populates='employee', lazy=True)

    def __init__(self, **kwargs):
        if 'company' in kwargs and isinstance(kwargs['company'], int):
            kwargs['company_id'] = kwargs.pop('company')
        super().__init__(**kwargs)

    def is_manager(self) -> bool:
        if isinstance(self.role, UserRole):
            return self.role == UserRole.MANAGER
        return self.role == UserRole.MANAGER.value

    def to_dict(self):
        active_plugins = []
        if self.company:
            active_plugins = self.company.get_active_plugin_slugs()
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role.value if hasattr(self.role, 'value') else self.role,
            'email': self.email,
            'company_id': self.company_id,
            'plugins': active_plugins,
            'active_plugins': active_plugins,
        }
