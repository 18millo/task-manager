# Task Manager CLI
## A Command-Line Task Management Application

**Presenter:** Millo  
**Date:** April 2026

---

## What is this Project?

A command-line application for managing personal tasks with:
- User authentication (register, login, logout)
- Full CRUD operations on tasks
- Advanced features: tags, priorities, due dates, reminders
- Search, filter, pagination, and bulk operations

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.14+ |
| Database | PostgreSQL |
| Password Hashing | bcrypt |
| DB Driver | psycopg2-binary |
| Config | python-dotenv |

---

## Project Structure

```
task-manager/
├── main.py                     # CLI entry point
├── Authentication/
│   └── auth_service.py        # User auth (register, login)
├── Tasks/
│   └── task_service.py       # Task CRUD, tags, bulk ops
├── database/
│   └── db.py                # DB connection & schema
├── app.log                   # Application logs
└── .env                     # Environment variables
```

---

## Database Schema

### users
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| email | VARCHAR(255) | Unique |
| password | TEXT | bcrypt hashed |
| created_at | TIMESTAMP | Created |

### tasks
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| title | TEXT | Task title |
| description | TEXT | Details |
| completed | BOOLEAN | Status |
| priority | VARCHAR(20) | low/medium/high |
| due_date | TIMESTAMP | Deadline |
| reminder_date | TIMESTAMP | Reminder |
| archived | BOOLEAN | Archived |
| user_id | INTEGER | FK → users |

### tags
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| name | VARCHAR(100) | Tag name |
| user_id | INTEGER | FK → users |

### task_tags (junction)
| Column | Type | Description |
|--------|------|-------------|
| task_id | INTEGER | FK → tasks |
| tag_id | INTEGER | FK → tags |

---

## Code Snippet: Password Hashing

```python
import bcrypt

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)
```

**Why bcrypt?**
- One-way hashing (not reversible)
- Built-in salt (prevents rainbow table attacks)
- Configurable work factor (slow = secure)

---

## Code Snippet: SQL Injection Prevention

```python
# WRONG - vulnerable to SQL injection
query = f"INSERT INTO tasks (title) VALUES ('{title}')"

# CORRECT - using parameterized queries
cursor.execute("""
    INSERT INTO tasks (title, description, priority, user_id)
    VALUES (%s, %s, %s, %s)
    RETURNING id, title;
""", (title, description, priority, user["id"]))
```

**Key Point:** Never use f-strings with user input in SQL!

---

## Code Snippet: Bulk Operations

```python
def bulk_complete(task_ids):
    cursor.execute("""
        UPDATE tasks
        SET completed = TRUE, updated_at = CURRENT_TIMESTAMP
        WHERE id = ANY(%s) AND user_id = %s AND completed = FALSE
        RETURNING id;
    """, (task_ids, user["id"]))
    conn.commit()
```

Uses PostgreSQL `ANY()` to update multiple rows in one query - efficient!

---

## Strong Points of This App

### 1. Security
- bcrypt password hashing (not encryption - one-way)
- Parameterized SQL queries prevent injection
- Input validation (email regex, password length minimum)

### 2. Database Design
- Proper foreign key relationships
- Normalized tables (users, tasks, tags, task_tags)
- Junction table for many-to-many relationship (task_tags)

### 3. Error Handling
- Try/except on all DB operations
- Rollback on failure
- User-friendly error messages

### 4. Code Quality
- Logging for debugging
- Clean separation of concerns (auth vs tasks vs db)

---

## What I Learned

- Database design and normalization
- SQL fundamentals (SELECT, INSERT, UPDATE, DELETE)
- Python database connectivity (psycopg2)
- Security best practices (hashing, injection prevention)
- CLI user experience design
- Error handling and logging

---

## Future Improvements

- Add unit tests (pytest)
- REST API (Flask/FastAPI)
- Docker containerization
- Web frontend
- Task categories (hierarchical tags)

---

## Demo Scenario

1. Register new user
2. Create task with priority + due date
3. View and filter tasks
4. Create and assign tags
5. Bulk complete multiple tasks
6. Archive old tasks

---

## Questions?

Thank you!