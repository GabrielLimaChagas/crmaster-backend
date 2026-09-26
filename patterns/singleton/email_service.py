import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class GmailService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.username = None
            cls._instance.password = None
            cls._instance.default_sender = None
            cls._instance.smtp_server = "smtp.gmail.com"
            cls._instance.smtp_port = 587
        return cls._instance

    def init_app(self, app):
        self.username = app.config.get('MAIL_USERNAME')
        self.password = app.config.get('MAIL_PASSWORD')
        self.default_sender = app.config.get('MAIL_DEFAULT_SENDER', self.username)

    def send_email(self, to_email: str, subject: str, body: str, is_html: bool = False):
        if not self.username or not self.password:
            raise ValueError("GmailService não foi inicializado corretamente com credenciais.")

        msg = MIMEMultipart()
        msg['From'] = self.default_sender
        msg['To'] = to_email
        msg['Subject'] = subject

        mime_type = 'html' if is_html else 'plain'
        msg.attach(MIMEText(body, mime_type))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Erro ao enviar e-mail: {e}")
            return False