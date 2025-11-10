# run.py - Main entry point


from dotenv import load_dotenv
load_dotenv()
from app import create_app


app = create_app()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎓 ITI Examination System")
    print("="*60)
    print("📌 Server running at: http://127.0.0.1:5000")
    print("📌 Login page: http://127.0.0.1:5000/auth/login")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
