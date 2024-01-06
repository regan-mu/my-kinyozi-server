import os


class Config:
    SECRET_KEY = os.environ.get('SECRET')
    SQLALCHEMY_DATABASE_URI = os.environ.get('KINYOZI_DB')  # "sqlite:///app.db"
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('EMAIL_ADDRESS')
    MAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
