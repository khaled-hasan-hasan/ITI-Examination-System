# app/__init__.py - Flask Application Factory - PROFESSIONAL VERSION

from flask import Flask, redirect
from app.database import DatabaseConnection
import logging
from app.routes.manager_ml import manager_ml_bp




# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """
    Create and configure Flask application
    
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    
    # ==================== CONFIGURATION ====================
    app.config['SECRET_KEY'] = 'ITI-Examination-System-Secret-Key-2024-Change-In-Production'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = 7200  # 2 hours
    app.config['SESSION_PERMANENT'] = False
    app.register_blueprint(manager_ml_bp)
    logger.info("Flask app created with configuration")
    
    # ==================== DATABASE TEST ====================
    try:
        test_conn = DatabaseConnection.get_connection()
        test_conn.close()
        logger.info("✓ Database connection successful")
    except Exception as e:
        logger.warning(f"⚠️ Database connection test failed: {e}")
    
    # ==================== REGISTER BLUEPRINTS ====================
    try:
        from app.routes.auth import auth_bp
        from app.routes.student import student_bp
        from app.routes.instructor import instructor_bp
        from app.routes.manager import manager_bp
        
        # Register authentication blueprint
        app.register_blueprint(auth_bp)
        logger.info("✓ auth_bp registered: /auth")
        
        # Register student blueprint
        app.register_blueprint(student_bp, url_prefix='/student')
        logger.info("✓ student_bp registered: /student")
        
        # Register instructor blueprint
        app.register_blueprint(instructor_bp, url_prefix='/instructor')
        logger.info("✓ instructor_bp registered: /instructor")
        
        # Register manager blueprint
        app.register_blueprint(manager_bp, url_prefix='/manager')
        logger.info("✓ manager_bp registered: /manager")
        
        # Try to register ML features (optional)
        try:
            from app.routes.student_ml import student_ml_bp
            app.register_blueprint(student_ml_bp)
            logger.info("✓ student_ml_bp registered: /student/ml")
        except ImportError:
            logger.info("⚠️ student_ml_bp not available (ML features disabled)")
        
    except Exception as e:
        logger.error(f"❌ Blueprint registration error: {e}")
        raise
    
    # ==================== ROOT ROUTE ====================
    @app.route('/')
    def index():
        """Redirect root to login"""
        return redirect('/auth/login')
    
    # ==================== ERROR HANDLERS ====================
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        logger.warning(f"404 error: {error}")
        return '''
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>404 - صفحة غير موجودة</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Cairo', sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .container {
                    background: white;
                    padding: 60px;
                    border-radius: 20px;
                    text-align: center;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                }
                .code {
                    font-size: 120px;
                    color: #667eea;
                    font-weight: bold;
                }
                h1 { color: #333; margin: 20px 0; }
                p { color: #666; margin-bottom: 30px; }
                a {
                    padding: 12px 30px;
                    background: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="code">404</div>
                <h1>الصفحة غير موجودة</h1>
                <p>الصفحة التي تبحث عنها غير متاحة</p>
                <a href="/auth/login">العودة للصفحة الرئيسية</a>
            </div>
        </body>
        </html>
        ''', 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        logger.error(f"500 error: {error}")
        return '''
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>500 - خطأ في الخادم</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Cairo', sans-serif;
                    background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
                    height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .container {
                    background: white;
                    padding: 60px;
                    border-radius: 20px;
                    text-align: center;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                }
                .code {
                    font-size: 120px;
                    color: #dc3545;
                    font-weight: bold;
                }
                h1 { color: #333; margin: 20px 0; }
                p { color: #666; margin-bottom: 30px; }
                a {
                    padding: 12px 30px;
                    background: #dc3545;
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="code">500</div>
                <h1>خطأ في الخادم</h1>
                <p>حدث خطأ غير متوقع. يرجى المحاولة لاحقاً</p>
                <a href="/auth/login">العودة للصفحة الرئيسية</a>
            </div>
        </body>
        </html>
        ''', 500
    
    logger.info("App initialization complete")
    return app
