import bcrypt
from database.db import get_connection

current_user = None

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def register_user(email, password):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        hashed_password = hash_password(password)

        cursor.execute("""
            INSERT INTO users (email, password)
            VALUES (%s, %s)
            RETURNING id, email
        """, (email, hashed_password))

        user = cursor.fetchone()
        conn.commit()

        print("✅ User registered successfully:", user)
        return user
    except Exception as e:
        print("Registration error:", e)
        conn.rollback()

    finally:
        cursor.close()
        conn.close()

def login_user(email, password):
    global current_user

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, email, password
            FROM users
            WHERE email = %s;
        """, (email,))

        user = cursor.fetchone()

        if not user:
            print("user not found")
            return None
        
        user_id, user_email, hashed_password = user

        if isinstance(hashed_password, str) and hashed_password.startswith('\\x'):
            hashed_password = bytes.fromhex(hashed_password[2:])

        if check_password(password, hashed_password):
            current_user = {
                "id": user_id,
                "email": user_email
            }

            print("Login Successful")
            return current_user
        else:
            print("Incorrect password")
    except Exception as e:
        print("Error login in! Please try again:", e)
        return None
    
    finally:
        cursor.close()
        conn.close()

def logout():
    global current_user
    current_user = None
    print("Logged out successfully")

def get_current_user():
    return current_user