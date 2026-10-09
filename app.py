from flask import Flask
from config.config import Config
from patterns.singleton.db_connection import DBConnection
from patterns.singleton.email_service import GmailService

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db_manager = DBConnection()
    db_manager.init_app(app)

    email_service = GmailService()
    email_service.init_app(app)        

    try:
        email_service.send_email(
            to_email="ddnvoreznubgncgedn@kjkpc.net",
            subject="Teste Email",
            body="<h1>This is a test email from Flask app</h1>",
            is_html=True
        )
    except Exception as e:
        print(f"[Aviso] Não foi possível enviar e-mail de inicialização: {e}")
    
    from routes.customer_routes import customer_bp
    app.register_blueprint(customer_bp)

    with app.app_context():
        import models
        try:
            db_manager.db.create_all()
        except Exception as e:
            print(f"[Aviso] create_all não pôde ser executado imediatamente: {e}")

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)