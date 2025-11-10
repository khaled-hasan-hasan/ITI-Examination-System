# app/ml_helper.py - مساعد ML لتحليل وتوقع أداء الطالب

from app.database import DatabaseConnection
import numpy as np
from sklearn.linear_model import LinearRegression
import logging

logger = logging.getLogger(__name__)

class StudentMLHelper:
    """
    مساعد ML لتحليل أداء الطالب والتنبؤ بالأداء المستقبلي
    """
    
    def __init__(self):
        self.model = LinearRegression()
        self.trained = False
    
    def get_student_insights(self, student_id):
        """
        الحصول على رؤى شاملة عن أداء الطالب
        
        Returns:
            dict: معلومات وتحليلات الطالب
        """
        try:
            # جلب بيانات الطالب
            query = """
            SELECT 
                COUNT(Takes_ID) as total_exams,
                AVG(Score) as avg_score,
                MAX(Score) as max_score,
                MIN(Score) as min_score,
                STDEV(Score) as std_dev
            FROM TAKES
            WHERE S_ID = ? AND Score IS NOT NULL AND Score > 0
            """
            
            result = DatabaseConnection.fetch_one(query, (student_id,))
            
            if not result or result[0] == 0:
                return {
                    'status': 'no_data',
                    'message': 'لا توجد بيانات كافية للتحليل'
                }
            
            total_exams = result[0]
            avg_score = float(result[1]) if result[1] else 0
            max_score = float(result[2]) if result[2] else 0
            min_score = float(result[3]) if result[3] else 0
            std_dev = float(result[4]) if result[4] else 0
            
            # تحليل الأداء
            performance_level = self._get_performance_level(avg_score)
            consistency = self._check_consistency(std_dev)
            trend = self._get_trend(student_id)
            recommendations = self._get_recommendations(avg_score, std_dev, trend)
            
            return {
                'status': 'success',
                'statistics': {
                    'total_exams': total_exams,
                    'avg_score': f"{avg_score:.1f}",
                    'max_score': f"{max_score:.1f}",
                    'min_score': f"{min_score:.1f}",
                    'std_dev': f"{std_dev:.1f}"
                },
                'analysis': {
                    'performance_level': performance_level,
                    'consistency': consistency,
                    'trend': trend
                },
                'recommendations': recommendations
            }
        
        except Exception as e:
            logger.error(f"Error in get_student_insights: {str(e)}")
            return {
                'status': 'error',
                'message': f'حدث خطأ في التحليل: {str(e)}'
            }
    
    def predict_next_exam(self, student_id):
        """
        التنبؤ بالدرجة المتوقعة في الامتحان القادم
        
        Returns:
            dict: التنبؤ والثقة
        """
        try:
            # جلب آخر 5 درجات للطالب
            query = """
            SELECT TOP 5 Score, DATEDIFF(day, '2024-01-01', Date_Taken) as days
            FROM TAKES
            WHERE S_ID = ? AND Score IS NOT NULL
            ORDER BY Date_Taken DESC
            """
            
            results = DatabaseConnection.fetch_all(query, (student_id,))
            
            if not results or len(results) < 3:
                return {
                    'status': 'insufficient_data',
                    'message': 'تحتاج إلى 3 امتحانات على الأقل للتنبؤ'
                }
            
            # تحضير البيانات
            X = np.array([[i] for i in range(len(results))])
            y = np.array([float(r[0]) for r in results])
            
            # تدريب النموذج
            self.model.fit(X, y)
            
            # التنبؤ
            next_prediction = self.model.predict([[len(results)]])[0]
            
            # حساب الثقة (based on consistency)
            std = np.std(y)
            confidence = max(50, min(95, 100 - (std * 2)))
            
            return {
                'status': 'success',
                'predicted_score': f"{next_prediction:.1f}",
                'confidence': f"{confidence:.0f}",
                'message': self._get_prediction_message(next_prediction)
            }
        
        except Exception as e:
            logger.error(f"Error in predict_next_exam: {str(e)}")
            return {
                'status': 'error',
                'message': 'حدث خطأ في التنبؤ'
            }
    
    def _get_performance_level(self, avg_score):
        """تحديد مستوى الأداء"""
        if avg_score >= 90:
            return {
                'level': 'ممتاز',
                'emoji': '🌟',
                'description': 'أداء متميز للغاية!'
            }
        elif avg_score >= 80:
            return {
                'level': 'جيد جداً',
                'emoji': '⭐',
                'description': 'أداء رائع، استمر!'
            }
        elif avg_score >= 70:
            return {
                'level': 'جيد',
                'emoji': '👍',
                'description': 'أداء جيد، يمكن تحسينه'
            }
        elif avg_score >= 60:
            return {
                'level': 'مقبول',
                'emoji': '📚',
                'description': 'تحتاج إلى بذل مزيد من الجهد'
            }
        else:
            return {
                'level': 'يحتاج تحسين',
                'emoji': '💪',
                'description': 'لا تيأس! يمكنك التحسن'
            }
    
    def _check_consistency(self, std_dev):
        """فحص ثبات الأداء"""
        if std_dev < 5:
            return {
                'level': 'ممتاز',
                'description': 'أداء ثابت ومستقر'
            }
        elif std_dev < 10:
            return {
                'level': 'جيد',
                'description': 'أداء مستقر نسبياً'
            }
        else:
            return {
                'level': 'متفاوت',
                'description': 'أداء متذبذب، حاول أن تكون أكثر انتظاماً'
            }
    
    def _get_trend(self, student_id):
        """تحليل اتجاه الأداء"""
        query = """
        SELECT TOP 5 Score
        FROM TAKES
        WHERE S_ID = ? AND Score IS NOT NULL
        ORDER BY Date_Taken DESC
        """
        
        results = DatabaseConnection.fetch_all(query, (student_id,))
        
        if not results or len(results) < 2:
            return {
                'direction': 'مستقر',
                'emoji': '➡️',
                'description': 'بيانات غير كافية لتحديد الاتجاه'
            }
        
        scores = [float(r[0]) for r in results]
        
        # حساب الاتجاه
        if scores[0] > scores[-1] + 5:
            return {
                'direction': 'تحسن',
                'emoji': '📈',
                'description': 'أداءك في تحسن مستمر!'
            }
        elif scores[0] < scores[-1] - 5:
            return {
                'direction': 'انخفاض',
                'emoji': '📉',
                'description': 'انتبه! أداءك في انخفاض'
            }
        else:
            return {
                'direction': 'مستقر',
                'emoji': '➡️',
                'description': 'أداءك مستقر'
            }
    
    def _get_recommendations(self, avg_score, std_dev, trend):
        """الحصول على توصيات"""
        recommendations = []
        
        # بناءً على المعدل
        if avg_score < 70:
            recommendations.append("📚 احرص على مراجعة المواد بانتظام")
            recommendations.append("👨‍🏫 لا تتردد في طلب المساعدة من المدرسين")
        
        # بناءً على الثبات
        if std_dev > 10:
            recommendations.append("⏰ حافظ على جدول دراسي منتظم")
            recommendations.append("😴 احصل على قسط كافٍ من النوم")
        
        # بناءً على الاتجاه
        if trend['direction'] == 'انخفاض':
            recommendations.append("⚠️ راجع طريقة دراستك وحاول تحسينها")
            recommendations.append("🎯 ركز على نقاط الضعف")
        elif trend['direction'] == 'تحسن':
            recommendations.append("🌟 استمر على نفس النهج!")
            recommendations.append("💪 حاول تطبيق نفس الاستراتيجية في جميع المواد")
        
        # توصيات عامة
        if len(recommendations) < 3:
            recommendations.append("📖 خصص وقتاً يومياً للمراجعة")
            recommendations.append("🧘 مارس تقنيات الاسترخاء قبل الامتحان")
        
        return recommendations
    
    def _get_prediction_message(self, predicted_score):
        """رسالة بناءً على الدرجة المتوقعة"""
        if predicted_score >= 90:
            return "🌟 متوقع أن تحصل على درجة ممتازة! استمر!"
        elif predicted_score >= 80:
            return "⭐ أداء جيد جداً متوقع! ركز قليلاً وستصل للتميز"
        elif predicted_score >= 70:
            return "👍 أداء جيد متوقع، يمكنك تحسينه بالمزيد من المراجعة"
        elif predicted_score >= 60:
            return "📚 احرص على المراجعة الجيدة لتحسين درجتك"
        else:
            return "💪 اهتم بالدراسة أكثر لتحسين نتائجك"


# Instance واحد
ml_helper_instance = StudentMLHelper()


def get_ml_helper():
    """الحصول على instance الـ ML Helper"""
    return ml_helper_instance
