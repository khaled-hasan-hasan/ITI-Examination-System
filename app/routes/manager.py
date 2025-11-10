# app/routes/manager.py - FIXED FINAL VERSION
# All SQL queries use correct column names from your schema

from flask import Blueprint, render_template_string, session, redirect, request, flash
from app.database import DatabaseConnection
from functools import wraps
import logging

logger = logging.getLogger(__name__)

manager_bp = Blueprint('manager', __name__)

def require_manager(f):
    """Require manager login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'warning')
            return redirect('/auth/login')
        if session.get('user_type') != 'manager':
            flash('Access denied', 'danger')
            return redirect('/auth/login')
        return f(*args, **kwargs)
    return decorated_function

# ==================== ROUTES ====================

@manager_bp.route('/dashboard')
@require_manager
def manager_dashboard():
    """Manager dashboard - with correct queries"""
    try:
        username = session.get('username', 'Manager')
        
        logger.info(f"Manager dashboard loaded for {username}")
        
        # FIXED: Use correct column names from schema
        
        # Get students - CORRECT QUERY
        students_query = """
        SELECT s.S_ID, p.F_name, p.L_name, p.Email, s.Is_graduated
        FROM Student s
        JOIN Person p ON s.Person_ID = p.ID
        ORDER BY s.S_ID
        """
        students = DatabaseConnection.fetch_all(students_query) or []
        
        # Get instructors - CORRECT QUERY
        instructors_query = """
        SELECT i.I_ID, p.F_name, p.L_name, p.Email, i.Salary
        FROM Instructor i
        JOIN Person p ON i.Person_ID = p.ID
        ORDER BY i.I_ID
        """
        instructors = DatabaseConnection.fetch_all(instructors_query) or []
        
        # Get courses - CORRECT QUERY (no Credit_hours, no Subject columns)
        courses_query = """
        SELECT c.Course_ID, c.name, c.hours, t.name as topic
        FROM Course c
        LEFT JOIN Topic t ON c.Topic_ID = t.Topic_ID
        ORDER BY c.Course_ID
        """
        courses = DatabaseConnection.fetch_all(courses_query) or []
        
        # Get exams - CORRECT QUERY (no Time_Duration column)
        exams_query = """
        SELECT e.Exam_ID, c.name as course_name, e.Semester, e.year, e.Total_marks, e.Time
        FROM Exam e
        JOIN Course c ON e.Course_ID = c.Course_ID
        ORDER BY e.Exam_ID DESC
        """
        exams = DatabaseConnection.fetch_all(exams_query) or []
        
        # Calculate stats
        stats = {
            'total_students': len(students),
            'total_instructors': len(instructors),
            'total_courses': len(courses),
            'total_exams': len(exams),
            'active_students': len([s for s in students if not s[4]]),  # Is_graduated = False
            'total_marks': sum([e[4] for e in exams if len(e) > 4 and e[4]])
        }
        
        logger.info(f"✓ Dashboard stats: {stats['total_students']} students, {stats['total_courses']} courses, {stats['total_exams']} exams")
        
        return render_template_string(DASHBOARD_TEMPLATE,
            username=username,
            students=students,
            instructors=instructors,
            courses=courses,
            exams=exams,
            stats=stats
        )
    
    except Exception as e:
        logger.error(f"Manager Dashboard Error: {str(e)}")
        return render_template_string(ERROR_TEMPLATE, error=str(e))

@manager_bp.route('/students')
@require_manager
def view_students():
    """View all students"""
    try:
        query = """
        SELECT s.S_ID, p.F_name, p.L_name, p.Email, p.Gender, p.B_Date, s.Is_graduated
        FROM Student s
        JOIN Person p ON s.Person_ID = p.ID
        ORDER BY s.S_ID
        """
        students = DatabaseConnection.fetch_all(query) or []
        
        return render_template_string(STUDENTS_TEMPLATE,
            students=students
        )
    except Exception as e:
        logger.error(f"View Students Error: {str(e)}")
        flash('Error loading students', 'danger')
        return redirect('/manager/dashboard')

@manager_bp.route('/courses')
@require_manager
def view_courses():
    """View all courses"""
    try:
        query = """
        SELECT c.Course_ID, c.name, c.hours, d.Dept_name, t.name as topic
        FROM Course c
        LEFT JOIN Department d ON c.Dept_ID = d.Dept_ID
        LEFT JOIN Topic t ON c.Topic_ID = t.Topic_ID
        ORDER BY c.Course_ID
        """
        courses = DatabaseConnection.fetch_all(query) or []
        
        return render_template_string(COURSES_TEMPLATE,
            courses=courses
        )
    except Exception as e:
        logger.error(f"View Courses Error: {str(e)}")
        flash('Error loading courses', 'danger')
        return redirect('/manager/dashboard')

@manager_bp.route('/instructors')
@require_manager
def view_instructors():
    """View all instructors"""
    try:
        query = """
        SELECT i.I_ID, p.F_name, p.L_name, p.Email, p.Gender, i.Salary
        FROM Instructor i
        JOIN Person p ON i.Person_ID = p.ID
        ORDER BY i.I_ID
        """
        instructors = DatabaseConnection.fetch_all(query) or []
        
        return render_template_string(INSTRUCTORS_TEMPLATE,
            instructors=instructors
        )
    except Exception as e:
        logger.error(f"View Instructors Error: {str(e)}")
        flash('Error loading instructors', 'danger')
        return redirect('/manager/dashboard')

@manager_bp.route('/exams')
@require_manager
def view_exams():
    """View all exams"""
    try:
        query = """
        SELECT e.Exam_ID, c.name as course, e.Semester, e.year, e.Total_marks, 
               COUNT(eq.Quest_ID) as questions, e.Time
        FROM Exam e
        JOIN Course c ON e.Course_ID = c.Course_ID
        LEFT JOIN Exam_Question eq ON e.Exam_ID = eq.Exam_ID
        GROUP BY e.Exam_ID, c.name, e.Semester, e.year, e.Total_marks, e.Time
        ORDER BY e.Exam_ID DESC
        """
        exams = DatabaseConnection.fetch_all(query) or []
        
        return render_template_string(EXAMS_TEMPLATE,
            exams=exams
        )
    except Exception as e:
        logger.error(f"View Exams Error: {str(e)}")
        flash('Error loading exams', 'danger')
        return redirect('/manager/dashboard')

# ==================== TEMPLATES ====================

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html dir="ltr">
<head>
    <title>Manager Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; }
        .header h1 { margin-bottom: 10px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-card h3 { color: #666; font-size: 14px; margin-bottom: 10px; }
        .stat-value { font-size: 32px; font-weight: bold; color: #667eea; }
        .section { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .section h2 { color: #333; margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; }
        th { background: #f5f5f5; padding: 12px; text-align: left; font-weight: 600; color: #666; border-bottom: 1px solid #ddd; }
        td { padding: 12px; border-bottom: 1px solid #eee; }
        tr:hover { background: #fafafa; }
        a { color: #667eea; text-decoration: none; margin-right: 15px; display: inline-block; }
        a:hover { text-decoration: underline; }
        .nav { background: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .logout { float: right; color: #c00; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Manager Dashboard</h1>
            <p>Welcome {{ username }} - Comprehensive system management</p>
        </div>
        
        <div class="nav">
            <a href="/manager/students">📚 Students</a>
            <a href="/manager/courses">📖 Courses</a>
            <a href="/manager/instructors">👨‍🏫 Instructors</a>
            <a href="/manager/exams">📝 Exams</a>
            <a href="/manager/ml/dashboard">📊 Analytics</a>
            <a href="/auth/logout" class="logout">Logout</a>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>Total Students</h3>
                <div class="stat-value">{{ stats.total_students }}</div>
            </div>
            <div class="stat-card">
                <h3>Total Courses</h3>
                <div class="stat-value">{{ stats.total_courses }}</div>
            </div>
            <div class="stat-card">
                <h3>Total Instructors</h3>
                <div class="stat-value">{{ stats.total_instructors }}</div>
            </div>
            <div class="stat-card">
                <h3>Total Exams</h3>
                <div class="stat-value">{{ stats.total_exams }}</div>
            </div>
            <div class="stat-card">
                <h3>Active Students</h3>
                <div class="stat-value">{{ stats.active_students }}</div>
            </div>
            <div class="stat-card">
                <h3>Total Marks</h3>
                <div class="stat-value">{{ stats.total_marks }}</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📚 Recent Exams</h2>
            {% if exams %}
            <table>
                <thead>
                    <tr>
                        <th>Exam ID</th>
                        <th>Course</th>
                        <th>Semester</th>
                        <th>Year</th>
                        <th>Total Marks</th>
                        <th>Time</th>
                    </tr>
                </thead>
                <tbody>
                    {% for exam in exams[:10] %}
                    <tr>
                        <td>#{{ exam[0] }}</td>
                        <td>{{ exam[1] }}</td>
                        <td>{{ exam[2] }}</td>
                        <td>{{ exam[3] }}</td>
                        <td>{{ exam[4] }}</td>
                        <td>{{ exam[5] }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p>No exams found.</p>
            {% endif %}
        </div>
        
        <div class="section">
            <h2>👥 Recent Students</h2>
            {% if students %}
            <table>
                <thead>
                    <tr>
                        <th>Student ID</th>
                        <th>First Name</th>
                        <th>Last Name</th>
                        <th>Email</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for student in students[:10] %}
                    <tr>
                        <td>#{{ student[0] }}</td>
                        <td>{{ student[1] }}</td>
                        <td>{{ student[2] }}</td>
                        <td>{{ student[3] }}</td>
                        <td>{% if student[4] %}Graduated{% else %}Active{% endif %}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p>No students found.</p>
            {% endif %}
        </div>
        
        <div class="section">
            <h2>📖 Recent Courses</h2>
            {% if courses %}
            <table>
                <thead>
                    <tr>
                        <th>Course ID</th>
                        <th>Name</th>
                        <th>Hours</th>
                        <th>Topic</th>
                    </tr>
                </thead>
                <tbody>
                    {% for course in courses[:10] %}
                    <tr>
                        <td>#{{ course[0] }}</td>
                        <td>{{ course[1] }}</td>
                        <td>{{ course[2] }}</td>
                        <td>{{ course[3] or '-' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p>No courses found.</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''

STUDENTS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Students</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f5f5f5; font-weight: 600; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>📚 All Students</h1>
    <a href="/manager/dashboard">← Back to Dashboard</a>
    <br><br>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>First Name</th>
                <th>Last Name</th>
                <th>Email</th>
                <th>Gender</th>
                <th>Birth Date</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for s in students %}
            <tr>
                <td>{{ s[0] }}</td>
                <td>{{ s[1] }}</td>
                <td>{{ s[2] }}</td>
                <td>{{ s[3] }}</td>
                <td>{{ s[4] or '-' }}</td>
                <td>{{ s[5] or '-' }}</td>
                <td>{% if s[6] %}Graduated{% else %}Active{% endif %}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
'''

COURSES_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Courses</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f5f5f5; font-weight: 600; }
        a { color: #0066cc; text-decoration: none; }
    </style>
</head>
<body>
    <h1>📖 All Courses</h1>
    <a href="/manager/dashboard">← Back to Dashboard</a>
    <br><br>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Hours</th>
                <th>Department</th>
                <th>Topic</th>
            </tr>
        </thead>
        <tbody>
            {% for c in courses %}
            <tr>
                <td>{{ c[0] }}</td>
                <td>{{ c[1] }}</td>
                <td>{{ c[2] }}</td>
                <td>{{ c[3] or '-' }}</td>
                <td>{{ c[4] or '-' }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
'''

INSTRUCTORS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Instructors</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f5f5f5; font-weight: 600; }
        a { color: #0066cc; text-decoration: none; }
    </style>
</head>
<body>
    <h1>👨‍🏫 All Instructors</h1>
    <a href="/manager/dashboard">← Back to Dashboard</a>
    <br><br>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>First Name</th>
                <th>Last Name</th>
                <th>Email</th>
                <th>Gender</th>
                <th>Salary</th>
            </tr>
        </thead>
        <tbody>
            {% for i in instructors %}
            <tr>
                <td>{{ i[0] }}</td>
                <td>{{ i[1] }}</td>
                <td>{{ i[2] }}</td>
                <td>{{ i[3] }}</td>
                <td>{{ i[4] or '-' }}</td>
                <td>{{ i[5] or '-' }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
'''

EXAMS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Exams</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f5f5f5; font-weight: 600; }
        a { color: #0066cc; text-decoration: none; }
    </style>
</head>
<body>
    <h1>📝 All Exams</h1>
    <a href="/manager/dashboard">← Back to Dashboard</a>
    <br><br>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Course</th>
                <th>Semester</th>
                <th>Year</th>
                <th>Total Marks</th>
                <th>Questions</th>
                <th>Time</th>
            </tr>
        </thead>
        <tbody>
            {% for e in exams %}
            <tr>
                <td>{{ e[0] }}</td>
                <td>{{ e[1] }}</td>
                <td>{{ e[2] }}</td>
                <td>{{ e[3] }}</td>
                <td>{{ e[4] }}</td>
                <td>{{ e[5] }}</td>
                <td>{{ e[6] or '-' }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
'''

ERROR_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Error</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .error { color: red; background: #f0f0f0; padding: 20px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>❌ Error</h1>
    <div class="error">
        <p>An error occurred while loading the dashboard:</p>
        <p><code>{{ error }}</code></p>
    </div>
    <a href="/manager/dashboard">← Try Again</a>
</body>
</html>
'''
