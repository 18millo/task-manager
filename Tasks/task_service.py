import logging
import re
from datetime import datetime
from database.db import get_connection
from Authentication.auth_service import get_current_user

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ----------------------------
# VALIDATION
# ----------------------------
def validate_priority(priority: str) -> bool:
    return priority in ['low', 'medium', 'high']


def parse_date(date_str: str) -> datetime | None:
    if not date_str or date_str.strip() == "":
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except ValueError:
        try:
            return datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            return None


# ----------------------------
# CREATE TASK
# ----------------------------
def create_task(title, description=None, completed=False, priority="medium", due_date=None, reminder_date=None, tag_ids=None):
    user = get_current_user()
    if not user:
        logger.warning("Unauthorized task creation attempt")
        print("❌ You must be logged in to create tasks")
        return None

    if not title or len(title.strip()) == 0:
        print("❌ Task title cannot be empty")
        return None

    if not validate_priority(priority):
        print("❌ Invalid priority. Use: low, medium, or high")
        return None

    conn = get_connection()
    cursor = conn.cursor()

    try:
        due_date_dt = parse_date(due_date) if due_date else None
        reminder_dt = parse_date(reminder_date) if reminder_date else None

        cursor.execute("""
            INSERT INTO tasks (title, description, completed, priority, due_date, reminder_date, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, title, description, completed, priority, due_date, reminder_date, created_at;
        """, (title, description, completed, priority, due_date_dt, reminder_dt, user["id"]))

        task = cursor.fetchone()
        task_id = task[0]

        if tag_ids:
            for tag_id in tag_ids:
                cursor.execute("""
                    INSERT INTO task_tags (task_id, tag_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING;
                """, (task_id, tag_id))

        conn.commit()
        logger.info(f"Task created: {task_id} by user {user['id']}")
        print(f"✅ Task created: ID={task_id}, Title={title}")
        return task

    except Exception as e:
        logger.error(f"Error creating task: {e}")
        print(f"❌ Error creating task: {e}")
        conn.rollback()
        return None

    finally:
        cursor.close()
        conn.close()


# ----------------------------
# VIEW TASKS (with filter, search, pagination)
# ----------------------------
def get_tasks(
    page=1,
    per_page=10,
    status=None,
    priority=None,
    tag_id=None,
    search=None,
    include_archived=False
):
    user = get_current_user()
    if not user:
        logger.warning("Unauthorized task fetch attempt")
        print("❌ You must be logged in")
        return []

    conn = get_connection()
    cursor = conn.cursor()

    try:
        conditions = ["t.user_id = %s"]
        values = [user["id"]]

        if not include_archived:
            conditions.append("t.archived = FALSE")

        if status == "completed":
            conditions.append("t.completed = TRUE")
        elif status == "pending":
            conditions.append("t.completed = FALSE")

        if priority:
            conditions.append("t.priority = %s")
            values.append(priority)

        if tag_id:
            conditions.append("t.id IN (SELECT task_id FROM task_tags WHERE tag_id = %s)")
            values.append(tag_id)

        if search:
            conditions.append("(t.title ILIKE %s OR t.description ILIKE %s)")
            search_term = f"%{search}%"
            values.extend([search_term, search_term])

        where_clause = " AND ".join(conditions)

        offset = (page - 1) * per_page

        query = f"""
            SELECT t.id, t.title, t.description, t.completed, t.priority,
                   t.due_date, t.reminder_date, t.archived, t.created_at,
                   t.updated_at
            FROM tasks t
            WHERE {where_clause}
            ORDER BY
                CASE t.priority
                    WHEN 'high' THEN 1
                    WHEN 'medium' THEN 2
                    WHEN 'low' THEN 3
                END,
                t.created_at DESC
            LIMIT %s OFFSET %s;
        """

        values.extend([per_page, offset])
        cursor.execute(query, values)
        tasks = cursor.fetchall()

        cursor.execute(f"SELECT COUNT(*) FROM tasks t WHERE {where_clause}", values[:-2])
        total = cursor.fetchone()[0]
        total_pages = (total + per_page - 1) // per_page

        print(f"\n📋 Your Tasks (Page {page}/{total_pages}) - Total: {total}")
        print("-" * 80)

        for task in tasks:
            tags = get_task_tags(task[0])
            tags_str = f" [Tags: {', '.join([t['name'] for t in tags])}]" if tags else ""
            status_str = "✅" if task[3] else "⬜"
            due_str = f" | Due: {task[5].strftime('%Y-%m-%d')}" if task[5] else ""
            reminder_str = f" | Reminder: {task[6].strftime('%Y-%m-%d')}" if task[6] else ""
            priority_symbol = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task[4], "🟡")

            print(f"{task[0]}: {status_str} {priority_symbol} {task[1]}{tags_str}")
            if task[2]:
                print(f"   Description: {task[2]}")
            print(f"   Priority: {task[4]} | Created: {task[9].strftime('%Y-%m-%d %H:%M')}{due_str}{reminder_str}")
            if task[7]:
                print(f"   [ARCHIVED]")
            print()

        logger.info(f"User {user['id']} fetched tasks - Page {page}, Total {total}")
        return tasks

    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        print(f"❌ Error fetching tasks: {e}")
        return []

    finally:
        cursor.close()
        conn.close()


# ----------------------------
# GET TASK TAGS
# ----------------------------
def get_task_tags(task_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT t.id, t.name
            FROM tags t
            JOIN task_tags tt ON t.id = tt.tag_id
            WHERE tt.task_id = %s;
        """, (task_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


# ----------------------------
# UPDATE TASK
# ----------------------------
def update_task(task_id, title=None, description=None, completed=None, priority=None, due_date=None, reminder_date=None, archived=None):
    user = get_current_user()
    if not user:
        logger.warning("Unauthorized task update attempt")
        print("❌ You must be logged in")
        return None

    conn = get_connection()
    cursor = conn.cursor()

    try:
        fields = []
        values = []

        if title is not None:
            fields.append("title = %s")
            values.append(title)

        if description is not None:
            fields.append("description = %s")
            values.append(description)

        if completed is not None:
            fields.append("completed = %s")
            values.append(completed)

        if priority is not None:
            if not validate_priority(priority):
                print("❌ Invalid priority. Use: low, medium, or high")
                return None
            fields.append("priority = %s")
            values.append(priority)

        if due_date is not None:
            due_date_dt = parse_date(due_date) if due_date else None
            fields.append("due_date = %s")
            values.append(due_date_dt)

        if reminder_date is not None:
            reminder_dt = parse_date(reminder_date) if reminder_date else None
            fields.append("reminder_date = %s")
            values.append(reminder_dt)

        if archived is not None:
            fields.append("archived = %s")
            values.append(archived)

        if not fields:
            print("⚠️ Nothing to update")
            return None

        fields.append("updated_at = CURRENT_TIMESTAMP")

        values.append(task_id)
        values.append(user["id"])

        query = f"""
            UPDATE tasks
            SET {", ".join(fields)}
            WHERE id = %s AND user_id = %s
            RETURNING id, title, description, completed, priority, due_date, reminder_date, archived;
        """

        cursor.execute(query, values)
        updated_task = cursor.fetchone()
        conn.commit()

        if updated_task:
            logger.info(f"Task {task_id} updated by user {user['id']}")
            print(f"✅ Task updated: ID={updated_task[0]}, Title={updated_task[1]}")
        else:
            print("❌ Task not found or not yours")

        return updated_task

    except Exception as e:
        logger.error(f"Error updating task: {e}")
        print(f"❌ Error updating task: {e}")
        conn.rollback()
        return None

    finally:
        cursor.close()
        conn.close()


# ----------------------------
# DELETE TASK
# ----------------------------
def delete_task(task_id):
    user = get_current_user()
    if not user:
        logger.warning("Unauthorized task delete attempt")
        print("❌ You must be logged in")
        return False

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
            logger.info(f"Task {task_id} deleted by user {user['id']}")
            print("🗑️ Task deleted successfully")
        else:
            print("❌ Task not found or not yours")

        return bool(deleted)

    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        print(f"❌ Error deleting task: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


# ----------------------------
# BULK OPERATIONS
# ----------------------------
def bulk_complete(task_ids):
    user = get_current_user()
    if not user:
        print("❌ You must be logged in")
        return 0

    if not task_ids:
        print("❌ No task IDs provided")
        return 0

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE tasks
            SET completed = TRUE, updated_at = CURRENT_TIMESTAMP
            WHERE id = ANY(%s) AND user_id = %s AND completed = FALSE
            RETURNING id;
        """, (task_ids, user["id"]))

        updated = cursor.fetchall()
        conn.commit()
        count = len(updated)

        logger.info(f"User {user['id']} bulk completed {count} tasks")
        print(f"✅ Marked {count} task(s) as complete")
        return count

    except Exception as e:
        logger.error(f"Error bulk completing tasks: {e}")
        print(f"❌ Error: {e}")
        conn.rollback()
        return 0

    finally:
        cursor.close()
        conn.close()


def bulk_delete(task_ids):
    user = get_current_user()
    if not user:
        print("❌ You must be logged in")
        return 0

    if not task_ids:
        print("❌ No task IDs provided")
        return 0

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE FROM tasks
            WHERE id = ANY(%s) AND user_id = %s
            RETURNING id;
        """, (task_ids, user["id"]))

        deleted = cursor.fetchall()
        conn.commit()
        count = len(deleted)

        logger.info(f"User {user['id']} bulk deleted {count} tasks")
        print(f"🗑️ Deleted {count} task(s)")
        return count

    except Exception as e:
        logger.error(f"Error bulk deleting tasks: {e}")
        print(f"❌ Error: {e}")
        conn.rollback()
        return 0

    finally:
        cursor.close()
        conn.close()


def bulk_archive(task_ids):
    user = get_current_user()
    if not user:
        print("❌ You must be logged in")
        return 0

    if not task_ids:
        print("❌ No task IDs provided")
        return 0

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE tasks
            SET archived = TRUE, updated_at = CURRENT_TIMESTAMP
            WHERE id = ANY(%s) AND user_id = %s AND archived = FALSE
            RETURNING id;
        """, (task_ids, user["id"]))

        archived = cursor.fetchall()
        conn.commit()
        count = len(archived)

        logger.info(f"User {user['id']} bulk archived {count} tasks")
        print(f"📦 Archived {count} task(s)")
        return count

    except Exception as e:
        logger.error(f"Error bulk archiving tasks: {e}")
        print(f"❌ Error: {e}")
        conn.rollback()
        return 0

    finally:
        cursor.close()
        conn.close()


# ----------------------------
# TAG MANAGEMENT
# ----------------------------
def create_tag(name):
    user = get_current_user()
    if not user:
        print("❌ You must be logged in")
        return None

    if not name or len(name.strip()) == 0:
        print("❌ Tag name cannot be empty")
        return None

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO tags (name, user_id)
            VALUES (%s, %s)
            RETURNING id, name;
        """, (name.strip(), user["id"]))

        tag = cursor.fetchone()
        conn.commit()

        logger.info(f"Tag {tag[0]} created by user {user['id']}")
        print(f"✅ Tag created: {tag[1]}")
        return tag

    except Exception as e:
        logger.error(f"Error creating tag: {e}")
        print(f"❌ Error creating tag: {e}")
        conn.rollback()
        return None

    finally:
        cursor.close()
        conn.close()


def get_tags():
    user = get_current_user()
    if not user:
        print("❌ You must be logged in")
        return []

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, name, created_at
            FROM tags
            WHERE user_id = %s
            ORDER BY name;
        """, (user["id"],))

        tags = cursor.fetchall()
        print("\n🏷️ Your Tags:")
        for tag in tags:
            print(f"  {tag[0]}: {tag[1]}")
        return tags

    except Exception as e:
        logger.error(f"Error fetching tags: {e}")
        print(f"❌ Error: {e}")
        return []

    finally:
        cursor.close()
        conn.close()


def delete_tag(tag_id):
    user = get_current_user()
    if not user:
        print("❌ You must be logged in")
        return False

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE FROM tags
            WHERE id = %s AND user_id = %s
            RETURNING id;
        """, (tag_id, user["id"]))

        deleted = cursor.fetchone()
        conn.commit()

        if deleted:
            logger.info(f"Tag {tag_id} deleted by user {user['id']}")
            print("🗑️ Tag deleted")
            return True
        else:
            print("❌ Tag not found or not yours")
            return False

    except Exception as e:
        logger.error(f"Error deleting tag: {e}")
        print(f"❌ Error: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


def add_tag_to_task(task_id, tag_id):
    user = get_current_user()
    if not user:
        print("❌ You must be logged in")
        return False

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO task_tags (task_id, tag_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            RETURNING task_id;
        """, (task_id, tag_id))

        result = cursor.fetchone()
        conn.commit()

        if result:
            logger.info(f"Tag {tag_id} added to task {task_id}")
            print(f"✅ Tag added to task")
            return True
        else:
            print("❌ Task or tag not found")
            return False

    except Exception as e:
        logger.error(f"Error adding tag to task: {e}")
        print(f"❌ Error: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


def remove_tag_from_task(task_id, tag_id):
    user = get_current_user()
    if not user:
        print("❌ You must be logged in")
        return False

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE FROM task_tags
            WHERE task_id = %s AND tag_id = %s
            RETURNING task_id;
        """, (task_id, tag_id))

        result = cursor.fetchone()
        conn.commit()

        if result:
            logger.info(f"Tag {tag_id} removed from task {task_id}")
            print("✅ Tag removed from task")
            return True
        else:
            print("❌ Connection not found")
            return False

    except Exception as e:
        logger.error(f"Error removing tag from task: {e}")
        print(f"❌ Error: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


# ----------------------------
# REMINDERS
# ----------------------------
def get_due_reminders():
    user = get_current_user()
    if not user:
        print("❌ You must be logged in")
        return []

    conn = get_connection()
    cursor = conn.cursor()

    try:
        now = datetime.now()

        cursor.execute("""
            SELECT id, title, due_date, reminder_date
            FROM tasks
            WHERE user_id = %s
              AND archived = FALSE
              AND completed = FALSE
              AND reminder_date IS NOT NULL
              AND reminder_date <= %s
            ORDER BY reminder_date;
        """, (user["id"], now))

        reminders = cursor.fetchall()

        if reminders:
            print("\n⏰ Pending Reminders:")
            for r in reminders:
                print(f"  {r[0]}: {r[1]} - Due: {r[2].strftime('%Y-%m-%d')}")
        else:
            print("\n⏰ No pending reminders")

        return reminders

    except Exception as e:
        logger.error(f"Error fetching reminders: {e}")
        print(f"❌ Error: {e}")
        return []

    finally:
        cursor.close()
        conn.close()