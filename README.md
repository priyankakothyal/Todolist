# Todo List Application

A simple and intuitive todo list application built with Python and Tkinter.

## Features

- Add new tasks
- Mark tasks as complete/incomplete
- Delete tasks
- Persistent storage (tasks are saved to a file)
- Clean and user-friendly interface

## Requirements

- Python 3.x
- Tkinter (usually comes with Python installation)

## How to Run

1. Make sure you have Python installed on your system
2. Run the application using:
   ```
   python todo_app.py
   ```

## How to Use

1. **Adding a Task**
   - Type your task in the text field
   - Press Enter or click the "Add Task" button

2. **Completing a Task**
   - Select a task from the list
   - Click the "Mark Complete" button
   - The task will be marked with a checkmark (✓)

3. **Deleting a Task**
   - Select a task from the list
   - Click the "Delete Task" button

## Data Storage

Tasks are automatically saved to a `tasks.json` file in the same directory as the application. The tasks will persist between sessions. 