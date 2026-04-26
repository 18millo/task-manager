from Authentication.auth_service import register_user, login_user, logout, get_current_user, delete_account
from Tasks.task_service import (
    create_task, get_tasks, update_task, delete_task,
    bulk_complete, bulk_delete, bulk_archive,
    create_tag, get_tags, delete_tag, add_tag_to_task, remove_tag_from_task,
    get_due_reminders
)
from database.db import create_tables

# INITIAL SETUP
def start_app():
    create_tables()
    print("\n🚀 Task Manager CLI")
    print("Type 'help' for available commands\n")

# AUTH MENU
def auth_menu():
    while True:
        print("\n===== AUTH MENU =====")
        print("1. Register")
        print("2. Login")
        print("3. Exit")

        choice = input("Select option: ").strip()

        if choice == "1":
            email = input("Enter email: ").strip()
            password = input("Enter password: ").strip()
            register_user(email, password)

        elif choice == "2":
            email = input("Enter email: ").strip()
            password = input("Enter password: ").strip()
            user = login_user(email, password)
            if user:
                task_menu()

        elif choice == "3":
            print("👋 Goodbye!")
            break

        elif choice.lower() in ["help", "h"]:
            print("\nHelp:")
            print("  1. Register - Create a new account")
            print("  2. Login - Sign in to your account")
            print("  3. Exit - Quit the application")

        else:
            print("❌ Invalid option")


# TASK MENU
def task_menu():
    user = get_current_user()
    while user:
        print(f"\n===== TASK MENU ({user['email']}) =====")
        print("1. Create Task")
        print("2. View Tasks (with filter/search)")
        print("3. Update Task")
        print("4. Delete Task")
        print("5. Bulk Operations")
        print("6. Tags Management")
        print("7. Reminders")
        print("8. Logout")
        print("9. Delete Account")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            title = input("Task title: ").strip()
            if not title:
                print("❌ Title cannot be empty")
                continue

            description = input("Description (optional): ").strip() or None

            print("Priority (low/medium/high) [default: medium]: ", end="")
            priority = input().strip().lower() or "medium"

            print("Due date (YYYY-MM-DD) [optional]: ", end="")
            due_date = input().strip() or None

            print("Reminder date (YYYY-MM-DD) [optional]: ", end="")
            reminder_date = input().strip() or None

            get_tags()
            tag_ids_input = input("Tag IDs (comma-separated) [optional]: ").strip()
            tag_ids = [int(t.strip()) for t in tag_ids_input.split(",") if t.strip().isdigit()] if tag_ids_input else None

            create_task(title, description, False, priority, due_date, reminder_date, tag_ids)

        elif choice == "2":
            print("\n--- View Tasks ---")
            print("Filters: status (completed/pending), priority (low/medium/high), tag_id, search")
            print("Press Enter for defaults\n")

            page = input("Page number [default: 1]: ").strip()
            page = int(page) if page.isdigit() else 1

            status = input("Status (completed/pending) [optional]: ").strip().lower() or None
            if status not in ["completed", "pending"]:
                status = None

            priority = input("Priority (low/medium/high) [optional]: ").strip().lower() or None
            if priority not in ["low", "medium", "high"]:
                priority = None

            tag_id = input("Tag ID [optional]: ").strip() or None
            tag_id = int(tag_id) if tag_id and tag_id.isdigit() else None

            search = input("Search keyword [optional]: ").strip() or None

            include_archived = input("Include archived? (yes/no) [default: no]: ").strip().lower() == "yes"

            get_tasks(page=page, status=status, priority=priority, tag_id=tag_id, search=search, include_archived=include_archived)

        elif choice == "3":
            task_id = input("Task ID: ").strip()
            if not task_id.isdigit():
                print("❌ Invalid task ID")
                continue

            print("Leave field empty to skip update\n")

            title = input("New title [skip]: ").strip() or None
            description = input("New description [skip]: ").strip() or None

            completed = input("Completed? (yes/no/skip): ").strip().lower()
            if completed == "yes":
                completed = True
            elif completed == "no":
                completed = False
            else:
                completed = None

            priority = input("Priority (low/medium/high) [skip]: ").strip().lower() or None

            due_date = input("Due date (YYYY-MM-DD) [skip]: ").strip() or None
            if due_date == "":
                due_date = None

            reminder_date = input("Reminder date (YYYY-MM-DD) [skip]: ").strip() or None
            if reminder_date == "":
                reminder_date = None

            archived = input("Archive? (yes/no/skip): ").strip().lower()
            if archived == "yes":
                archived = True
            elif archived == "no":
                archived = False
            else:
                archived = None

            update_task(task_id, title, description, completed, priority, due_date, reminder_date, archived)

        elif choice == "4":
            task_id = input("Task ID: ").strip()
            if not task_id.isdigit():
                print("❌ Invalid task ID")
                continue
            delete_task(task_id)

        elif choice == "5":
            bulk_menu()

        elif choice == "6":
            tags_menu()

        elif choice == "7":
            get_due_reminders()

        elif choice == "8":
            logout()
            break

        elif choice == "9":
            password = input("Enter your password to confirm: ").strip()
            if delete_account(password):
                break

        elif choice.lower() in ["help", "h"]:
            print("""
Task Menu Help:
  1. Create Task - Add a new task with title, description, priority, due date, reminder
  2. View Tasks - List tasks with optional filters (status, priority, tag, search)
  3. Update Task - Modify task fields
  4. Delete Task - Remove a task permanently
  5. Bulk Operations - Complete, delete, or archive multiple tasks
  6. Tags Management - Create, view, delete tags and assign to tasks
  7. Reminders - View due task reminders
  8. Logout - Sign out
  9. Delete Account - Delete your account
""")

        else:
            print("❌ Invalid option")


# ----------------------------
# BULK OPERATIONS MENU
# ----------------------------
def bulk_menu():
    while True:
        print("\n--- Bulk Operations ---")
        print("1. Mark Complete (multiple)")
        print("2. Delete Multiple")
        print("3. Archive Multiple")
        print("4. Back")

        choice = input("Select option: ").strip()

        if choice == "4":
            break
        elif choice in ["1", "2", "3"]:
            task_ids_input = input("Enter task IDs (comma-separated): ").strip()
            task_ids = [int(t.strip()) for t in task_ids_input.split(",") if t.strip().isdigit()]

            if not task_ids:
                print("❌ No valid task IDs")
                continue

            if choice == "1":
                bulk_complete(task_ids)
            elif choice == "2":
                bulk_delete(task_ids)
            elif choice == "3":
                bulk_archive(task_ids)

        else:
            print("❌ Invalid option")


# ----------------------------
# TAGS MANAGEMENT MENU
# ----------------------------
def tags_menu():
    while True:
        print("\n--- Tags Management ---")
        print("1. Create Tag")
        print("2. View Tags")
        print("3. Delete Tag")
        print("4. Add Tag to Task")
        print("5. Remove Tag from Task")
        print("6. Back")

        choice = input("Select option: ").strip()

        if choice == "1":
            name = input("Tag name: ").strip()
            if name:
                create_tag(name)

        elif choice == "2":
            get_tags()

        elif choice == "3":
            tag_id = input("Tag ID: ").strip()
            if tag_id.isdigit():
                delete_tag(int(tag_id))

        elif choice == "4":
            task_id = input("Task ID: ").strip()
            tag_id = input("Tag ID: ").strip()
            if task_id.isdigit() and tag_id.isdigit():
                add_tag_to_task(int(task_id), int(tag_id))

        elif choice == "5":
            task_id = input("Task ID: ").strip()
            tag_id = input("Tag ID: ").strip()
            if task_id.isdigit() and tag_id.isdigit():
                remove_tag_from_task(int(task_id), int(tag_id))

        elif choice == "6":
            break

        else:
            print("❌ Invalid option")


# ----------------------------
# RUN PROGRAM
# ----------------------------
if __name__ == "__main__":
    start_app()
    auth_menu()