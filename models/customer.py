from patterns.singleton.db_connection import DBConnection

db = DBConnection().db


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.String(255), nullable=True)
    cel = db.Column(db.String(64), nullable=True)
    email = db.Column(db.String(64), nullable=True)
    birth = db.Column(db.DateTime, nullable=True)
    address = db.Column(db.String(64), nullable=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey('companies.id', ondelete='SET NULL', onupdate='CASCADE'),
        nullable=True
    )

    # Relationships
    company = db.relationship('Company', back_populates='customers')
    pipelines = db.relationship('Pipeline', back_populates='customer', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'notes': self.notes,
            'cel': self.cel,
            'email': self.email,
            'birth': self.birth.isoformat() if self.birth else None,
            'address': self.address,
            'company_id': self.company_id
        }
