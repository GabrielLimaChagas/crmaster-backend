from patterns.singleton.db_connection import DBConnection

db = DBConnection().db


class CompanyPlugin(db.Model):
    __tablename__ = 'company_plugin'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False
    )
    plugin_id = db.Column(
        db.Integer,
        db.ForeignKey('plugins.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False
    )

    # Relationships
    company = db.relationship('Company', back_populates='company_plugins')
    plugin = db.relationship('Plugin', back_populates='company_plugins')

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'plugin_id': self.plugin_id
        }
