from Authentication.auth_service import register_user, login_user, logout, get_current_user, delete_account
from Tasks.task_service import create_task, get_tasks, update_task, delete_task
from database.db import create_tables


# ----------------------------
# INITIAL SETUP
# ----------------------------
def start_app():
    create_tables()
    print("\n🚀 Welcome to Task Manager CLI\n")


# ----------------------------
# AUTH MENU
# ----------------------------
def auth_menu():
    while True:
        print("\n===== AUTH MENU =====")
        print("1. Register")
        print("2. Login")
        print("3. Exit")

        choice = input("Select option: ")

        if choice == "1":
            email = input("Enter email: ")
            password = input("Enter password: ")
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

        else:
            print("❌ Invalid option")


# ----------------------------
# TASK MENU
# ----------------------------
def task_menu():
    user = get_current_user()
    while user:
        print(f"\n===== TASK MENU (User: {user['email']}) =====")
        print("1. Create Task")
        print("2. View Tasks")
        print("3. Update Task")
        print("4. Delete Task")
        print("5. Logout")
        print("6. Delete Account")

        choice = input("Select option: ")

        if choice == "1":
            title = input("Task title: ")
            create_task(title)

        elif choice == "2":
            get_tasks()

        elif choice == "3":
            task_id = input("Task ID: ")
            title = input("New title (leave blank to skip): ")
            completed = input("Completed? (yes/no/skip): ")

            title = title if title else None

            if completed.lower() == "yes":
                completed = True
            elif completed.lower() == "no":
                completed = False
            else:
                completed = None

            update_task(task_id, title, completed)

        elif choice == "4":
            task_id = input("Task ID: ")
            delete_task(task_id)

        elif choice == "5":
            logout()
            break

        elif choice == "6":
            password = input("Enter your password to confirm: ")
            if delete_account(password):
                break

        else:
            print("❌ Invalid option")


# ----------------------------
# RUN PROGRAM
# ----------------------------
if __name__ == "__main__":
    start_app()
    auth_menu()