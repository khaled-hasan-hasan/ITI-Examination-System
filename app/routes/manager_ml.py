# app/routes/manager_ml.py - FIXED VERSION

from flask import Blueprint, render_template_string, session, redirect, jsonify
import logging

logger = logging.getLogger(__name__)

manager_ml_bp = Blueprint('manager_ml', __name__, url_prefix='/manager/ml')

def require_manager(f=None):
    from functools import wraps
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or session.get('user_type') != 'manager':
                return redirect('/auth/login')
            return func(*args, **kwargs)
        return decorated_function
    
    if f is None:
        return decorator
    else:
        return decorator(f)

@manager_ml_bp.route('/dashboard')
@require_manager
def analytics_dashboard():
    try:
        username = session.get('username', 'Manager')
        from app.database import DatabaseConnection
        
        # Simple stats query - NO nested aggregates
        stats_query = """
        SELECT 
            COUNT(DISTINCT s.S_ID),
            ISNULL(COUNT(DISTINCT t.Takes_ID), 0),
            ISNULL(AVG(CAST(t.Score AS FLOAT)), 0),
            COUNT(DISTINCT e.Exam_ID)
        FROM Student s
        LEFT JOIN TAKES t ON s.S_ID = t.S_ID AND t.Score IS NOT NULL AND t.Score > 0
        LEFT JOIN Exam e ON t.Exam_ID = e.Exam_ID
        """
        stats = DatabaseConnection.fetch_one(stats_query)
        
        if stats and stats[0] and stats[0] > 0:
            total_students, total_exams_taken, avg_score, total_exams = stats
            
            # Simple performance count
            perf_query = """
            SELECT 
                SUM(CASE WHEN avg_score >= 90 THEN 1 ELSE 0 END),
                SUM(CASE WHEN avg_score >= 80 AND avg_score < 90 THEN 1 ELSE 0 END),
                SUM(CASE WHEN avg_score >= 70 AND avg_score < 80 THEN 1 ELSE 0 END),
                SUM(CASE WHEN avg_score >= 60 AND avg_score < 70 THEN 1 ELSE 0 END),
                SUM(CASE WHEN avg_score < 60 THEN 1 ELSE 0 END)
            FROM (
                SELECT s.S_ID, AVG(CAST(t.Score AS FLOAT)) as avg_score
                FROM Student s
                LEFT JOIN TAKES t ON s.S_ID = t.S_ID AND t.Score IS NOT NULL AND t.Score > 0
                GROUP BY s.S_ID
            ) x
            """
            perf = DatabaseConnection.fetch_one(perf_query) or (0,0,0,0,0)
            
            performance_dist = {
                'excellent': perf[0] or 0,
                'very_good': perf[1] or 0,
                'good': perf[2] or 0,
                'acceptable': perf[3] or 0,
                'needs_improvement': perf[4] or 0
            }
            
            # Top students
            top_query = """
            SELECT TOP 10 p.F_name, p.L_name, p.Email, AVG(CAST(t.Score AS FLOAT)), COUNT(t.Takes_ID)
            FROM Student s
            JOIN Person p ON s.Person_ID = p.ID
            LEFT JOIN TAKES t ON s.S_ID = t.S_ID AND t.Score IS NOT NULL AND t.Score > 0
            GROUP BY s.S_ID, p.F_name, p.L_name, p.Email
            ORDER BY AVG(CAST(t.Score AS FLOAT)) DESC
            """
            top_students = DatabaseConnection.fetch_all(top_query) or []
            
            return render_template_string(TEMPLATE,
                username=username,
                has_data=True,
                total_students=total_students,
                total_exams_taken=total_exams_taken,
                average_score=f"{float(avg_score):.1f}" if avg_score else "0",
                total_exams=total_exams,
                performance_dist=performance_dist,
                top_students=top_students
            )
        else:
            return render_template_string(TEMPLATE,
                username=username,
                has_data=False,
                message="No exam data available"
            )
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return render_template_string(TEMPLATE,
            username=session.get('username', 'Manager'),
            has_data=False,
            message=f"Error: {str(e)}"
        )

TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Analytics</title>
    <style>
        body { font-family: Arial; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
        .stat { background: #f9f9f9; padding: 15px; border-radius: 5px; text-align: center; }
        .stat h3 { color: #666; font-size: 12px; margin-bottom: 10px; }
        .stat-value { font-size: 28px; color: #667eea; font-weight: bold; }
        a { color: #667eea; text-decoration: none; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th { background: #f5f5f5; padding: 10px; text-align: left; }
        td { padding: 10px; border-bottom: 1px solid #eee; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/manager/dashboard">← Back</a>
        <div class="header">
            <h1>📊 Analytics</h1>
            <p>Welcome {{ username }}</p>
        </div>
        
        {% if has_data %}
            <div class="stats">
                <div class="stat">
                    <h3>Students</h3>
                    <div class="stat-value">{{ total_students }}</div>
                </div>
                <div class="stat">
                    <h3>Exams Taken</h3>
                    <div class="stat-value">{{ total_exams_taken }}</div>
                </div>
                <div class="stat">
                    <h3>Average</h3>
                    <div class="stat-value">{{ average_score }}%</div>
                </div>
                <div class="stat">
                    <h3>Total Exams</h3>
                    <div class="stat-value">{{ total_exams }}</div>
                </div>
            </div>
            
            <h3>Performance</h3>
            <table>
                <tr><td>Excellent (90+)</td><td><strong>{{ performance_dist.excellent }}</strong></td></tr>
                <tr><td>Very Good (80-89)</td><td><strong>{{ performance_dist.very_good }}</strong></td></tr>
                <tr><td>Good (70-79)</td><td><strong>{{ performance_dist.good }}</strong></td></tr>
                <tr><td>Acceptable (60-69)</td><td><strong>{{ performance_dist.acceptable }}</strong></td></tr>
                <tr><td>Needs Improvement (<60)</td><td><strong>{{ performance_dist.needs_improvement }}</strong></td></tr>
            </table>
            
            {% if top_students %}
            <h3 style="margin-top: 20px;">Top Students</h3>
            <table>
                <thead><tr><th>Name</th><th>Email</th><th>Avg</th><th>Exams</th></tr></thead>
                <tbody>
                {% for s in top_students %}
                <tr>
                    <td>{{ s[0] }} {{ s[1] }}</td>
                    <td>{{ s[2] }}</td>
                    <td><strong>{{ "%.1f"|format(s[3]) }}</strong></td>
                    <td>{{ s[4] }}</td>
                </tr>
                {% endfor %}
                </tbody>
            </table>
            {% endif %}
        {% else %}
            <div style="padding: 40px; text-align: center; color: #999;">
                <h2>📚 No Data</h2>
                <p>{{ message }}</p>
            </div>
        {% endif %}
    </div>
</body>
</html>
'''
