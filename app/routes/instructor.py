# app/routes/instructor.py - COMPLETE FINAL VERSION
# Place in: app/routes/instructor.py

from flask import Blueprint, render_template_string, session, redirect, request, flash
from app.models import Instructor, Exam, Course, Student
from app.database import DatabaseConnection
from functools import wraps
import traceback

instructor_bp = Blueprint('instructor', __name__)

# ==================== DECORATOR ====================
def require_instructor(f=None):
    """Require instructor login - works with or without parentheses"""
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('يرجى تسجيل الدخول أولاً', 'warning')
                return redirect('/auth/login')
            if session.get('user_type') != 'Instructor':
                flash('هذه الصفحة للمدرسين فقط', 'danger')
                return redirect('/auth/login')
            return func(*args, **kwargs)
        return decorated_function
    
    if f is None:
        return decorator
    else:
        return decorator(f)

# ==================== TEMPLATES ====================
INSTRUCTOR_DASHBOARD = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة التحكم - المدرس</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', 'Cairo', Tahoma, sans-serif;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 20px 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 {
            color: #333;
            font-size: 1.8rem;
        }
        .btn-logout {
            padding: 10px 20px;
            background: #f44336;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: all 0.3s;
        }
        .btn-logout:hover {
            background: #d32f2f;
            transform: translateY(-2px);
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-card .icon {
            font-size: 3rem;
            margin-bottom: 10px;
        }
        .stat-card .value {
            font-size: 2rem;
            font-weight: bold;
            color: #f5576c;
            margin-bottom: 5px;
        }
        .stat-card .label {
            color: #666;
            font-size: 0.95rem;
        }
        .nav-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .nav-tabs button {
            padding: 12px 25px;
            background: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.3s;
            font-weight: 600;
        }
        .nav-tabs button.active {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        .content-section {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            display: none;
        }
        .content-section.active {
            display: block;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        table th, table td {
            padding: 12px;
            text-align: right;
            border-bottom: 1px solid #e0e0e0;
        }
        table th {
            background: #f8f9fa;
            font-weight: 600;
        }
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s;
        }
        .btn-primary {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
        }
        .alert {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .alert-success {
            background: #d4edda;
            color: #155724;
        }
        .alert-danger {
            background: #f8d7da;
            color: #721c24;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
        }
        .form-group input, .form-group select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1rem;
            font-family: inherit;
        }
        .form-group input:focus, .form-group select:focus {
            outline: none;
            border-color: #f5576c;
        }
        .btn-submit {
            padding: 12px 30px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
        }
        .btn-submit:hover {
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>👨‍🏫 مرحباً أستاذ {{ user_name }}</h1>
                <p style="color: #666;">{{ user_email }}</p>
            </div>
            <a href="/auth/logout" class="btn-logout">تسجيل الخروج</a>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon">📚</div>
                <div class="value">{{ courses|length }}</div>
                <div class="label">المقررات</div>
            </div>
            <div class="stat-card">
                <div class="icon">📝</div>
                <div class="value">{{ exams|length }}</div>
                <div class="label">الامتحانات</div>
            </div>
        </div>

        <div class="nav-tabs">
            <button class="active" onclick="showTab('courses')">المقررات</button>
            <button onclick="showTab('exams')">الامتحانات</button>
            <button onclick="showTab('create')">إنشاء امتحان</button>
        </div>

        <div id="courses" class="content-section active">
            <h2>📚 المقررات الدراسية</h2>
            {% if courses %}
                <table>
                    <thead>
                        <tr>
                            <th>رقم المقرر</th>
                            <th>اسم المقرر</th>
                            <th>الساعات</th>
                            <th>الموضوع</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for course in courses %}
                        <tr>
                            <td>{{ course[0] }}</td>
                            <td><strong>{{ course[1] }}</strong></td>
                            <td>{{ course[2] }}</td>
                            <td>{{ course[3] or 'N/A' }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            {% else %}
                <div class="empty-state">
                    <p>لا توجد مقررات حالياً</p>
                </div>
            {% endif %}
        </div>

        <div id="exams" class="content-section">
            <h2>📝 الامتحانات</h2>
            {% if exams %}
                <table>
                    <thead>
                        <tr>
                            <th>رقم الامتحان</th>
                            <th>المقرر</th>
                            <th>الفصل</th>
                            <th>العام</th>
                            <th>الدرجة</th>
                            <th>الإجراءات</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for exam in exams %}
                        <tr>
                            <td>{{ exam[0] }}</td>
                            <td>{{ exam[1] }}</td>
                            <td>{{ exam[2] }}</td>
                            <td>{{ exam[3] }}</td>
                            <td>{{ exam[4] }}</td>
                            <td>
                                <a href="/instructor/exam/{{ exam[0] }}/students" class="btn btn-primary">عرض الطلاب</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            {% else %}
                <div class="empty-state">
                    <p>لا توجد امتحانات بعد</p>
                </div>
            {% endif %}
        </div>

        <div id="create" class="content-section">
            <h2>➕ إنشاء امتحان جديد</h2>
            <form method="POST" action="/instructor/exam/create" style="max-width: 600px;">
                <div class="form-group">
                    <label for="course_id">المقرر</label>
                    <select name="course_id" id="course_id" required>
                        <option value="">اختر المقرر</option>
                        {% for course in courses %}
                        <option value="{{ course[0] }}">{{ course[1] }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group">
                    <label for="semester">الفصل الدراسي</label>
                    <input type="text" name="semester" id="semester" required placeholder="مثال: 1">
                </div>
                <div class="form-group">
                    <label for="year">العام</label>
                    <input type="number" name="year" id="year" required value="2024">
                </div>
                <div class="form-group">
                    <label for="total_marks">الدرجة الكلية</label>
                    <input type="number" name="total_marks" id="total_marks" required placeholder="100">
                </div>
                <div class="form-group">
                    <label for="time">الوقت (HH:MM:SS)</label>
                    <input type="text" name="time" id="time" placeholder="01:30:00" pattern="[0-9]{2}:[0-9]{2}:[0-9]{2}">
                    <small style="color: #666; display: block; margin-top: 5px;">صيغة الوقت: ساعة:دقيقة:ثانية (مثال: 01:30:00)</small>
                </div>
                <button type="submit" class="btn-submit">إنشاء الامتحان</button>
            </form>
        </div>
    </div>

    <script>
        function showTab(tabName) {
            document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.nav-tabs button').forEach(b => b.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
'''

EXAM_STUDENTS_PAGE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>طلاب الامتحان</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', 'Cairo', Tahoma, sans-serif;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 15px;
        }
        h1 { color: #333; margin-bottom: 20px; }
        .back-btn {
            display: inline-block;
            padding: 10px 20px;
            background: #e0e0e0;
            color: #333;
            text-decoration: none;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        table th, table td {
            padding: 12px;
            text-align: right;
            border-bottom: 1px solid #e0e0e0;
        }
        table th {
            background: #f8f9fa;
            font-weight: 600;
        }
        .badge {
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.85rem;
        }
        .badge-success { background: #d4edda; color: #155724; }
        .badge-warning { background: #fff3cd; color: #856404; }
        .badge-danger { background: #f8d7da; color: #721c24; }
        .exam-info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/instructor/dashboard" class="back-btn">← العودة</a>
        <h1>📊 طلاب امتحان: {{ exam[1] }}</h1>
        <div class="exam-info">
            <p><strong>الفصل:</strong> {{ exam[3] }} | <strong>العام:</strong> {{ exam[4] }}</p>
            <p><strong>الدرجة الكلية:</strong> {{ exam[5] }} درجة</p>
        </div>
        
        {% if students %}
            <table>
                <thead>
                    <tr>
                        <th>رقم الطالب</th>
                        <th>الاسم</th>
                        <th>الدرجة</th>
                        <th>التقدير</th>
                        <th>تاريخ الامتحان</th>
                    </tr>
                </thead>
                <tbody>
                    {% for student in students %}
                    <tr>
                        <td>{{ student[0] }}</td>
                        <td>{{ student[1] }} {{ student[2] }}</td>
                        <td><strong>{{ student[3] or 'قيد المراجعة' }}</strong></td>
                        <td>
                            {% if student[4] %}
                                <span class="badge badge-{{ 'success' if student[4] in ['A','B'] else 'warning' if student[4] in ['C','D'] else 'danger' }}">
                                    {{ student[4] }}
                                </span>
                            {% else %}
                                <span class="badge badge-warning">قيد المراجعة</span>
                            {% endif %}
                        </td>
                        <td>{{ student[5].strftime('%Y-%m-%d %H:%M') if student[5] else 'N/A' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        {% else %}
            <p style="text-align: center; padding: 60px; color: #999;">لم يقم أي طالب بإجراء هذا الامتحان بعد</p>
        {% endif %}
    </div>
</body>
</html>
'''

# ==================== ROUTES ====================
@instructor_bp.route('/dashboard')
@require_instructor
def dashboard():
    """Instructor dashboard"""
    try:
        instructor_id = session.get('instructor_id')
        
        print(f"\n{'='*60}")
        print(f"🔍 Loading dashboard for instructor {instructor_id}")
        print(f"{'='*60}")
        
        courses = Instructor.get_courses(instructor_id) or []
        exams = Instructor.get_exams(instructor_id) or []
        
        print(f"✅ Loaded {len(courses)} courses and {len(exams)} exams")
        print(f"{'='*60}\n")
        
        return render_template_string(
            INSTRUCTOR_DASHBOARD,
            user_name=session.get('user_name'),
            user_email=session.get('user_email'),
            courses=courses,
            exams=exams
        )
    except Exception as e:
        print(f"❌ Instructor dashboard error: {str(e)}")
        print(traceback.format_exc())
        flash(f'حدث خطأ في تحميل لوحة التحكم', 'danger')
        return redirect('/auth/login')

@instructor_bp.route('/exam/create', methods=['POST'])
@require_instructor
def create_exam():
    """Create new exam - REAL DATABASE OPERATION"""
    try:
        instructor_id = session.get('instructor_id')
        course_id = request.form.get('course_id')
        semester = request.form.get('semester')
        year = request.form.get('year')
        total_marks = request.form.get('total_marks')
        time = request.form.get('time') or None
        
        print(f"\n{'='*60}")
        print(f"📝 Creating exam for instructor {instructor_id}")
        print(f"  Course ID: {course_id}")
        print(f"  Semester: {semester}")
        print(f"  Year: {year}")
        print(f"  Total Marks: {total_marks}")
        print(f"  Time: {time}")
        print(f"{'='*60}")
        
        # Validate inputs
        if not all([course_id, semester, year, total_marks]):
            flash('⚠️ يرجى ملء جميع الحقول المطلوبة', 'warning')
            return redirect('/instructor/dashboard')
        
        # Create exam in database
        exam_id = Exam.create_exam(
            instructor_id=instructor_id,
            course_id=int(course_id),
            semester=semester,
            year=int(year),
            total_marks=int(total_marks),
            time=time
        )
        
        print(f"✅ Exam created successfully! Exam ID: {exam_id}")
        print(f"{'='*60}\n")
        
        flash(f'✅ تم إنشاء الامتحان بنجاح! رقم الامتحان: {exam_id}', 'success')
        return redirect('/instructor/dashboard')
        
    except Exception as e:
        print(f"❌ Create exam error: {str(e)}")
        print(traceback.format_exc())
        flash(f'حدث خطأ في إنشاء الامتحان: {str(e)}', 'danger')
        return redirect('/instructor/dashboard')

@instructor_bp.route('/exam/<int:exam_id>/students')
@require_instructor
def exam_students(exam_id):
    """View students who took specific exam"""
    try:
        print(f"\n{'='*60}")
        print(f"🔍 Loading students for exam {exam_id}")
        print(f"{'='*60}")
        
        exam = Exam.get_exam_by_id(exam_id)
        if not exam:
            flash('الامتحان غير موجود', 'danger')
            return redirect('/instructor/dashboard')
        
        print(f"📋 Exam: {exam[1]}")
        
        students = Instructor.get_students_for_exam(exam_id) or []
        
        print(f"✅ Found {len(students)} students who took this exam")
        print(f"{'='*60}\n")
        
        return render_template_string(
            EXAM_STUDENTS_PAGE,
            exam=exam,
            students=students
        )
    except Exception as e:
        print(f"❌ Exam students error: {str(e)}")
        print(traceback.format_exc())
        flash(f'حدث خطأ في عرض الطلاب', 'danger')
        return redirect('/instructor/dashboard')
