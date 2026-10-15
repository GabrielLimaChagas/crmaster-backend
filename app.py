from flask import Flask
from flask_cors import CORS
from config.config import Config
from patterns.singleton.db_connection import DBConnection
from patterns.singleton.email_service import GmailService

def create_app():
    print("[1] Iniciando app...")
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configuração de CORS para permitir requisições do frontend local
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    print("[2] Conectando ao Banco...")
    db_manager = DBConnection()
    db_manager.init_app(app)

    print("[3] Iniciando Gmail...")
    email_service = GmailService()
    email_service.init_app(app)        
    
    from routes.customer_routes import customer_bp
    from routes.product_routes import product_bp
    from routes.metric_routes import metric_bp
    from routes.pipeline_routes import pipeline_bp
    from routes.company_routes import company_bp
    from routes.notification_routes import notification_bp
    app.register_blueprint(customer_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(metric_bp)
    app.register_blueprint(pipeline_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(notification_bp)

    @app.after_request
    def set_no_cache_headers(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    print("[4] Executando create_all...")
    with app.app_context():
        import models
        try:
            db_manager.db.create_all()
        except Exception as e:
            print(f"[Aviso] create_all erro: {e}")

    print("[5] App criado com sucesso!")
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)