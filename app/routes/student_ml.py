# app/routes/student_ml.py - FIXED VERSION
# Handles missing data gracefully, shows useful messages

from flask import Blueprint, render_template_string, session, redirect, jsonify
import logging
import traceback
import json

logger = logging.getLogger(__name__)

student_ml_bp = Blueprint('student_ml', __name__, url_prefix='/student/ml')

def require_student(f=None):
    """Decorator to require student login"""
    from functools import wraps
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or session.get('user_type') != 'Student':
                return redirect('/auth/login')
            return func(*args, **kwargs)
        return decorated_function
    
    if f is None:
        return decorator
    else:
        return decorator(f)

# ==================== ANALYTICS DASHBOARD ====================

@student_ml_bp.route('/analytics')
@require_student
def analytics_dashboard():
    """ML-powered analytics dashboard"""
    try:
        student_id = session.get('student_id')
        username = session.get('username', 'Student')
        
        logger.info(f"ML Analytics requested for student {student_id}")
        
        # Get data from database directly
        from app.models import Student
        from app.database import DatabaseConnection
        
        # Get student performance data
        query = """
        SELECT COUNT(*) as exam_count, AVG(Score) as avg_score, MAX(Score) as max_score, MIN(Score) as min_score
        FROM TAKES
        WHERE S_ID = ? AND Score IS NOT NULL AND Score > 0
        """
        result = DatabaseConnection.fetch_one(query, (student_id,))
        
        if result and result[0] > 0:  # Has exam data
            exam_count, avg_score, max_score, min_score = result
            
            # Get detailed exam history
            exam_history_query = """
            SELECT TOP 10
                c.name as course,
                e.Total_marks,
                t.Score,
                t.Grade,
                t.Date_Taken
            FROM TAKES t
            JOIN Exam e ON t.Exam_ID = e.Exam_ID
            JOIN Course c ON e.Course_ID = c.Course_ID
            WHERE t.S_ID = ? AND t.Score IS NOT NULL
            ORDER BY t.Date_Taken DESC
            """
            exam_history = DatabaseConnection.fetch_all(exam_history_query, (student_id,)) or []
            
            performance_summary = {
                'exam_count': exam_count,
                'avg_score': float(avg_score) if avg_score else 0,
                'max_score': float(max_score) if max_score else 0,
                'min_score': float(min_score) if min_score else 0,
                'status': 'Data Available',
                'trend': 'Calculating...'
            }
            
            # Calculate performance percentage
            percentage = float(avg_score) if avg_score else 0
            if percentage >= 90:
                performance_level = 'Excellent'
            elif percentage >= 80:
                performance_level = 'Very Good'
            elif percentage >= 70:
                performance_level = 'Good'
            elif percentage >= 60:
                performance_level = 'Acceptable'
            else:
                performance_level = 'Needs Improvement'
            
            logger.info(f"✓ Found {exam_count} exams for student {student_id}")
            
            return render_template_string(ML_ANALYTICS_TEMPLATE,
                username=username,
                has_data=True,
                exam_count=exam_count,
                avg_score=f"{avg_score:.1f}" if avg_score else "0",
                max_score=f"{max_score:.1f}" if max_score else "0",
                min_score=f"{min_score:.1f}" if min_score else "0",
                performance_level=performance_level,
                exam_history=exam_history
            )
        else:
            # No exam data yet
            logger.info(f"No exam data for student {student_id} - showing prompt")
            return render_template_string(ML_ANALYTICS_TEMPLATE,
                username=username,
                has_data=False,
                exam_count=0,
                message="You haven't taken any exams yet. Take an exam to see your performance analysis!"
            )
    
    except Exception as e:
        logger.error(f"ML Analytics error: {str(e)}\n{traceback.format_exc()}")
        return render_template_string(ML_ANALYTICS_TEMPLATE,
            username=session.get('username', 'Student'),
            has_data=False,
            message=f"Error loading analytics: {str(e)}"
        )

# ==================== API ENDPOINTS ====================

@student_ml_bp.route('/api/performance')
@require_student
def api_performance():
    """API: Get performance summary"""
    try:
        student_id = session.get('student_id')
        from app.database import DatabaseConnection
        
        query = """
        SELECT COUNT(*) as exams, AVG(Score) as avg, MAX(Score) as max, MIN(Score) as min
        FROM TAKES WHERE S_ID = ? AND Score IS NOT NULL AND Score > 0
        """
        result = DatabaseConnection.fetch_one(query, (student_id,))
        
        if result and result[0] > 0:
            return jsonify({
                'exams_taken': result[0],
                'average_score': float(result[1]) if result[1] else 0,
                'max_score': float(result[2]) if result[2] else 0,
                'min_score': float(result[3]) if result[3] else 0,
                'status': 'success'
            })
        else:
            return jsonify({
                'status': 'no_data',
                'message': 'Take an exam to see performance data'
            })
    except Exception as e:
        logger.error(f"API performance error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@student_ml_bp.route('/api/trend')
@require_student
def api_trend():
    """API: Get performance trend"""
    try:
        student_id = session.get('student_id')
        from app.database import DatabaseConnection
        
        query = """
        SELECT TOP 20
            t.Date_Taken,
            t.Score,
            e.Total_marks,
            CAST(t.Score * 100.0 / e.Total_marks AS DECIMAL(5,2)) as percentage
        FROM TAKES t
        JOIN Exam e ON t.Exam_ID = e.Exam_ID
        WHERE t.S_ID = ? AND t.Score IS NOT NULL
        ORDER BY t.Date_Taken ASC
        """
        results = DatabaseConnection.fetch_all(query, (student_id,)) or []
        
        trend_data = [
            {
                'date': str(r[0]) if r[0] else '',
                'score': float(r[1]) if r[1] else 0,
                'percentage': float(r[3]) if r[3] else 0
            }
            for r in results
        ]
        
        return jsonify({'trend': trend_data, 'status': 'success'})
    except Exception as e:
        logger.error(f"API trend error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================== TEMPLATE ====================

ML_ANALYTICS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Performance Analytics</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; }
        .header h1 { margin-bottom: 10px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-card h3 { color: #666; font-size: 14px; margin-bottom: 10px; }
        .stat-value { font-size: 32px; font-weight: bold; color: #667eea; }
        .no-data { background: white; padding: 40px; border-radius: 8px; text-align: center; color: #999; }
        .no-data h2 { color: #666; margin-bottom: 10px; }
        .exam-table { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; }
        th { background: #f5f5f5; padding: 15px; text-align: left; font-weight: 600; color: #666; border-bottom: 1px solid #ddd; }
        td { padding: 15px; border-bottom: 1px solid #eee; }
        tr:hover { background: #fafafa; }
        .back-link { color: #667eea; text-decoration: none; display: inline-block; margin-bottom: 20px; }
        .back-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/student/dashboard" class="back-link">← Back to Dashboard</a>
        
        <div class="header">
            <h1>📊 Your Performance Analytics</h1>
            <p>Welcome {{ username }} - Comprehensive analysis of your exam performance</p>
        </div>
        
        {% if has_data %}
            <div class="stats">
                <div class="stat-card">
                    <h3>Exams Completed</h3>
                    <div class="stat-value">{{ exam_count }}</div>
                </div>
                <div class="stat-card">
                    <h3>Average Score</h3>
                    <div class="stat-value">{{ avg_score }}%</div>
                </div>
                <div class="stat-card">
                    <h3>Highest Score</h3>
                    <div class="stat-value">{{ max_score }}%</div>
                </div>
                <div class="stat-card">
                    <h3>Lowest Score</h3>
                    <div class="stat-value">{{ min_score }}%</div>
                </div>
                <div class="stat-card">
                    <h3>Performance Level</h3>
                    <div class="stat-value">{{ performance_level }}</div>
                </div>
            </div>
            
            {% if exam_history %}
            <h2 style="margin: 30px 0 20px 0;">Recent Exams</h2>
            <div class="exam-table">
                <table>
                    <thead>
                        <tr>
                            <th>Course</th>
                            <th>Total Marks</th>
                            <th>Your Score</th>
                            <th>Grade</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for exam in exam_history %}
                        <tr>
                            <td>{{ exam[0] }}</td>
                            <td>{{ exam[1] }}</td>
                            <td><strong>{{ exam[2] }}</strong></td>
                            <td>{{ exam[3] if exam[3] else 'Pending' }}</td>
                            <td>{{ exam[4].strftime('%Y-%m-%d %H:%M') if exam[4] else 'N/A' }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endif %}
        {% else %}
            <div class="no-data">
                <h2>📚 No Data Available Yet</h2>
                <p>{{ message }}</p>
                <p style="margin-top: 20px; color: #999;">
                    After you take an exam, detailed analytics and insights will appear here!
                </p>
                <a href="/student/dashboard" style="display: inline-block; margin-top: 20px; padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 4px;">Go Take an Exam</a>
            </div>
        {% endif %}
    </div>
</body>
</html>
'''
