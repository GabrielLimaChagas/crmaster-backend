from patterns.singleton.db_connection import DBConnection
from .enums import PipelineStep

db = DBConnection().db


class Pipeline(db.Model):
    __tablename__ = 'pipelines'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    note = db.Column(db.String(255), nullable=True)
    date = db.Column(db.DateTime, nullable=True)
    step = db.Column(db.Enum(PipelineStep), nullable=False, default=PipelineStep.PROPSECTING)
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey('customers.id', ondelete='SET NULL', onupdate='CASCADE'),
        nullable=True
    )
    employee_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='SET NULL', onupdate='CASCADE'),
        nullable=True
    )

    # Relationships
    customer = db.relationship('Customer', back_populates='pipelines')
    employee = db.relationship('User', back_populates='pipelines')
    sale_products = db.relationship('SaleProduct', back_populates='sale', cascade='all, delete-orphan', lazy=True)

    def advance_step(self):
        steps = list(PipelineStep)
        current = self.step if isinstance(self.step, PipelineStep) else PipelineStep(self.step)
        current_index = steps.index(current)
        if current_index < len(steps) - 1:
            self.step = steps[current_index + 1]
        return self.step

    def calculate_total(self) -> float:
        total = sum(item.subtotal() for item in self.sale_products) if self.sale_products else 0.0
        return round(float(total), 2)

    def to_dict(self):
        return {
            'id': self.id,
            'note': self.note,
            'date': self.date.isoformat() if self.date else None,
            'step': self.step.value if hasattr(self.step, 'value') else self.step,
            'customer_id': self.customer_id,
            'employee_id': self.employee_id,
            'total': self.calculate_total()
        }
