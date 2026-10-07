from patterns.singleton.db_connection import DBConnection

db = DBConnection().db


class Plugin(db.Model):
    __tablename__ = 'plugins'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)

    # Relationships
    company_plugins = db.relationship('CompanyPlugin', back_populates='plugin', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }
