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
    list_tasks()
    if tasks:
        idx = int(input("Enter task number to update: ")) - 1
        if 0 <= idx < len(tasks):
            new_title = input("Enter new title: ")
            tasks[idx]['title'] = new_title
            print("✏️ Task updated.")
        else:
            print("❌ Invalid task number.")
