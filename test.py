
from task_manager import add_task, list_tasks, delete_task, update_task

def menu():
    while True:
        print("\n📝 Smart Task Manager")
        print("1. Add Task")
        print("2. List Tasks")
        print("3. Delete Task")
        print("4. Update Task")
        print("0. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            add_task()
        elif choice == "2":
            list_tasks()
        elif choice == "3":
            delete_task()
        elif choice == "4":
            update_task()
        elif choice == "0":
            print("👋 Exiting.")
            break
        else:
            print("❌ Invalid choice.")

menu()
