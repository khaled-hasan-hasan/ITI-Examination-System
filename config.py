import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # SQL Server Configuration
    SQLSERVER_DRIVER = '{ODBC Driver 17 for SQL Server}'
    SQLSERVER_SERVER = 'khaled_win' 
    SQLSERVER_DATABASE = 'ITI_Examination_System'
    SQLSERVER_TRUSTED_CONNECTION = 'yes'
    
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
