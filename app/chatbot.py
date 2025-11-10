# app/chatbot.py - WORKING VERSION with correct model

import google.generativeai as genai
import os
import logging

logger = logging.getLogger(__name__)

class StudentChatbot:
    """Chatbot ذكي مع Google API"""

    def __init__(self):
        """Initialize chatbot"""
        self.use_api = False
        self.model = None

        try:
            api_key = os.getenv('GEMINI_API_KEY')

            if api_key:
                try:
                    logger.info("Configuring Gemini API...")
                    genai.configure(api_key=api_key)
                    self.model = genai.GenerativeModel('gemini-2.5-flash')
                    self.use_api = True
                    logger.info("✓ Using Google Gemini API - gemini-2.5-flash")

                except Exception as e:
                    logger.warning(f"API failed: {str(e)}")
                    self.use_api = False
            else:
                logger.warning("No API key")
                self.use_api = False

        except Exception as e:
            logger.error(f"Init error: {str(e)}")
            self.use_api = False

    
    def get_response(self, user_message, student_context=None):
        """Get response"""
        try:
            if not user_message or len(user_message.strip()) == 0:
                return "⚠️ الرسالة فارغة."
            
            logger.info(f"Processing: {user_message[:50]}...")
            
            # Try API
            if self.use_api and self.model:
                try:
                    prompt = self._build_prompt(user_message, student_context)
                    response = self.model.generate_content(prompt)
                    
                    if response and response.text:
                        logger.info("✓ API response received")
                        return response.text
                except Exception as e:
                    logger.warning(f"API error: {str(e)}")
            
            # Fallback to local
            return self._get_local_response(user_message)
        
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return "❌ خطأ. حاول مرة أخرى."
    
    def _build_prompt(self, user_message, student_context):
        """Build prompt"""
        system = """أنت مساعد تعليمي ذكي.

مساعدتك:
• نصائح دراسية فعالة
• شرح المواد الدراسية
• استراتيجيات الامتحانات
• تحفيز وتشجيع الطالب

الأسلوب:
• عربية بسيطة وواضحة
• إجابات قصيرة ومباشرة
• إيجابي ومشجع
• استخدم رموز تعبيرية"""
        
        if student_context:
            system += f"\n\nالطالب: {student_context}"
        
        return f"{system}\n\nالسؤال: {user_message}\n\nالإجابة:"
    
    def _get_local_response(self, user_message):
        """Local response"""
        import random
        
        message = user_message.lower()
        
        if any(w in message for w in ['ذاكر', 'دراسة', 'study']):
            return "📚 **نصائح دراسية:**\n• ذاكر بانتظام يومياً\n• اقسم الدرس لأجزاء\n• خذ فترات راحة\n• اختبر نفسك\n• نم جيداً"
        elif any(w in message for w in ['امتحان', 'exam', 'test']):
            return "📝 **نصائح امتحان:**\n• اقرأ الأسئلة كاملة\n• خطط وقتك\n• ابدأ بالسهل\n• تحقق من الإجابات\n• استرخِ"
        elif any(w in message for w in ['تركيز', 'focus']):
            return "🧠 **زيادة التركيز:**\n• ابعد الجوال\n• مكان هادئ\n• اشرب ماء\n• فترات راحة\n• أوقات مناسبة"
        elif any(w in message for w in ['مرحبا', 'hello', 'hi']):
            return "👋 **مرحباً!** أنا مساعدك الدراسي الذكي.\n\nاسأل عن:\n✓ نصائح دراسية\n✓ امتحانات\n✓ تركيز\n✓ تحفيز\n\nماذا تريد؟ 😊"
        else:
            return "💭 **يمكنك السؤال عن:**\n✓ نصائح دراسية\n✓ امتحانات\n✓ تركيز\n✓ تحفيز\n✓ أي موضوع دراسي!\n\nاسأل سؤالاً محدداً 😊"
    
    def get_study_tips(self, topic):
        return self.get_response(f"أعطني نصائح دراسية لـ {topic}")
    
    def analyze_performance(self, student_stats):
        return self.get_response("كيف أحسن أدائي الدراسي")


chatbot_instance = StudentChatbot()

def get_chatbot():
    return chatbot_instance
