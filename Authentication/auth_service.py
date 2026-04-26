import logging
import re
import bcrypt
from database.db import get_connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def validate_email(email: str) -> tuple[bool, str]:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not email or len(email.strip()) == 0:
        return False, "Email cannot be empty"
    if not re.match(pattern, email):
        return False, "Invalid email format"
    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, ""

current_user = None


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)


def register_user(email, password):
    is_valid, error = validate_email(email)
    if not is_valid:
        logger.warning(f"Registration failed - invalid email: {email}")
        print(f"❌ {error}")
        return None

    is_valid, error = validate_password(password)
    if not is_valid:
        logger.warning("Registration failed - weak password")
        print(f"❌ {error}")
        return None

    conn = get_connection()
    cursor = conn.cursor()

    try:
        hashed_password = hash_password(password)

        cursor.execute("""
            INSERT INTO users (email, password)
            VALUES (%s, %s)
            RETURNING id, email;
        """, (email, hashed_password))

        user = cursor.fetchone()
        conn.commit()

        logger.info(f"User registered: {user[0]}")
        print(f"✅ User registered successfully!")
        return user

    except Exception as e:
        logger.error(f"Registration error: {e}")
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            print("❌ Email already registered")
        else:
            print(f"❌ Registration error: {e}")
        conn.rollback()
        return None

    finally:
        cursor.close()
        conn.close()


def login_user(email, password):
    global current_user

    is_valid, error = validate_email(email)
    if not is_valid:
        logger.warning(f"Login failed - invalid email: {email}")
        print(f"❌ {error}")
        return None

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
            logger.warning(f"Login failed - user not found: {email}")
            print("❌ User not found")
            return None

        user_id, user_email, hashed_password = user

        if isinstance(hashed_password, str) and hashed_password.startswith('\\x'):
            hashed_password = bytes.fromhex(hashed_password[2:])

        if check_password(password, hashed_password):
            current_user = {
                "id": user_id,
                "email": user_email
            }
            logger.info(f"User logged in: {user_id}")
            print("✅ Login successful!")
            return current_user
        else:
            logger.warning(f"Login failed - incorrect password: {email}")
            print("❌ Incorrect password")
            return None

    except Exception as e:
        logger.error(f"Login error: {e}")
        print(f"❌ Login error: {e}")
        return None

    finally:
        cursor.close()
        conn.close()


def logout():
    global current_user
    if current_user:
        logger.info(f"User logged out: {current_user['id']}")
    current_user = None
    print("✅ Logged out successfully")


def get_current_user():
    return current_user


def delete_account(password):
    global current_user

    if not current_user:
        logger.warning("Delete account - no user logged in")
        print("❌ No user logged in")
        return False

    is_valid, error = validate_password(password)
    if not is_valid:
        logger.warning("Delete account - invalid password")
        print(f"❌ {error}")
        return False

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT password
            FROM users
            WHERE id = %s;
        """, (current_user["id"],))

        user = cursor.fetchone()

        if not user:
            logger.error("Delete account - user not found")
            print("❌ User not found")
            return False

        hashed_password = user[0]

        if isinstance(hashed_password, str) and hashed_password.startswith('\\x'):
            hashed_password = bytes.fromhex(hashed_password[2:])

        if not check_password(password, hashed_password):
            logger.warning(f"Delete account - incorrect password for user {current_user['id']}")
            print("❌ Incorrect password")
            return False

        cursor.execute("""
            DELETE FROM users
            WHERE id = %s;
        """, (current_user["id"],))

        conn.commit()

        logger.info(f"Account deleted: {current_user['id']}")
        current_user = None
        print("✅ Account deleted successfully")
        return True

    except Exception as e:
        logger.error(f"Delete account error: {e}")
        print(f"❌ Error deleting account: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()