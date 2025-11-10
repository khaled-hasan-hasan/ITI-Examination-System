# app/routes/student.py - Student Routes - PROFESSIONAL COMPLETE VERSION
# All bugs fixed, all features preserved, professional design

from flask import Blueprint, jsonify, render_template_string, session, redirect, request, flash
from app.models import Student, Question, Exam
from functools import wraps
from datetime import datetime
import traceback
import logging
from app.chatbot import get_chatbot
from app.ml_helper import get_ml_helper
import json

logger = logging.getLogger(__name__)
student_bp = Blueprint('student', __name__)

# ==================== DECORATOR ====================

def require_student(f=None):
    """Decorator to require student login"""
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('يرجى تسجيل الدخول أولاً', 'warning')
                return redirect('/auth/login')
            if session.get('user_type') != 'Student':
                flash('هذه الصفحة للطلاب فقط', 'danger')
                return redirect('/auth/login')
            return func(*args, **kwargs)
        return decorated_function
    
    if f is None:
        return decorator
    else:
        return decorator(f)

# ==================== ROUTES ====================
# ==================== CHATBOT ROUTES ====================

@student_bp.route('/chatbot')
@require_student
def chatbot_page():
    """صفحة الـ Chatbot"""
    username = session.get('username', 'Student')
    return render_template_string(CHATBOT_TEMPLATE, username=username)


@student_bp.route('/chatbot/ask', methods=['POST'])
@require_student
def chatbot_ask():
    """API للتحدث مع الـ Chatbot"""
    try:
        student_id = session.get('student_id')
        user_message = request.form.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'الرسالة فارغة'}), 400
        
        # جلب معلومات الطالب للسياق
        from app.models import Student
        
        avg_score = Student.get_average_score(student_id)
        completed_exams = Student.get_completed_exams(student_id)
        exam_count = len(completed_exams) if completed_exams else 0
        
        last_exam = None
        last_score = None
        if completed_exams:
            last_exam = completed_exams[0][0]  # اسم آخر امتحان
            last_score = completed_exams[0][1]  # درجة آخر امتحان
        
        student_context = {
            'name': session.get('username'),
            'avg_score': f"{avg_score:.1f}" if avg_score else 'N/A',
            'exam_count': exam_count,
            'last_exam': last_exam or 'لا يوجد',
            'last_score': f"{last_score:.1f}" if last_score else 'N/A'
        }
        
        # الحصول على الرد من الـ Chatbot
        chatbot = get_chatbot()
        bot_response = chatbot.get_response(user_message, student_context)
        
        return jsonify({
            'status': 'success',
            'response': bot_response
        })
    
    except Exception as e:
        logger.error(f"Chatbot error: {str(e)}")
        return jsonify({
            'status': 'error',
            'response': 'عذراً، حدث خطأ. حاول مرة أخرى.'
        }), 500


# ==================== ML INSIGHTS ROUTES ====================

@student_bp.route('/insights')
@require_student
def student_insights():
    """صفحة رؤى الأداء المدعومة بـ ML"""
    try:
        student_id = session.get('student_id')
        username = session.get('username', 'Student')
        
        # الحصول على التحليلات من ML Helper
        ml_helper = get_ml_helper()
        insights = ml_helper.get_student_insights(student_id)
        prediction = ml_helper.predict_next_exam(student_id)
        
        return render_template_string(INSIGHTS_TEMPLATE,
            username=username,
            insights=insights,
            prediction=prediction
        )
    
    except Exception as e:
        logger.error(f"Insights error: {str(e)}")
        flash('حدث خطأ في تحميل التحليلات', 'danger')
        return redirect('/student/dashboard')


@student_bp.route('/study-tips/<topic>')
@require_student
def get_study_tips(topic):
    """الحصول على نصائح دراسية لموضوع معين"""
    try:
        chatbot = get_chatbot()
        tips = chatbot.get_study_tips(topic)
        
        return jsonify({
            'status': 'success',
            'tips': tips
        })
    
    except Exception as e:
        logger.error(f"Study tips error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'حدث خطأ في جلب النصائح'
        }), 500

@student_bp.route('/dashboard')
@require_student
def dashboard():
    """Student dashboard with statistics"""
    try:
        student_id = session.get('student_id')
        user_name = session.get('user_name', 'الطالب')
        
        # Get all exam data
        available_exams = Student.get_available_exams(student_id) or []
        completed_exams = Student.get_completed_exams(student_id) or []
        grades = Student.get_grades(student_id) or []
        
        # Calculate statistics
        total_exams = len(completed_exams)
        avg_score = Student.get_average_score(student_id)
        
        logger.info(f"Dashboard loaded for student {student_id}: {len(available_exams)} available, {total_exams} completed")
        
        return render_template_string(
            STUDENT_DASHBOARD,
            user_name=user_name,
            available_exams=available_exams,
            completed_exams=completed_exams,
            grades=grades,
            total_exams=total_exams,
            avg_score=avg_score
        )
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}\n{traceback.format_exc()}")
        flash(f'حدث خطأ: {str(e)}', 'danger')
        return redirect('/auth/login')

@student_bp.route('/exam/<int:exam_id>')
@require_student
def take_exam(exam_id):
    """Start taking an exam - FIXED"""
    try:
        student_id = session.get('student_id')
        logger.info(f"Student {student_id} starting exam {exam_id}")
        
        # Check if already taken
        existing = Student.check_exam_taken(student_id, exam_id)
        if existing:
            logger.warning(f"Student {student_id} already took exam {exam_id}")
            flash('لقد أجريت هذا الامتحان من قبل', 'warning')
            return redirect('/student/dashboard')
        
        # Get exam details
        exam = Exam.get_exam_by_id(exam_id)
        if not exam:
            logger.error(f"Exam {exam_id} not found")
            flash('الامتحان غير موجود', 'danger')
            return redirect('/student/dashboard')
        
        logger.info(f"Exam {exam_id} details loaded: {exam[1]}")
        
        # Get questions - FIXED: Better error handling
        questions = Question.get_exam_questions(exam_id)
        if not questions:
            logger.error(f"No questions found for exam {exam_id}")
            flash('لا توجد أسئلة لهذا الامتحان. يرجى التواصل مع المدرس.', 'warning')
            return redirect('/student/dashboard')
        
        logger.info(f"Loaded {len(questions)} questions for exam {exam_id}")
        
        # Get choices for each question - FIXED: Comprehensive loading
        choices = {}
        for q in questions:
            q_id = q[0]
            q_type = q[2]
            
            # Check if it's MCQ (multiple variations supported)
            if q_type and any(mcq_type in str(q_type).upper() for mcq_type in ['MCQ', 'MULTIPLE']):
                q_choices = Question.get_question_choices(q_id)
                if q_choices:
                    choices[q_id] = q_choices
                    logger.info(f"Q{q_id}: Loaded {len(q_choices)} choices")
                else:
                    logger.warning(f"Q{q_id}: No choices found despite being MCQ type")
        
        logger.info(f"Total MCQ questions with choices: {len(choices)}/{len(questions)}")
        
        # CRITICAL FIX: Create TAKES record and save to session
        try:
            takes_id = Student.start_exam(student_id, exam_id)
            if takes_id:
                # Clear old session data
                session.pop('current_takes_id', None)
                session.pop('current_exam_id', None)
                
                # Set new session
                session['current_takes_id'] = int(takes_id)
                session['current_exam_id'] = int(exam_id)
                session.modified = True
                
                logger.info(f"✓ Exam session created: Takes_ID={takes_id}")
            else:
                logger.error(f"Failed to create TAKES record for student {student_id}, exam {exam_id}")
                flash('فشل في بدء الامتحان - خطأ في النظام', 'danger')
                return redirect('/student/dashboard')
        except Exception as e:
            logger.error(f"Error starting exam: {str(e)}\n{traceback.format_exc()}")
            flash(f'خطأ في بدء الامتحان: {str(e)}', 'danger')
            return redirect('/student/dashboard')
        
        return render_template_string(
            EXAM_TEMPLATE,
            exam=exam,
            questions=questions,
            choices=choices,
            takes_id=takes_id  # Pass takes_id to template for hidden field
        )
        
    except Exception as e:
        logger.error(f"Take exam error: {str(e)}\n{traceback.format_exc()}")
        flash(f'حدث خطأ: {str(e)}', 'danger')
        return redirect('/student/dashboard')

@student_bp.route('/exam/submit', methods=['POST'])
@require_student
def submit_exam():
    """Submit exam answers - FIXED"""
    try:
        # CRITICAL: Get takes_id from form first (session backup)
        takes_id = request.form.get('takes_id')
        exam_id = request.form.get('exam_id')

        # Fallback to session if form data missing
        if not takes_id:
            takes_id = session.get('current_takes_id')
        if not exam_id:
            exam_id = session.get('current_exam_id')

        # Convert to int if strings
        takes_id = int(takes_id) if takes_id else None
        exam_id = int(exam_id) if exam_id else None
        student_id = session.get('student_id')
        
        logger.info(f"Submitting exam: Takes_ID={takes_id}, Exam_ID={exam_id}, Student={student_id}")
        
        if not takes_id or not exam_id:
            logger.error(f"Session error: takes_id={takes_id}, exam_id={exam_id}")
            flash('خطأ: جلسة الامتحان منتهية. يرجى بدء الامتحان من جديد', 'danger')
            return redirect('/student/dashboard')
        
        # Get exam questions
        questions = Question.get_exam_questions(exam_id)
        if not questions:
            logger.error(f"No questions found for exam {exam_id} during submission")
            flash('خطأ: لم يتم العثور على أسئلة الامتحان', 'danger')
            return redirect('/student/dashboard')
        
        # Save answers and calculate score
        total_score = 0.0
        answered_count = 0
        
        for q in questions:
            q_id = q[0]
            q_type = q[2]
            marks = float(q[3]) if q[3] else 1.0
            
            answer_key = f'question_{q_id}'
            
            # Handle MCQ questions
            if q_type and any(mcq in str(q_type).upper() for mcq in ['MCQ', 'MULTIPLE']):
                selected_choice = request.form.get(answer_key)
                if selected_choice:
                    try:
                        choice_id = int(selected_choice)
                        # Save answer
                        Question.save_student_answer(takes_id, q_id, choice_id=choice_id)
                        answered_count += 1
                        
                        # Check if correct
                        is_correct = Question.check_mcq_answer(q_id, choice_id)
                        if is_correct:
                            total_score += marks
                            logger.debug(f"✓ Q{q_id}: Correct!")
                        else:
                            logger.debug(f"✗ Q{q_id}: Incorrect")
                    except ValueError:
                        logger.warning(f"Invalid choice ID for Q{q_id}: {selected_choice}")
            
            # Handle True/False questions
            elif q_type and 'TRUE' in str(q_type).upper():
                selected = request.form.get(answer_key)
                if selected:
                    Question.save_student_answer(takes_id, q_id, answer_text=selected)
                    answered_count += 1
            
            # Handle Essay/Short Answer
            else:
                text_answer = request.form.get(answer_key, '').strip()
                if text_answer:
                    Question.save_student_answer(takes_id, q_id, answer_text=text_answer)
                    answered_count += 1
        
        # Get exam total marks
        exam = Exam.get_exam_by_id(exam_id)
        total_marks = float(exam[5]) if exam and exam[5] else 100.0
        
        # Calculate percentage and grade
        percentage = (total_score / total_marks * 100) if total_marks > 0 else 0
        
        if percentage >= 90:
            grade = 'A'
        elif percentage >= 80:
            grade = 'B'
        elif percentage >= 70:
            grade = 'C'
        elif percentage >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        # Update TAKES record with final score
        Student.submit_exam(takes_id, total_score, grade)
        
        # Clear session
        session.pop('current_takes_id', None)
        session.pop('current_exam_id', None)
        session.modified = True
        
        logger.info(f"✓ Exam submitted: Score={total_score}/{total_marks}, Grade={grade}, Answered={answered_count}/{len(questions)}")
        
        message = f'تم تسليم الامتحان بنجاح! 🎉\\nدرجتك: {total_score}/{total_marks}\\nالتقدير: {grade}\\nعدد الأسئلة المجابة: {answered_count}/{len(questions)}'
        flash(message, 'success')
        return redirect('/student/dashboard')
        
    except Exception as e:
        logger.error(f"Submit exam error: {str(e)}\n{traceback.format_exc()}")
        flash(f'حدث خطأ عند تسليم الامتحان: {str(e)}', 'danger')
        return redirect('/student/dashboard')

# ==================== TEMPLATES ====================

STUDENT_DASHBOARD = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة الطالب</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', 'Cairo', Tahoma, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container { max-width: 1200px; margin: 0 auto; }
        
        .header {
            background: white;
            padding: 25px 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 { color: #333; font-size: 1.8rem; }
        
        .logout-btn {
            padding: 10px 20px;
            background: #dc3545;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: all 0.3s;
            font-weight: 600;
        }
        
        .logout-btn:hover { 
            background: #c82333; 
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
            transition: all 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }
        
        .stat-icon { font-size: 3rem; margin-bottom: 10px; }
        .stat-value { font-size: 2.2rem; font-weight: bold; color: #667eea; }
        .stat-label { color: #999; margin-top: 10px; }
        
        .nav-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            background: white;
            padding: 10px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }
        
        .nav-tabs button {
            flex: 1;
            padding: 12px 20px;
            background: #f0f0f0;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .nav-tabs button:hover,
        .nav-tabs button.active {
            background: #667eea;
            color: white;
        }
        
        .content-section {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            display: none;
        }
        
        .content-section.active { display: block; animation: fadeIn 0.3s; }
        
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        
        .exam-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #f9fafb 100%);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            border-right: 4px solid #667eea;
            transition: all 0.3s;
        }
        
        .exam-card:hover {
            transform: translateX(-5px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.1);
        }
        
        .exam-card h3 { color: #333; margin-bottom: 10px; }
        .exam-info { color: #999; font-size: 0.9rem; margin-bottom: 12px; }
        
        .start-btn {
            padding: 10px 25px;
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            display: inline-block;
            transition: all 0.3s;
            font-weight: 600;
        }
        
        .start-btn:hover {
            background: linear-gradient(135deg, #218838 0%, #1aa179 100%);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(40, 167, 69, 0.2);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        th, td {
            padding: 12px;
            text-align: right;
            border-bottom: 1px solid #ddd;
        }
        
        th {
            background: #667eea;
            color: white;
            font-weight: 600;
        }
        
        tr:hover { background: #f8f9fa; }
        
        .alert {
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            white-space: pre-line;
            animation: slideDown 0.3s ease;
        }
        
        @keyframes slideDown { from { transform: translateY(-10px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        
        .alert-success { background: #d4edda; color: #155724; border-left: 4px solid #28a745; }
        .alert-danger { background: #f8d7da; color: #721c24; border-left: 4px solid #dc3545; }
        .alert-warning { background: #fff3cd; color: #856404; border-left: 4px solid #ffc107; }
        
        .no-data {
            text-align: center;
            padding: 40px;
            color: #999;
            font-size: 1.1rem;
        }
        
        .ml-button {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .ml-button a {
            padding: 15px 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 10px;
            display: inline-block;
            font-weight: bold;
            transition: all 0.3s;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.2);
        }
        
        .ml-button a:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
        }
    </style>
</head>
<body>
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    <!-- أضف بعد قسم الإحصائيات -->
    <div style="display: flex; gap: 15px; margin: 20px 0;">
        <a href="/student/chatbot" style="flex: 1; padding: 15px; background: #667eea; 
        color: white; text-decoration: none; border-radius: 8px; text-align: center;">
            🤖 المساعد الذكي
        </a>
        <a href="/student/insights" style="flex: 1; padding: 15px; background: #764ba2; 
        color: white; text-decoration: none; border-radius: 8px; text-align: center;">
            📊 رؤى الأداء
        </a>
    </div>
    
        <div class="header">
            <h1>🎓 لوحة الطالب - {{ user_name }}</h1>
            <a href="/auth/logout" class="logout-btn">تسجيل الخروج</a>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">📊</div>
                <div class="stat-value">{{ "%.1f"|format(avg_score) }}%</div>
                <div class="stat-label">المعدل العام</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">✅</div>
                <div class="stat-value">{{ total_exams }}</div>
                <div class="stat-label">امتحانات مكتملة</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📝</div>
                <div class="stat-value">{{ available_exams|length if available_exams else 0 }}</div>
                <div class="stat-label">امتحانات متاحة</div>
            </div>
        </div>
        
        <div class="ml-button">
            <a href="/student/ml/analytics">🤖 التحليل الذكي للأداء</a>
        </div>
        
        <div class="nav-tabs">
            <button class="active" onclick="showTab(event, 'available')">الامتحانات المتاحة</button>
            <button onclick="showTab(event, 'completed')">الامتحانات المكتملة</button>
            <button onclick="showTab(event, 'grades')">الدرجات</button>
        </div>
        
        <div id="available" class="content-section active">
            <h2 style="margin-bottom: 20px;">📝 الامتحانات المتاحة</h2>
            {% if available_exams and available_exams|length > 0 %}
                {% for exam in available_exams %}
                <div class="exam-card">
                    <h3>{{ exam[1] }}</h3>
                    <div class="exam-info">
                        📅 الفصل: {{ exam[2] }} | السنة: {{ exam[3] }} | الدرجة الكلية: {{ exam[4] }}
                    </div>
                    <a href="/student/exam/{{ exam[0] }}" class="start-btn">ابدأ الامتحان ➜</a>
                </div>
                {% endfor %}
            {% else %}
                <div class="no-data">لا توجد امتحانات متاحة حالياً</div>
            {% endif %}
        </div>
        
        <div id="completed" class="content-section">
            <h2 style="margin-bottom: 20px;">✅ الامتحانات المكتملة</h2>
            {% if completed_exams and completed_exams|length > 0 %}
                <table>
                    <tr>
                        <th>المقرر</th>
                        <th>الدرجة</th>
                        <th>التقدير</th>
                        <th>تاريخ الامتحان</th>
                    </tr>
                    {% for exam in completed_exams %}
                    <tr>
                        <td>{{ exam[0] }}</td>
                        <td>{{ exam[1] if exam[1] is not none else 'قيد المراجعة' }}</td>
                        <td>{{ exam[2] if exam[2] else 'قيد المراجعة' }}</td>
                        <td>{{ exam[3].strftime('%Y-%m-%d %H:%M') if exam[3] else 'N/A' }}</td>
                    </tr>
                    {% endfor %}
                </table>
            {% else %}
                <div class="no-data">لم تقم بإجراء أي امتحان بعد</div>
            {% endif %}
        </div>
        
        <div id="grades" class="content-section">
            <h2 style="margin-bottom: 20px;">📈 الدرجات</h2>
            {% if grades and grades|length > 0 %}
                <table>
                    <tr>
                        <th>المقرر</th>
                        <th>الدرجة</th>
                        <th>التقدير</th>
                    </tr>
                    {% for exam in grades %}
                    <tr>
                        <td>{{ exam[0] }}</td>
                        <td>{{ exam[1] }}</td>
                        <td>{{ exam[2] if exam[2] else 'N/A' }}</td>
                    </tr>
                    {% endfor %}
                </table>
            {% else %}
                <div class="no-data">لا توجد درجات بعد</div>
            {% endif %}
        </div>
        <!-- أضف بعد قسم الإحصائيات -->
    <div style="display: flex; gap: 15px; margin: 20px 0;">
            <a href="/student/chatbot" style="flex: 1; padding: 15px; background: #667eea; 
            color: white; text-decoration: none; border-radius: 8px; text-align: center;">
                🤖 المساعد الذكي
            </a>
            <a href="/student/insights" style="flex: 1; padding: 15px; background: #764ba2; 
            color: white; text-decoration: none; border-radius: 8px; text-align: center;">
                📊 رؤى الأداء
            </a>
    </div>

    </div>
    
    <script>
        function showTab(event, tabName) {
            document.querySelectorAll('.content-section').forEach(section => section.classList.remove('active'));
            document.querySelectorAll('.nav-tabs button').forEach(btn => btn.classList.remove('active'));
            
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
'''

EXAM_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ exam[1] }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', 'Cairo', Tahoma, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container { max-width: 950px; margin: 0 auto; }
        
        .exam-header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .exam-header h1 { color: #333; margin-bottom: 10px; }
        .exam-info { color: #666; font-size: 0.95rem; }
        
        .question-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .question-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }
        
        .question-number {
            font-weight: bold;
            color: #667eea;
            font-size: 1.1rem;
        }
        
        .question-marks {
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
        }
        
        .question-type {
            display: inline-block;
            padding: 4px 12px;
            background: #e3f2fd;
            color: #1976d2;
            border-radius: 5px;
            font-size: 0.8rem;
            margin-bottom: 12px;
            font-weight: 600;
        }
        
        .question-text {
            font-size: 1.05rem;
            color: #333;
            margin-bottom: 20px;
            line-height: 1.7;
        }
        
        .choices {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .choice {
            display: flex;
            align-items: flex-start;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            border: 2px solid transparent;
        }
        
        .choice:hover {
            background: #e9ecef;
            border-color: #667eea;
            transform: translateX(-3px);
        }
        
        .choice input {
            margin-left: 15px;
            margin-top: 2px;
            cursor: pointer;
            width: 20px;
            height: 20px;
        }
        
        .choice label {
            cursor: pointer;
            width: 100%;
            font-size: 1rem;
        }
        
        textarea {
            width: 100%;
            padding: 15px;
            border-radius: 8px;
            border: 2px solid #ddd;
            font-family: inherit;
            font-size: 1rem;
            resize: vertical;
            min-height: 100px;
        }
        
        textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .submit-btn {
            padding: 15px 40px;
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.1rem;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            margin-top: 20px;
            transition: all 0.3s;
        }
        
        .submit-btn:hover {
            background: linear-gradient(135deg, #218838 0%, #1aa179 100%);
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(40, 167, 69, 0.2);
        }
        
        .no-choices-warning {
            background: #fff3cd;
            border: 1px solid #ffc107;
            color: #856404;
            padding: 12px 15px;
            border-radius: 8px;
            margin-top: 10px;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="exam-header">
            <h1>📝 {{ exam[1] }}</h1>
            <div class="exam-info">
                الفصل: {{ exam[3] }} | السنة: {{ exam[4] }} | الدرجة الكلية: {{ exam[5] }}
            </div>
        </div>
        
        <form method="POST" action="/student/exam/submit" id="examForm">
            {% for q in questions %}
            <div class="question-card">
                <div class="question-header">
                    <span class="question-number">السؤال {{ loop.index }}</span>
                    <span class="question-marks">{{ q[3] }} نقطة</span>
                </div>
                <span class="question-type">{{ q[2] }}</span>
                <div class="question-text">{{ q[1] }}</div>
                
                {% if q[2] and ('MCQ' in q[2]|upper or 'MULTIPLE' in q[2]|upper) %}
                    {% if q[0] in choices and choices[q[0]]|length > 0 %}
                        <div class="choices">
                            {% for choice in choices[q[0]] %}
                            <div class="choice">
                                <input 
                                    type="radio" 
                                    id="q{{ q[0] }}_c{{ choice[0] }}" 
                                    name="question_{{ q[0] }}" 
                                    value="{{ choice[0] }}"
                                    required
                                >
                                <label for="q{{ q[0] }}_c{{ choice[0] }}">{{ choice[1] }}</label>
                            </div>
                            {% endfor %}
                        </div>
                    {% else %}
                        <div class="no-choices-warning">
                            ⚠️ لا توجد اختيارات لهذا السؤال. يرجى إبلاغ المدرس.
                        </div>
                    {% endif %}
                {% elif q[2] and 'TRUE' in q[2]|upper %}
                    <div class="choices">
                        <div class="choice">
                            <input type="radio" id="q{{ q[0] }}_t" name="question_{{ q[0] }}" value="True" required>
                            <label for="q{{ q[0] }}_t">✓ صحيح</label>
                        </div>
                        <div class="choice">
                            <input type="radio" id="q{{ q[0] }}_f" name="question_{{ q[0] }}" value="False" required>
                            <label for="q{{ q[0] }}_f">✗ خطأ</label>
                        </div>
                    </div>
                {% else %}
                    <textarea 
                        name="question_{{ q[0] }}" 
                        placeholder="اكتب إجابتك هنا..."
                    ></textarea>
                {% endif %}
            </div>
            {% endfor %}
            
            <button type="submit" class="submit-btn" onclick="return confirm('هل أنت متأكد من تسليم الامتحان؟');">
                ✓ تسليم الامتحان
            </button>
        </form>
    </div>
    
    <script>
        let formSubmitted = false;
        document.getElementById('examForm').addEventListener('submit', function() {
            formSubmitted = true;
        });
        
        window.addEventListener('beforeunload', function(e) {
            if (!formSubmitted) {
                e.preventDefault();
                e.returnValue = '';
            }
        });
    </script>
</body>
</html>
'''
# ==================== CHATBOT TEMPLATE ====================

CHATBOT_TEMPLATE = '''
<!DOCTYPE html>
<html dir="rtl">
<head>
    <title>المساعد الذكي</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #f0f2f5; }
        .container { max-width: 900px; margin: 20px auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                  color: white; padding: 20px; border-radius: 10px 10px 0 0; }
        .chat-box { background: white; height: 500px; overflow-y: auto; 
                    padding: 20px; border-left: 1px solid #ddd; border-right: 1px solid #ddd; }
        .message { padding: 12px 16px; margin: 10px 0; border-radius: 18px; max-width: 70%; }
        .user-message { background: #667eea; color: white; margin-right: auto; text-align: right; }
        .bot-message { background: #e4e6eb; color: #050505; margin-left: auto; text-align: left; }
        .input-area { background: white; padding: 15px; border-radius: 0 0 10px 10px; 
                      border: 1px solid #ddd; display: flex; gap: 10px; }
        input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 20px; 
                font-size: 15px; }
        button { padding: 12px 30px; background: #667eea; color: white; border: none; 
                 border-radius: 20px; cursor: pointer; font-weight: bold; }
        button:hover { background: #5568d3; }
        .back-link { display: inline-block; color: #667eea; text-decoration: none; 
                     padding: 10px; margin-bottom: 10px; }
        .typing { color: #888; font-style: italic; padding: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/student/dashboard" class="back-link">← العودة للوحة التحكم</a>
        
        <div class="header">
            <h1>🤖 المساعد الذكي</h1>
            <p>مرحباً {{ username }}! اسألني أي سؤال عن دراستك</p>
        </div>
        
        <div class="chat-box" id="chatBox">
            <div class="bot-message">
                <strong>المساعد:</strong> مرحباً! أنا هنا لمساعدتك. يمكنك أن تسألني عن:
                <br>• نصائح للدراسة
                <br>• كيفية الاستعداد للامتحانات
                <br>• تحليل أدائك
                <br>• أي سؤال يخص دراستك!
            </div>
        </div>
        
        <div class="input-area">
            <input type="text" id="userInput" placeholder="اكتب سؤالك هنا..." 
                   onkeypress="if(event.key==='Enter') sendMessage()">
            <button onclick="sendMessage()">إرسال</button>
        </div>
    </div>
    
    <script>
        const chatBox = document.getElementById('chatBox');
        const userInput = document.getElementById('userInput');
        
        function sendMessage() {
            const message = userInput.value.trim();
            if (!message) return;
            
            // عرض رسالة المستخدم
            addMessage(message, 'user');
            userInput.value = '';
            
            // عرض typing indicator
            const typingDiv = document.createElement('div');
            typingDiv.className = 'typing';
            typingDiv.id = 'typing';
            typingDiv.textContent = 'المساعد يكتب...';
            chatBox.appendChild(typingDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
            
            // إرسال للسيرفر
            fetch('/student/chatbot/ask', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'message=' + encodeURIComponent(message)
            })
            .then(res => res.json())
            .then(data => {
                // إزالة typing indicator
                document.getElementById('typing').remove();
                
                if (data.status === 'success') {
                    addMessage(data.response, 'bot');
                } else {
                    addMessage('عذراً، حدث خطأ. حاول مرة أخرى.', 'bot');
                }
            })
            .catch(error => {
                document.getElementById('typing').remove();
                addMessage('عذراً، حدث خطأ في الاتصال.', 'bot');
            });
        }
        
        function addMessage(text, type) {
            const div = document.createElement('div');
            div.className = 'message ' + type + '-message';
            
            if (type === 'user') {
                div.innerHTML = '<strong>أنت:</strong> ' + text;
            } else {
                div.innerHTML = '<strong>المساعد:</strong> ' + text;
            }
            
            chatBox.appendChild(div);
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    </script>
</body>
</html>
'''

# ==================== INSIGHTS TEMPLATE ====================

INSIGHTS_TEMPLATE = '''
<!DOCTYPE html>
<html dir="rtl">
<head>
    <title>رؤى الأداء</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 20px auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                  color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; }
        .card { background: white; padding: 20px; border-radius: 8px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                      gap: 15px; margin-bottom: 30px; }
        .stat-box { background: white; padding: 20px; border-radius: 8px; text-align: center; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-value { font-size: 32px; font-weight: bold; color: #667eea; margin: 10px 0; }
        .stat-label { color: #666; font-size: 14px; }
        .level-badge { display: inline-block; padding: 10px 20px; border-radius: 20px; 
                       font-weight: bold; margin: 10px 0; }
        .level-excellent { background: #4caf50; color: white; }
        .level-good { background: #2196f3; color: white; }
        .level-average { background: #ff9800; color: white; }
        .level-poor { background: #f44336; color: white; }
        .recommendations { background: #fff3cd; padding: 15px; border-radius: 5px; 
                          border-left: 4px solid #ffc107; }
        .recommendation-item { padding: 8px 0; }
        .prediction-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                         color: white; padding: 20px; border-radius: 8px; text-align: center; }
        .back-link { color: #667eea; text-decoration: none; padding: 10px; display: inline-block; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/student/dashboard" class="back-link">← العودة</a>
        
        <div class="header">
            <h1>📊 رؤى الأداء المدعومة بالذكاء الاصطناعي</h1>
            <p>مرحباً {{ username }} - تحليل شامل لأدائك الدراسي</p>
        </div>
        
        {% if insights.status == 'success' %}
            <!-- الإحصائيات -->
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-label">عدد الامتحانات</div>
                    <div class="stat-value">{{ insights.statistics.total_exams }}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">المعدل</div>
                    <div class="stat-value">{{ insights.statistics.avg_score }}%</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">أعلى درجة</div>
                    <div class="stat-value">{{ insights.statistics.max_score }}%</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">أدنى درجة</div>
                    <div class="stat-value">{{ insights.statistics.min_score }}%</div>
                </div>
            </div>
            
            <!-- التحليل -->
            <div class="card">
                <h2>📈 تحليل الأداء</h2>
                <p>
                    <span class="level-badge level-good">
                        {{ insights.analysis.performance_level.emoji }} 
                        {{ insights.analysis.performance_level.level }}
                    </span>
                </p>
                <p style="margin: 15px 0; color: #666;">
                    {{ insights.analysis.performance_level.description }}
                </p>
                
                <h3 style="margin-top: 20px;">🎯 ثبات الأداء</h3>
                <p>{{ insights.analysis.consistency.description }}</p>
                
                <h3 style="margin-top: 20px;">{{ insights.analysis.trend.emoji }} الاتجاه</h3>
                <p>{{ insights.analysis.trend.description }}</p>
            </div>
            
            <!-- التوصيات -->
            <div class="card">
                <h2>💡 التوصيات</h2>
                <div class="recommendations">
                    {% for rec in insights.recommendations %}
                    <div class="recommendation-item">{{ rec }}</div>
                    {% endfor %}
                </div>
            </div>
        {% else %}
            <div class="card">
                <p>{{ insights.message }}</p>
            </div>
        {% endif %}
        
        <!-- التنبؤ -->
        {% if prediction.status == 'success' %}
        <div class="prediction-box">
            <h2>🔮 التنبؤ بالامتحان القادم</h2>
            <div style="font-size: 48px; margin: 20px 0;">
                {{ prediction.predicted_score }}%
            </div>
            <p>مستوى الثقة: {{ prediction.confidence }}%</p>
            <p style="margin-top: 10px;">{{ prediction.message }}</p>
        </div>
        {% endif %}
    </div>
</body>
</html>
'''
