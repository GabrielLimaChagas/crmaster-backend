from patterns.singleton.db_connection import DBConnection

db = DBConnection().db


class Product(db.Model):
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    price = db.Column(db.String(255), nullable=False)

    # Relationships
    sale_products = db.relationship('SaleProduct', back_populates='product', cascade='all, delete-orphan', lazy=True)

    def get_numeric_price(self) -> float:
        if self.price is None:
            return 0.0
        if isinstance(self.price, (int, float)):
            return float(self.price)
        price_str = str(self.price).strip().replace('R$', '').replace(' ', '')
        if not price_str:
            return 0.0
        if '.' in price_str and ',' in price_str:
            if price_str.rfind(',') > price_str.rfind('.'):
                price_str = price_str.replace('.', '').replace(',', '.')
            else:
                price_str = price_str.replace(',', '')
        elif ',' in price_str:
            price_str = price_str.replace(',', '.')
        try:
            return float(price_str)
        except ValueError:
            return 0.0

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price
        }
