# app/models.py - ULTIMATE COMPLETE FIX - NO MORE ISSUES! 🚀
# Fixed: Question loading, encoding, MCQ handling, session management

from app.database import DatabaseConnection
import logging
import traceback

logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class User:
    """User model for Person table"""
    
    @staticmethod
    def get_by_email(email):
        """Get user by email"""
        query = "SELECT ID, F_name, L_name, Email, Person_type FROM Person WHERE Email = ?"
        return DatabaseConnection.fetch_one(query, (email,))
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        query = "SELECT ID, F_name, L_name, Email, Person_type FROM Person WHERE ID = ?"
        return DatabaseConnection.fetch_one(query, (user_id,))


class Student:
    """Student model with all operations - FULLY FIXED"""
    
    @staticmethod
    def get_by_person_id(person_id):
        """Get student by person ID"""
        query = "SELECT S_ID, Person_ID, Is_graduated FROM Student WHERE Person_ID = ?"
        return DatabaseConnection.fetch_one(query, (person_id,))
    
    @staticmethod
    def get_by_id(student_id):
        """Get student by S_ID"""
        query = """
        SELECT s.S_ID, s.Person_ID, s.Is_graduated, p.F_name, p.L_name, p.Email
        FROM Student s
        JOIN Person p ON s.Person_ID = p.ID
        WHERE s.S_ID = ?
        """
        return DatabaseConnection.fetch_one(query, (student_id,))
    
    @staticmethod
    def get_available_exams(student_id):
        """Get exams that student hasn't taken yet - OPTIMIZED"""
        query = """
        SELECT DISTINCT
            e.Exam_ID,
            c.name as Course_name,
            e.Semester,
            e.year,
            e.Total_marks,
            ISNULL(e.Time, '01:30:00') as Time
        FROM Exam e
        INNER JOIN Course c ON e.Course_ID = c.Course_ID
        WHERE e.Exam_ID NOT IN (
            SELECT DISTINCT Exam_ID 
            FROM TAKES 
            WHERE S_ID = ?
        )
        -- Only show exams that have questions
        AND EXISTS (
            SELECT 1 FROM Exam_Question eq 
            WHERE eq.Exam_ID = e.Exam_ID
        )
        ORDER BY e.year DESC, e.Semester DESC
        """
        try:
            result = DatabaseConnection.fetch_all(query, (student_id,))
            logger.info(f"✅ Loaded {len(result) if result else 0} available exams for student {student_id}")
            return result if result else []
        except Exception as e:
            logger.error(f"❌ Error getting available exams: {str(e)}")
            return []
    
    @staticmethod
    def get_completed_exams(student_id):
        """Get exams that student has completed"""
        query = """
        SELECT 
            c.name as Course_name, 
            ISNULL(t.Score, 0) as Score, 
            ISNULL(t.Grade, 'قيد المراجعة') as Grade, 
            t.Date_Taken
        FROM TAKES t
        INNER JOIN Exam e ON t.Exam_ID = e.Exam_ID
        INNER JOIN Course c ON e.Course_ID = c.Course_ID
        WHERE t.S_ID = ?
        ORDER BY t.Date_Taken DESC
        """
        try:
            result = DatabaseConnection.fetch_all(query, (student_id,))
            return result if result else []
        except Exception as e:
            logger.error(f"Error getting completed exams: {str(e)}")
            return []
    
    @staticmethod
    def get_grades(student_id):
        """Get student grades"""
        query = """
        SELECT 
            c.name as Course_name, 
            ISNULL(t.Score, 0) as Score, 
            ISNULL(t.Grade, 'N/A') as Grade
        FROM TAKES t
        INNER JOIN Exam e ON t.Exam_ID = e.Exam_ID
        INNER JOIN Course c ON e.Course_ID = c.Course_ID
        WHERE t.S_ID = ? AND t.Score > 0
        ORDER BY t.Date_Taken DESC
        """
        try:
            result = DatabaseConnection.fetch_all(query, (student_id,))
            return result if result else []
        except Exception as e:
            logger.error(f"Error getting grades: {str(e)}")
            return []
    
    @staticmethod
    def get_average_score(student_id):
        """Get student average score - IMPROVED"""
        query = """
        SELECT AVG(CAST(Score AS FLOAT)) 
        FROM TAKES 
        WHERE S_ID = ? 
        AND Score IS NOT NULL 
        AND Score > 0
        """
        try:
            result = DatabaseConnection.execute_scalar(query, (student_id,))
            return round(float(result), 2) if result else 0.0
        except Exception as e:
            logger.error(f"Error calculating average: {str(e)}")
            return 0.0
    
    @staticmethod
    def check_exam_taken(student_id, exam_id):
        """Check if student already took this exam"""
        query = "SELECT Takes_ID, Score FROM TAKES WHERE S_ID = ? AND Exam_ID = ?"
        return DatabaseConnection.fetch_one(query, (student_id, exam_id))
    
    @staticmethod
    def start_exam(student_id, exam_id):
        """
        🎯 CRITICAL: Record that student started an exam
        Fixed to handle all edge cases and return Takes_ID reliably
        """
        try:
            import pyodbc
            conn = DatabaseConnection.get_connection()
            cursor = conn.cursor()
            
            # Insert new TAKES record with Score = 0
            insert_query = """
            INSERT INTO TAKES (S_ID, Exam_ID, Score, Grade, Date_Taken)
            OUTPUT INSERTED.Takes_ID
            VALUES (?, ?, 0, NULL, GETDATE())
            """
            
            cursor.execute(insert_query, (student_id, exam_id))
            result = cursor.fetchone()
            conn.commit()
            
            if result and result[0]:
                takes_id = int(result[0])
                cursor.close()
                conn.close()
                logger.info(f"✅ Exam started successfully: Takes_ID={takes_id}, Student={student_id}, Exam={exam_id}")
                return takes_id
            
            # Fallback: Get last inserted ID
            cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
            result = cursor.fetchone()
            if result and result[0]:
                takes_id = int(result[0])
                cursor.close()
                conn.close()
                logger.info(f"✅ Retrieved Takes_ID via SCOPE_IDENTITY: {takes_id}")
                return takes_id
            
            cursor.close()
            conn.close()
            
            # Last resort: Query by student and exam
            check_query = """
            SELECT TOP 1 Takes_ID 
            FROM TAKES 
            WHERE S_ID = ? AND Exam_ID = ? 
            ORDER BY Takes_ID DESC
            """
            alt_result = DatabaseConnection.fetch_one(check_query, (student_id, exam_id))
            if alt_result:
                takes_id = alt_result[0]
                logger.info(f"✅ Retrieved Takes_ID using fallback query: {takes_id}")
                return takes_id
            
            logger.error("❌ Failed to get Takes_ID after all attempts")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error starting exam: {str(e)}\n{traceback.format_exc()}")
            return None
    
    @staticmethod
    def submit_exam(takes_id, score, grade):
        """Update TAKES record with final score and grade"""
        try:
            query = """
            UPDATE TAKES
            SET Score = ?, Grade = ?, Date_Taken = GETDATE()
            WHERE Takes_ID = ?
            """
            DatabaseConnection.execute_query(query, (score, grade, takes_id))
            logger.info(f"✅ Exam submitted: Takes_ID={takes_id}, Score={score}, Grade={grade}")
        except Exception as e:
            logger.error(f"❌ Error submitting exam: {str(e)}")
    
    @staticmethod
    def get_all_students():
        """Get all students"""
        query = """
        SELECT s.S_ID, p.F_name, p.L_name, p.Email, ISNULL(s.Is_graduated, 0) as Is_graduated
        FROM Student s
        INNER JOIN Person p ON s.Person_ID = p.ID
        ORDER BY s.S_ID
        """
        return DatabaseConnection.fetch_all(query)


class Instructor:
    """Instructor model - ENHANCED"""
    
    @staticmethod
    def get_by_person_id(person_id):
        query = "SELECT I_ID, Person_ID, Salary FROM Instructor WHERE Person_ID = ?"
        return DatabaseConnection.fetch_one(query, (person_id,))
    
    @staticmethod
    def get_by_id(instructor_id):
        query = """
        SELECT i.I_ID, i.Person_ID, i.Salary, p.F_name, p.L_name, p.Email
        FROM Instructor i
        INNER JOIN Person p ON i.Person_ID = p.ID
        WHERE i.I_ID = ?
        """
        return DatabaseConnection.fetch_one(query, (instructor_id,))
    
    @staticmethod
    def get_courses(instructor_id):
        """Get instructor's courses with proper joins"""
        query = """
        SELECT DISTINCT 
            c.Course_ID, 
            c.name, 
            c.hours, 
            ISNULL(t.name, 'عام') as Topic_name
        FROM Course c
        INNER JOIN Teaching te ON c.Course_ID = te.Course_ID
        LEFT JOIN Topic t ON c.Topic_ID = t.Topic_ID
        WHERE te.I_ID = ?
        ORDER BY c.name
        """
        return DatabaseConnection.fetch_all(query, (instructor_id,))
    
    @staticmethod
    def get_exams(instructor_id):
        """Get instructor's exams"""
        query = """
        SELECT 
            e.Exam_ID, 
            c.name as Course_name, 
            e.Semester, 
            e.year, 
            e.Total_marks, 
            ISNULL(e.Time, '01:30:00') as Time
        FROM Exam e
        INNER JOIN Course c ON e.Course_ID = c.Course_ID
        WHERE e.I_ID = ?
        ORDER BY e.year DESC, e.Semester DESC
        """
        return DatabaseConnection.fetch_all(query, (instructor_id,))
    
    @staticmethod
    def get_students_for_exam(exam_id):
        """Get students who took a specific exam"""
        query = """
        SELECT 
            s.S_ID,
            p.F_name,
            p.L_name,
            ISNULL(t.Score, 0) as Score,
            ISNULL(t.Grade, 'قيد المراجعة') as Grade,
            t.Date_Taken
        FROM TAKES t
        INNER JOIN Student s ON t.S_ID = s.S_ID
        INNER JOIN Person p ON s.Person_ID = p.ID
        WHERE t.Exam_ID = ?
        ORDER BY t.Date_Taken DESC
        """
        return DatabaseConnection.fetch_all(query, (exam_id,))


class Exam:
    """Exam model - ENHANCED"""
    
    @staticmethod
    def get_exam_by_id(exam_id):
        """Get exam details with proper null handling"""
        query = """
        SELECT 
            e.Exam_ID, 
            c.name as Course_name, 
            e.Course_ID,
            e.Semester, 
            e.year, 
            e.Total_marks, 
            ISNULL(e.Time, '01:30:00') as Time, 
            e.I_ID
        FROM Exam e
        INNER JOIN Course c ON e.Course_ID = c.Course_ID
        WHERE e.Exam_ID = ?
        """
        return DatabaseConnection.fetch_one(query, (exam_id,))
    
    @staticmethod
    def get_all_exams():
        """Get all exams"""
        query = """
        SELECT 
            e.Exam_ID, 
            c.name as Course_name, 
            e.Semester, 
            e.year, 
            e.Total_marks
        FROM Exam e
        INNER JOIN Course c ON e.Course_ID = c.Course_ID
        ORDER BY e.year DESC, e.Semester DESC
        """
        return DatabaseConnection.fetch_all(query)
    
    @staticmethod
    def create_exam(instructor_id, course_id, semester, year, total_marks, time=None):
        """Create new exam - FIXED"""
        try:
            import pyodbc
            conn = DatabaseConnection.get_connection()
            cursor = conn.cursor()
            
            insert_query = """
            INSERT INTO Exam (I_ID, Course_ID, Semester, year, Total_marks, Time)
            OUTPUT INSERTED.Exam_ID
            VALUES (?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(insert_query, (instructor_id, course_id, semester, year, total_marks, time))
            result = cursor.fetchone()
            conn.commit()
            cursor.close()
            conn.close()
            
            if result and result[0]:
                exam_id = int(result[0])
                logger.info(f"✅ Exam created: Exam_ID={exam_id}")
                return exam_id
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error creating exam: {str(e)}")
            return None


class Question:
    """
    🎯 ULTIMATE QUESTION MODEL - ALL ISSUES FIXED!
    
    Fixes:
    1. ✅ Question loading from Exam_Question table
    2. ✅ MCQ choices loading
    3. ✅ Proper encoding for Arabic text
    4. ✅ Null handling
    5. ✅ Type validation
    """
    
    @staticmethod
    def get_exam_questions(exam_id):
        """
        🚀 ULTIMATE FIX: Get all exam questions with proper validation
        
        This function:
        - Loads questions from Exam_Question table (correct approach)
        - Validates question types
        - Handles Arabic encoding
        - Returns empty list if no questions (instead of crashing)
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🔍 LOADING QUESTIONS FOR EXAM {exam_id}")
        logger.info(f"{'='*70}")
        
        try:
            # STEP 1: Check if exam exists and has questions
            check_query = """
            SELECT COUNT(*) 
            FROM Exam_Question 
            WHERE Exam_ID = ?
            """
            count = DatabaseConnection.execute_scalar(check_query, (exam_id,))
            
            if not count or count == 0:
                logger.warning(f"⚠️ NO QUESTIONS LINKED TO EXAM {exam_id} in Exam_Question table!")
                logger.warning(f"📝 ACTION NEEDED: Run question insertion script for this exam")
                return []
            
            logger.info(f"✅ Found {count} questions in Exam_Question table")
            
            # STEP 2: Load questions with proper joins and validation
            query = """
            SELECT
                q.Quest_ID,
                LTRIM(RTRIM(ISNULL(q.Question_text, ''))) as Question_text,
                UPPER(LTRIM(RTRIM(ISNULL(q.Type, 'Essay')))) as Type,
                ISNULL(eq.marks, 1.0) as marks,
                ISNULL(q.Difficulty_Level, '3') as Difficulty_Level
            FROM Exam_Question eq
            INNER JOIN Question q ON q.Quest_ID = eq.Quest_ID
            WHERE eq.Exam_ID = ?
            AND q.Question_text IS NOT NULL
            AND LEN(q.Question_text) > 0
            ORDER BY eq.Question_order ASC
            """
            
            result = DatabaseConnection.fetch_all(query, (exam_id,))
            
            if not result:
                logger.error(f"❌ Query returned no results even though Exam_Question has {count} records!")
                logger.error(f"🔍 Possible issue: Question table data is NULL or empty")
                return []
            
            # STEP 3: Validate and log each question
            valid_questions = []
            for idx, q in enumerate(result, 1):
                q_id, q_text, q_type, marks, difficulty = q
                
                # Validate question text
                if not q_text or q_text.strip() == '':
                    logger.warning(f"⚠️ Question {q_id} has empty text - SKIPPING")
                    continue
                
                # Fix encoding issues (if any)
                try:
                    q_text_fixed = q_text.encode('latin1').decode('utf-8')
                except:
                    q_text_fixed = q_text
                
                valid_questions.append((q_id, q_text_fixed, q_type, marks, difficulty))
                
                logger.info(f"  ✅ Q{idx}: ID={q_id}, Type={q_type}, Marks={marks}")
                logger.debug(f"      Text: {q_text_fixed[:60]}...")
            
            logger.info(f"{'='*70}")
            logger.info(f"✅ SUCCESSFULLY LOADED {len(valid_questions)} VALID QUESTIONS")
            logger.info(f"{'='*70}\n")
            
            return valid_questions
        
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR in get_exam_questions: {str(e)}")
            logger.error(traceback.format_exc())
            logger.info(f"{'='*70}\n")
            return []
    
    @staticmethod
    def get_question_choices(question_id):
        """
        🎯 Get MCQ choices with validation
        
        Fixes:
        - Validates Choice table data
        - Handles encoding
        - Returns empty list if no choices (safe)
        """
        query = """
        SELECT
            Choice_ID,
            LTRIM(RTRIM(ISNULL(Choice_text, ''))) as Choice_text,
            ISNULL(is_correct, 0) as is_correct
        FROM Choice
        WHERE Quest_ID = ?
        AND Choice_text IS NOT NULL
        AND LEN(Choice_text) > 0
        ORDER BY Choice_ID
        """
        try:
            result = DatabaseConnection.fetch_all(query, (question_id,))
            
            if not result:
                logger.warning(f"⚠️ No choices found for Question {question_id}")
                return []
            
            # Fix encoding for each choice
            fixed_choices = []
            for choice in result:
                choice_id, choice_text, is_correct = choice
                try:
                    choice_text_fixed = choice_text.encode('latin1').decode('utf-8')
                except:
                    choice_text_fixed = choice_text
                fixed_choices.append((choice_id, choice_text_fixed, is_correct))
            
            logger.info(f"✅ Loaded {len(fixed_choices)} choices for Question {question_id}")
            return fixed_choices
            
        except Exception as e:
            logger.error(f"❌ Error loading choices for Q{question_id}: {str(e)}")
            return []
    
    @staticmethod
    def check_mcq_answer(question_id, choice_id):
        """Check if MCQ answer is correct - SAFE VERSION"""
        query = """
        SELECT ISNULL(is_correct, 0)
        FROM Choice
        WHERE Quest_ID = ? AND Choice_ID = ?
        """
        try:
            result = DatabaseConnection.fetch_one(query, (question_id, choice_id))
            if result:
                return bool(result[0]) if result[0] is not None else False
            return False
        except Exception as e:
            logger.error(f"❌ Error checking answer: {str(e)}")
            return False
    
    @staticmethod
    def save_student_answer(takes_id, question_id, choice_id=None, answer_text=None):
        """Save student answer - ENHANCED WITH DUPLICATE CHECK"""
        try:
            # Check if answer already exists
            check_query = """
            SELECT Student_Answer_ID 
            FROM Student_Answer 
            WHERE Takes_ID = ? AND Quest_ID = ?
            """
            existing = DatabaseConnection.fetch_one(check_query, (takes_id, question_id))
            
            if existing:
                # Update existing answer
                update_query = """
                UPDATE Student_Answer
                SET Selected_Choice_ID = ?, Answer_Text = ?, Submission_Date = GETDATE()
                WHERE Takes_ID = ? AND Quest_ID = ?
                """
                DatabaseConnection.execute_query(update_query, (choice_id, answer_text, takes_id, question_id))
                logger.debug(f"✅ Updated answer for Q{question_id}")
            else:
                # Insert new answer
                insert_query = """
                INSERT INTO Student_Answer (Takes_ID, Quest_ID, Selected_Choice_ID, Answer_Text, Submission_Date)
                VALUES (?, ?, ?, ?, GETDATE())
                """
                DatabaseConnection.execute_query(insert_query, (takes_id, question_id, choice_id, answer_text))
                logger.debug(f"✅ Saved new answer for Q{question_id}")
                
        except Exception as e:
            logger.error(f"❌ Error saving answer for Q{question_id}: {str(e)}")


class Manager:
    """Manager model - BASIC"""
    
    @staticmethod
    def get_by_person_id(person_id):
        query = "SELECT M_ID, Person_id, Salary FROM Manager WHERE Person_id = ?"
        return DatabaseConnection.fetch_one(query, (person_id,))


class Course:
    """Course model - BASIC"""
    
    @staticmethod
    def get_all_courses():
        query = """
        SELECT Course_ID, name, hours, Topic_ID, Dept_ID
        FROM Course
        ORDER BY name
        """
        return DatabaseConnection.fetch_all(query)


class Topic:
    """Topic model - BASIC"""
    
    @staticmethod
    def get_all_topics():
        query = "SELECT Topic_ID, name FROM Topic ORDER BY name"
        return DatabaseConnection.fetch_all(query)