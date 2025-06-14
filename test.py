tasks = []

def add_task():
    title = input("Enter task title: ")
    tasks.append({"title": title})
    print("✅ Task added.")
