# app/routes/auth.py - Professional Authentication - COMPLETE VERSION

from flask import Blueprint, render_template_string, request, session, redirect, flash
from app.models import User, Student, Instructor, Manager
import traceback
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# ==================== ROUTES ====================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Professional login handler"""
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            
            if not email or not password:
                flash('يرجى إدخال البريد الإلكتروني وكلمة المرور', 'danger')
                return redirect('/auth/login')
            
            # Get user from database
            user = User.get_by_email(email)
            
            if not user:
                logger.warning(f"Login attempt with non-existent email: {email}")
                flash('البريد الإلكتروني أو كلمة المرور غير صحيحة', 'danger')
                return redirect('/auth/login')
            
            # Demo password verification (use proper hashing in production)
            if password != 'password':
                logger.warning(f"Failed login attempt for: {email}")
                flash('البريد الإلكتروني أو كلمة المرور غير صحيحة', 'danger')
                return redirect('/auth/login')
            
            # Clear old session
            session.clear()
            
            # Set session data
            session['user_id'] = user[0]          # ID
            session['user_email'] = user[3]       # Email
            session['user_type'] = user[4]        # Person_type
            session['user_name'] = f"{user[1]} {user[2]}"  # F_name + L_name
            session.modified = True
            
            logger.info(f"Successful login: {email} ({user[4]})")
            
            # Redirect based on user type
            if user[4] == 'Student':
                student = Student.get_by_person_id(user[0])
                if student:
                    session['student_id'] = student[0]
                    session.modified = True
                    flash(f'أهلاً بك {session["user_name"]}! 👋', 'success')
                    return redirect('/student/dashboard')
            
            elif user[4] == 'Instructor':
                instructor = Instructor.get_by_person_id(user[0])
                if instructor:
                    session['instructor_id'] = instructor[0]
                    session.modified = True
                    flash(f'أهلاً بك {session["user_name"]}! 👋', 'success')
                    return redirect('/instructor/dashboard')
            
            elif user[4] == 'manager':
                manager = Manager.get_by_person_id(user[0])
                if manager:
                    session['manager_id'] = manager[0]
                    session.modified = True
                    flash(f'أهلاً بك {session["user_name"]}! 👋', 'success')
                    return redirect('/manager/dashboard')
            
            flash('نوع المستخدم غير معروف', 'danger')
            return redirect('/auth/login')
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}\n{traceback.format_exc()}")
            flash('حدث خطأ في النظام. يرجى المحاولة لاحقاً', 'danger')
            return redirect('/auth/login')
    
    return render_template_string(LOGIN_TEMPLATE)

@auth_bp.route('/logout')
def logout():
    """Logout and clear session"""
    user_name = session.get('user_name', 'المستخدم')
    session.clear()
    flash(f'تم تسجيل الخروج بنجاح. إلى اللقاء {user_name}! 👋', 'success')
    return redirect('/auth/login')

# ==================== LOGIN TEMPLATE ====================

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نظام الامتحانات الإلكترونية - تسجيل الدخول</title>
    <style>
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }
        
        body {
            font-family: 'Segoe UI', 'Cairo', Tahoma, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .login-wrapper {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0;
            max-width: 1000px;
            width: 100%;
            background: white;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            animation: slideUp 0.6s ease-out;
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .login-left {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 60px 40px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: white;
        }
        
        .login-left h2 {
            font-size: 2.5rem;
            margin-bottom: 20px;
            font-weight: 700;
        }
        
        .login-left p {
            font-size: 1.1rem;
            text-align: center;
            opacity: 0.9;
            line-height: 1.8;
            margin-bottom: 30px;
        }
        
        .feature-list {
            text-align: right;
            width: 100%;
        }
        
        .feature-item {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 20px;
            opacity: 0.95;
        }
        
        .feature-icon {
            font-size: 1.8rem;
        }
        
        .feature-text {
            font-size: 0.95rem;
        }
        
        .login-right {
            padding: 60px 40px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        .login-header {
            margin-bottom: 40px;
            text-align: center;
        }
        
        .login-header h3 {
            color: #333;
            font-size: 1.8rem;
            margin-bottom: 10px;
        }
        
        .login-header p {
            color: #999;
            font-size: 0.95rem;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            color: #333;
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 0.95rem;
        }
        
        .form-group input {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1rem;
            transition: all 0.3s;
            font-family: inherit;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .form-group input::placeholder {
            color: #ccc;
        }
        
        .btn-login {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.05rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 10px;
        }
        
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }
        
        .btn-login:active {
            transform: translateY(0);
        }
        
        .flash-messages {
            margin-bottom: 20px;
        }
        
        .alert {
            padding: 12px 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            font-size: 0.9rem;
            animation: fadeIn 0.3s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .alert-danger {
            background: #f8d7da;
            color: #721c24;
            border-left: 4px solid #f5c6cb;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border-left: 4px solid #c3e6cb;
        }
        
        .alert-warning {
            background: #fff3cd;
            color: #856404;
            border-left: 4px solid #ffeaa7;
        }
        
        .demo-credentials {
            background: #f0f8ff;
            border: 2px dashed #667eea;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            font-size: 0.85rem;
            color: #555;
        }
        
        .demo-credentials h4 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 0.95rem;
        }
        
        .demo-credentials ul {
            list-style: none;
            padding: 0;
        }
        
        .demo-credentials li {
            padding: 5px 0;
            border-bottom: 1px solid #ddd;
        }
        
        .demo-credentials li:last-child {
            border-bottom: none;
        }
        
        .demo-credentials strong {
            color: #667eea;
        }
        
        @media (max-width: 768px) {
            .login-wrapper {
                grid-template-columns: 1fr;
            }
            
            .login-left {
                padding: 40px 30px;
            }
            
            .login-right {
                padding: 40px 30px;
            }
            
            .login-left h2 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="login-wrapper">
        <!-- Left Side - Info -->
        <div class="login-left">
            <h2>🎓 ITI</h2>
            <p>نظام إدارة الامتحانات الإلكترونية المتقدم</p>
            
            <div class="feature-list">
                <div class="feature-item">
                    <div class="feature-icon">📝</div>
                    <div class="feature-text">امتحانات إلكترونية متطورة</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">📊</div>
                    <div class="feature-text">تقارير وإحصائيات فورية</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">🔒</div>
                    <div class="feature-text">نظام أمان متقدم</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">⚡</div>
                    <div class="feature-text">أداء سريع وموثوق</div>
                </div>
            </div>
        </div>
        
        <!-- Right Side - Login Form -->
        <div class="login-right">
            <div class="login-header">
                <h3>تسجيل الدخول</h3>
                <p>أدخل بيانات دخولك للمتابعة</p>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    <div class="flash-messages">
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">{{ message }}</div>
                        {% endfor %}
                    </div>
                {% endif %}
            {% endwith %}
            
            <form method="POST" action="/auth/login">
                <div class="form-group">
                    <label for="email">📧 البريد الإلكتروني</label>
                    <input 
                        type="email" 
                        id="email" 
                        name="email" 
                        placeholder="أدخل بريدك الإلكتروني"
                        required
                        autocomplete="email"
                    >
                </div>
                
                <div class="form-group">
                    <label for="password">🔐 كلمة المرور</label>
                    <input 
                        type="password" 
                        id="password" 
                        name="password" 
                        placeholder="أدخل كلمة المرور"
                        required
                        autocomplete="current-password"
                    >
                </div>
                
                <button type="submit" class="btn-login">🚀 دخول</button>
            </form>
            
            <div class="demo-credentials">
                <h4>📌 بيانات تجريبية:</h4>
                <ul>
                    <li><strong>أي بريد من قاعدة البيانات</strong></li>
                    
                </ul>
            </div>
        </div>
    </div>
</body>
</html>
'''
