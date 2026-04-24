from database.db import get_connection
from Authentication.auth_service import get_current_user

# ----------------------------
# CREATE TASK
# ----------------------------
def create_task(title, completed=False):
    user = get_current_user()
    if not user:
        print("❌ You must be logged in to create tasks")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO tasks (title, completed, user_id)
            VALUES (%s, %s, %s)
            RETURNING id, title, completed;
        """, (title, completed, user["id"]))

        task = cursor.fetchone()
        conn.commit()

        print("✅ Task created:", task)
        return task

    except Exception as e:
        print("❌ Error creating task:", e)
        conn.rollback()

    finally:
        cursor.close()
        conn.close()


# ----------------------------
# VIEW ALL TASKS (for user)
# ----------------------------
def get_tasks():
    user = get_current_user()
    if not user:
        print("❌ You must be logged in")
        return []

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, title, completed, created_at
            FROM tasks
            WHERE user_id = %s
            ORDER BY id DESC;
        """, (user["id"],))

        tasks = cursor.fetchall()

        print("\n📋 Your Tasks:")
        for task in tasks:
            print(task)

        return tasks

    except Exception as e:
        print("❌ Error fetching tasks:", e)
        return []

    finally:
        cursor.close()
        conn.close()


# ----------------------------
# UPDATE TASK
# ----------------------------
def update_task(task_id, title=None, completed=None):
    user = get_current_user()
    if not user:
        print("❌ You must be logged in")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Build dynamic update
        fields = []
        values = []

        if title is not None:
            fields.append("title = %s")
            values.append(title)

        if completed is not None:
            fields.append("completed = %s")
            values.append(completed)

        if not fields:
            print("⚠️ Nothing to update")
            return

        values.append(task_id)
        values.append(user["id"])

        query = f"""
            UPDATE tasks
            SET {", ".join(fields)}
            WHERE id = %s AND user_id = %s
            RETURNING id, title, completed;
        """

        cursor.execute(query, values)
        updated_task = cursor.fetchone()

        conn.commit()

        if updated_task:
            print("✅ Task updated:", updated_task)
        else:
            print("❌ Task not found or not yours")

        return updated_task

    except Exception as e:
        print("❌ Error updating task:", e)
        conn.rollback()

    finally:
        cursor.close()
        conn.close()


# ----------------------------
# DELETE TASK
# ----------------------------
def delete_task(task_id):
    user = get_current_user()
    if not user:
        print("❌ You must be logged in")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE FROM tasks
            WHERE id = %s AND user_id = %s
            RETURNING id;
        """, (task_id, user["id"]))

        deleted = cursor.fetchone()
        conn.commit()

        if deleted:
            print("🗑️ Task deleted successfully")
        else:
            print("❌ Task not found or not yours")

    except Exception as e:
        print("❌ Error deleting task:", e)
        conn.rollback()

    finally:
        cursor.close()
        conn.close()