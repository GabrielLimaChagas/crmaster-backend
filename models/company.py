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

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'cnpj': self.cnpj,
            'campany_id': self.campany_id
        }
