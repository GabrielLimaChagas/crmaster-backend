from flask import Flask
from config.config import Config
from patterns.singleton.db_connection import DBConnection

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db_manager = DBConnection()

    db_manager.init_app(app)

    with app.app_context():
        db_manager.db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)