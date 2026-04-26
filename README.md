# Task Manager CLI

A command-line task management application with user authentication, task CRUD operations, tags, priorities, reminders, and more.

## Features

- **User Authentication** - Register, login, logout, delete account
- **Task Management** - Create, read, update, delete tasks
- **Task Fields** - Title, description, priority (low/medium/high), due date, reminder date
- **Tags** - Create custom tags and assign to tasks
- **Search & Filter** - Filter by status, priority, tag, or search by keyword
- **Pagination** - Browse large task lists with pages
- **Bulk Operations** - Complete, delete, or archive multiple tasks at once
- **Reminders** - View tasks with pending reminders
- **Archiving** - Archive completed tasks instead of deleting
- **Logging** - Application logs saved to `app.log`
- **Input Validation** - Email format, password strength, date parsing

## Requirements

- Python 3.14+
- PostgreSQL database
- Environment variables (see `.env`)

## Setup

1. **Clone the repository**

2. **Create a `.env` file** in the project root:
   ```
   DB_NAME=taskmanager
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   ```

3. **Create the database** ( PostgreSQL):
   ```sql
   CREATE DATABASE taskmanager;
   ```

4. **Install dependencies**:
   ```bash
   pip install psycopg2-binary bcrypt python-dotenv pydantic
   ```

5. **Run the application**:
   ```bash
   python main.py
   ```

## Usage

### Auth Menu
1. **Register** - Create a new account
2. **Login** - Sign in to your account
3. **Exit** - Quit the application

### Task Menu
1. **Create Task** - Add a new task with:
   - Title (required)
   - Description (optional)
   - Priority: low, medium, high (default: medium)
   - Due date: YYYY-MM-DD format (optional)
   - Reminder date: YYYY-MM-DD format (optional)
   - Tag IDs: comma-separated (optional)

2. **View Tasks** - List tasks with optional filters:
   - Page number
   - Status: completed / pending
   - Priority: low / medium / high
   - Tag ID
   - Search keyword
   - Include archived: yes / no

3. **Update Task** - Modify any task field (leave blank to skip)

4. **Delete Task** - Permanently remove a task

5. **Bulk Operations**:
   - Mark Complete (multiple IDs)
   - Delete Multiple
   - Archive Multiple

6. **Tags Management**:
   - Create Tag
   - View Tags
   - Delete Tag
   - Add Tag to Task
   - Remove Tag from Task

7. **Reminders** - View pending task reminders

8. **Logout** - Sign out

9. **Delete Account** - Delete your account

### Commands
- Type `help` or `h` in any menu to see available commands

## Project Structure

```
task-manager/
├── main.py                      # CLI application entry point
├── Authentication/
│   └── auth_service.py         # User authentication
├── Tasks/
│   └── task_service.py         # Task CRUD and management
├── database/
│   └── db.py                  # Database connection and schema
├── app.log                     # Application logs
└── .env                        # Environment variables
```

## Database Schema

### users
| Column | Type | Description |
|--------|------|--------------|
| id | INTEGER | Primary key |
| email | VARCHAR(255) | Unique user email |
| password | TEXT | Hashed password |
| created_at | TIMESTAMP | Creation timestamp |

### tasks
| Column | Type | Description |
|--------|------|--------------|
| id | SERIAL | Primary key |
| title | TEXT | Task title |
| description | TEXT | Task description |
| completed | BOOLEAN | Completion status |
| priority | VARCHAR(20) | low/medium/high |
| due_date | TIMESTAMP | Deadline |
| reminder_date | TIMESTAMP | Reminder date |
| archived | BOOLEAN | Archive status |
| user_id | INTEGER | Foreign key to users |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Update timestamp |

### tags
| Column | Type | Description |
|--------|------|--------------|
| id | SERIAL | Primary key |
| name | VARCHAR(100) | Tag name |
| user_id | INTEGER | Foreign key to users |
| created_at | TIMESTAMP | Creation timestamp |

### task_tags
| Column | Type | Description |
|--------|------|--------------|
| task_id | INTEGER | Foreign key to tasks |
| tag_id | INTEGER | Foreign key to tags |

## License

MIT