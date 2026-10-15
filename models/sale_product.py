from patterns.singleton.db_connection import DBConnection

db = DBConnection().db


class SaleProduct(db.Model):
    __tablename__ = 'sale_product'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quantidade = db.Column(db.Integer, nullable=False)
    sale_id = db.Column(
        db.Integer,
        db.ForeignKey('pipelines.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=True
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey('product.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=True
    )

    # Relationships
    sale = db.relationship('Pipeline', back_populates='sale_products')
    product = db.relationship('Product', back_populates='sale_products')

    def subtotal(self) -> float:
        if self.product and self.quantidade:
            return round(self.quantidade * self.product.get_numeric_price(), 2)
        return 0.0

    def to_dict(self):
        product_name = self.product.name if self.product else "Produto"
        numeric_price = self.product.get_numeric_price() if self.product else 0.0
        return {
            'id': self.id,
            'quantidade': self.quantidade,
            'sale_id': self.sale_id,
            'product_id': self.product_id,
            'name': product_name,
            'product_name': product_name,
            'price': numeric_price,
            'subtotal': self.subtotal()
        }
