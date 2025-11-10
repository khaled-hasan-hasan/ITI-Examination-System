from werkzeug.security import generate_password_hash
from app.database import DatabaseConnection

def hash_all_passwords():
    """Hash all existing passwords in the database"""
    
    print("\n" + "="*60)
    print("🔐 Starting Password Hashing Process...")
    print("="*60 + "\n")
    
    # First, add Password column if it doesn't exist
    try:
        query_add_column = """
        IF NOT EXISTS (SELECT * FROM sys.columns 
                      WHERE object_id = OBJECT_ID('Person') 
                      AND name = 'Password')
        BEGIN
            ALTER TABLE Person ADD Password NVARCHAR(255);
        END
        """
        DatabaseConnection.execute_query(query_add_column)
        print("✅ Password column checked/added successfully\n")
    except Exception as e:
        print(f"ℹ️  Column already exists or error: {e}\n")
    
    # Get all users
    query_users = "SELECT ID, Email FROM Person"
    users = DatabaseConnection.fetch_all(query_users)
    
    if not users:
        print("❌ No users found!")
        return
    
    print(f"Found {len(users)} users. Hashing passwords...\n")
    
    # Hash passwords (using email as default password)
    success_count = 0
    for user in users:
        user_id = user[0]
        email = user[1]
        
        try:
            # Generate hash (default password = email)
            hashed_password = generate_password_hash(email)
            
            # Update database
            update_query = "UPDATE Person SET Password = ? WHERE ID = ?"
            DatabaseConnection.execute_query(update_query, (hashed_password, user_id))
            
            print(f"✅ User {user_id}: {email} - Password hashed")
            success_count += 1
            
        except Exception as e:
            print(f"❌ User {user_id}: {email} - Error: {e}")
    
    print("\n" + "="*60)
    print(f"✅ Password hashing completed!")
    print(f"   Success: {success_count}/{len(users)} users")
    print("="*60 + "\n")
    
    print("ℹ️  Default passwords are set to user's email address")
    print("   Example: If email is 'test@iti.com', password is 'test@iti.com'")
    print("\n")

if __name__ == '__main__':
    try:
        hash_all_passwords()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
