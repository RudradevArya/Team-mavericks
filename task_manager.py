tasks = []

def add_task():
    title = input("Enter task title: ")
    tasks.append({"title": title})
    print("✅ Task added.")

def list_tasks():
    if not tasks:
        print("📭 No tasks yet.")
        return
    for i, task in enumerate(tasks, start=1):
        print(f"{i}. {task['title']}")

def delete_task():
    list_tasks()
    if tasks:
        idx = int(input("Enter task number to delete: ")) - 1
        if 0 <= idx < len(tasks):
            deleted = tasks.pop(idx)
            print(f"🗑️ Deleted: {deleted['title']}")
        else:
            print("❌ Invalid task number.")

def update_task():
    if not tasks:
        print("📭 No tasks to update.")
        return

    list_tasks()
    try:
        idx = int(input("Enter task number to update: ")) - 1
        if idx not in range(len(tasks)):
            print("❌ Invalid task number.")
            return

        current_title = tasks[idx]['title']
        new_title = input(f"Enter new title (current: '{current_title}'): ").strip()
        if new_title:
            tasks[idx]['title'] = new_title
            print("✏️ Task updated.")
        else:
            print("⚠️ Title cannot be empty. Task not updated.")
    except ValueError:
        print("❌ Please enter a valid number.")

