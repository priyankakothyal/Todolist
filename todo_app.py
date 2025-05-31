import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime, timedelta
from tkcalendar import Calendar
from tkinter import simpledialog
import random
import csv
import threading
import time

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ Task Manager")
        self.root.geometry("1000x1000")  # Increased height to show all buttons
        self.root.minsize(800, 800)  # Set minimum window size
        self.root.configure(bg="#f0f0f0")
        
        # Initialize tasks list and filter state
        self.tasks = []
        self.current_filter = "all"
        self.current_theme = "light"
        self.current_sort = "priority"
        self.reminder_thread = None
        self.stop_reminder_thread = False
        
        # Define categories and priorities
        self.categories = ["Work", "Personal", "Shopping", "Health", "Other"]
        self.priorities = ["High", "Medium", "Low"]
        
        # Theme colors
        self.theme_colors = {
            "light": {
                "bg": "#f0f0f0",
                "fg": "#2c3e50",
                "button_bg": "#3498db",
                "button_fg": "white",
                "listbox_bg": "white",
                "listbox_fg": "#2c3e50",
                "select_bg": "#3498db",
                "select_fg": "white"
            },
            "dark": {
                "bg": "#2c3e50",
                "fg": "#ecf0f1",
                "button_bg": "#34495e",
                "button_fg": "#ecf0f1",
                "listbox_bg": "#34495e",
                "listbox_fg": "#ecf0f1",
                "select_bg": "#3498db",
                "select_fg": "white"
            }
        }
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure("Custom.TFrame", background="#f0f0f0")
        self.style.configure("Custom.TButton",
                            padding=10,
                            font=('Helvetica', 10, 'bold'))
        self.style.configure("Title.TLabel",
                            font=('Helvetica', 24, 'bold'),
                            background="#f0f0f0",
                            foreground="#2c3e50")
        self.style.configure("Subtitle.TLabel",
                            font=('Helvetica', 12),
                            background="#f0f0f0",
                            foreground="#7f8c8d")
        self.style.configure("Stats.TLabel",
                            font=('Helvetica', 10),
                            background="#f0f0f0",
                            foreground="#34495e")
        
        # Configure progress bar style
        self.style.configure("Horizontal.TProgressbar",
                           troughcolor="#ecf0f1",
                           background="#3498db",
                           thickness=10)
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, style="Custom.TFrame", padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title and theme toggle
        self.title_frame = ttk.Frame(self.main_frame, style="Custom.TFrame")
        self.title_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.title_label = ttk.Label(self.title_frame,
                                   text="✨ Task Manager",
                                   style="Title.TLabel")
        self.title_label.grid(row=0, column=0, padx=(0, 20))
        
        self.theme_button = ttk.Button(self.title_frame,
                                     text="🌙 Dark Mode",
                                     command=self.toggle_theme,
                                     style="Custom.TButton")
        self.theme_button.grid(row=0, column=1)
        
        # Export/Import buttons
        self.export_button = ttk.Button(self.title_frame,
                                      text="📤 Export",
                                      command=self.export_tasks,
                                      style="Custom.TButton")
        self.export_button.grid(row=0, column=2, padx=5)
        
        self.import_button = ttk.Button(self.title_frame,
                                      text="📥 Import",
                                      command=self.import_tasks,
                                      style="Custom.TButton")
        self.import_button.grid(row=0, column=3, padx=5)
        
        # Stats frame
        self.stats_frame = ttk.Frame(self.main_frame, style="Custom.TFrame")
        self.stats_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.stats_label = ttk.Label(self.stats_frame,
                                   text="",
                                   style="Stats.TLabel")
        self.stats_label.grid(row=0, column=0)
        
        # Progress bars frame
        self.progress_frame = ttk.Frame(self.main_frame, style="Custom.TFrame")
        self.progress_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Priority progress bars
        self.priority_bars = {}
        for priority in self.priorities:
            frame = ttk.Frame(self.progress_frame, style="Custom.TFrame")
            frame.grid(row=0, column=self.priorities.index(priority), padx=10, sticky=(tk.W, tk.E))
            
            ttk.Label(frame, text=f"{priority} Priority", style="Stats.TLabel").pack()
            progress = ttk.Progressbar(frame, 
                                     length=200, 
                                     mode='determinate',
                                     style="Horizontal.TProgressbar")
            progress.pack(pady=5)
            self.priority_bars[priority] = progress
        
        # Search frame
        self.search_frame = ttk.Frame(self.main_frame, style="Custom.TFrame")
        self.search_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        self.search_entry = ttk.Entry(self.search_frame,
                                    textvariable=self.search_var,
                                    width=40,
                                    font=('Helvetica', 12))
        self.search_entry.grid(row=0, column=0, padx=(0, 10))
        self.search_entry.insert(0, "🔍 Search tasks...")
        self.search_entry.bind('<FocusIn>', lambda e: self.search_entry.delete(0, tk.END) if self.search_entry.get() == "🔍 Search tasks..." else None)
        self.search_entry.bind('<FocusOut>', lambda e: self.search_entry.insert(0, "🔍 Search tasks...") if not self.search_entry.get() else None)
        
        # Create task entry frame
        self.entry_frame = ttk.Frame(self.main_frame, style="Custom.TFrame")
        self.entry_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Task entry
        self.task_var = tk.StringVar()
        self.task_entry = ttk.Entry(self.entry_frame,
                                  textvariable=self.task_var,
                                  width=40,
                                  font=('Helvetica', 12))
        self.task_entry.grid(row=0, column=0, padx=(0, 10))
        
        # Category dropdown
        self.category_var = tk.StringVar(value="Work")
        self.category_dropdown = ttk.Combobox(self.entry_frame,
                                            textvariable=self.category_var,
                                            values=self.categories,
                                            width=10,
                                            font=('Helvetica', 12))
        self.category_dropdown.grid(row=0, column=1, padx=10)
        
        # Priority dropdown
        self.priority_var = tk.StringVar(value="Medium")
        self.priority_dropdown = ttk.Combobox(self.entry_frame,
                                            textvariable=self.priority_var,
                                            values=self.priorities,
                                            width=8,
                                            font=('Helvetica', 12))
        self.priority_dropdown.grid(row=0, column=2, padx=10)
        
        # Due date button
        self.due_date_var = tk.StringVar(value="No due date")
        self.due_date_button = ttk.Button(self.entry_frame,
                                        text="📅 Due Date",
                                        command=self.set_due_date,
                                        style="Custom.TButton")
        self.due_date_button.grid(row=0, column=3, padx=10)
        
        # Add task button
        self.add_button = ttk.Button(self.entry_frame,
                                   text="Add Task",
                                   command=self.add_task,
                                   style="Custom.TButton")
        self.add_button.grid(row=0, column=4)
        
        # Create task listbox with custom style
        self.task_listbox = tk.Listbox(self.main_frame,
                                     width=80,
                                     height=15,  # Reduced height to show buttons
                                     font=('Helvetica', 11),
                                     bg="white",
                                     fg="#2c3e50",
                                     selectbackground="#3498db",
                                     selectforeground="white",
                                     activestyle="none",
                                     borderwidth=0,
                                     highlightthickness=1,
                                     highlightbackground="#bdc3c7",
                                     highlightcolor="#3498db")
        self.task_listbox.grid(row=5, column=0, columnspan=3, pady=(0, 20), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Add scrollbar
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.task_listbox.yview)
        self.scrollbar.grid(row=5, column=3, sticky=(tk.N, tk.S))
        self.task_listbox.configure(yscrollcommand=self.scrollbar.set)
        
        # Create buttons frame
        self.button_frame = ttk.Frame(self.main_frame, style="Custom.TFrame")
        self.button_frame.grid(row=6, column=0, columnspan=4, pady=(0, 20))
        
        # Action buttons
        self.complete_button = ttk.Button(self.button_frame,
                                        text="✓ Complete",
                                        command=self.complete_task,
                                        style="Custom.TButton")
        self.complete_button.grid(row=0, column=0, padx=5)
        
        self.edit_button = ttk.Button(self.button_frame,
                                    text="✎ Edit",
                                    command=self.edit_task,
                                    style="Custom.TButton")
        self.edit_button.grid(row=0, column=1, padx=5)
        
        self.delete_button = ttk.Button(self.button_frame,
                                      text="🗑 Delete",
                                      command=self.delete_task,
                                      style="Custom.TButton")
        self.delete_button.grid(row=0, column=2, padx=5)
        
        # Sort options
        self.sort_label = ttk.Label(self.button_frame, text="Sort by:", style="Stats.TLabel")
        self.sort_label.grid(row=0, column=3, padx=(20, 5))
        
        self.sort_var = tk.StringVar(value="priority")
        self.sort_priority = ttk.Radiobutton(self.button_frame,
                                           text="Priority",
                                           variable=self.sort_var,
                                           value="priority",
                                           command=self.update_task_list)
        self.sort_priority.grid(row=0, column=4, padx=5)
        
        self.sort_date = ttk.Radiobutton(self.button_frame,
                                       text="Due Date",
                                       variable=self.sort_var,
                                       value="date",
                                       command=self.update_task_list)
        self.sort_date.grid(row=0, column=5, padx=5)
        
        self.sort_category = ttk.Radiobutton(self.button_frame,
                                           text="Category",
                                           variable=self.sort_var,
                                           value="category",
                                           command=self.update_task_list)
        self.sort_category.grid(row=0, column=6, padx=5)
        
        # Filter frame
        self.filter_frame = ttk.Frame(self.main_frame, style="Custom.TFrame")
        self.filter_frame.grid(row=7, column=0, columnspan=4, pady=(0, 20))
        
        # Filter buttons
        self.filter_all = ttk.Button(self.filter_frame,
                                   text="All",
                                   command=lambda: self.filter_tasks("all"),
                                   style="Custom.TButton")
        self.filter_all.grid(row=0, column=0, padx=5)
        
        self.filter_active = ttk.Button(self.filter_frame,
                                      text="Active",
                                      command=lambda: self.filter_tasks("active"),
                                      style="Custom.TButton")
        self.filter_active.grid(row=0, column=1, padx=5)
        
        self.filter_completed = ttk.Button(self.filter_frame,
                                        text="Completed",
                                        command=lambda: self.filter_tasks("completed"),
                                        style="Custom.TButton")
        self.filter_completed.grid(row=0, column=2, padx=5)
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(5, weight=1)  # Make task list expandable
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(2, weight=1)
        
        # Load tasks from file
        self.load_tasks()
        
        # Bind Enter key to add task
        self.task_entry.bind('<Return>', lambda e: self.add_task())
        
        # Set focus to entry
        self.task_entry.focus()
        
        # Update stats
        self.update_stats()
        
        # Start reminder thread
        self.start_reminder_thread()
    
    def start_reminder_thread(self):
        self.stop_reminder_thread = False
        self.reminder_thread = threading.Thread(target=self.check_reminders)
        self.reminder_thread.daemon = True
        self.reminder_thread.start()
    
    def check_reminders(self):
        while not self.stop_reminder_thread:
            now = datetime.now()
            for task in self.tasks:
                if not task["completed"] and task["due_date"] != "No due date":
                    due_date = datetime.strptime(task["due_date"], "%Y-%m-%d")
                    if due_date.date() == now.date():
                        self.root.after(0, lambda t=task: self.show_reminder(t))
            time.sleep(60)  # Check every minute
    
    def show_reminder(self, task):
        messagebox.showinfo("Task Reminder", f"Task due today: {task['task']}")
    
    def export_tasks(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Task", "Category", "Priority", "Due Date", "Completed", "Notes", "Tags"])
                    for task in self.tasks:
                        writer.writerow([
                            task["task"],
                            task["category"],
                            task["priority"],
                            task["due_date"],
                            task["completed"],
                            task.get("notes", ""),
                            ", ".join(task.get("tags", []))
                        ])
                messagebox.showinfo("Success", "Tasks exported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Error exporting tasks: {str(e)}")
    
    def import_tasks(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        task_data = {
                            "task": row["Task"],
                            "category": row["Category"],
                            "priority": row["Priority"],
                            "due_date": row["Due Date"],
                            "completed": row["Completed"].lower() == "true",
                            "notes": row["Notes"],
                            "tags": [tag.strip() for tag in row["Tags"].split(",") if tag.strip()],
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        self.tasks.append(task_data)
                self.update_task_list()
                self.save_tasks()
                messagebox.showinfo("Success", "Tasks imported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Error importing tasks: {str(e)}")
    
    def update_stats(self):
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for task in self.tasks if task["completed"])
        active_tasks = total_tasks - completed_tasks
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        stats_text = f"📊 Stats: {total_tasks} total tasks | {active_tasks} active | {completed_tasks} completed | {completion_rate:.1f}% completion rate"
        self.stats_label.configure(text=stats_text)
        
        # Update priority progress bars
        for priority in self.priorities:
            priority_tasks = [task for task in self.tasks if task["priority"] == priority]
            if priority_tasks:
                completed = sum(1 for task in priority_tasks if task["completed"])
                progress = (completed / len(priority_tasks)) * 100
                self.priority_bars[priority]["value"] = progress
            else:
                self.priority_bars[priority]["value"] = 0
    
    def on_search_change(self, *args):
        self.update_task_list()
    
    def set_due_date(self):
        date_window = tk.Toplevel(self.root)
        date_window.title("Select Due Date")
        date_window.geometry("300x300")
        
        cal = Calendar(date_window, selectmode='day', date_pattern='yyyy-mm-dd')
        cal.pack(pady=20)
        
        def set_date():
            selected_date = cal.get_date()
            self.due_date_var.set(selected_date)
            date_window.destroy()
        
        ttk.Button(date_window, text="Confirm", command=set_date).pack(pady=10)
    
    def add_task(self):
        task = self.task_var.get().strip()
        if task:
            task_data = {
                "task": task,
                "completed": False,
                "category": self.category_var.get(),
                "priority": self.priority_var.get(),
                "due_date": self.due_date_var.get(),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "notes": "",
                "tags": [],
                "dependencies": []  # New field for task dependencies
            }
            self.tasks.append(task_data)
            self.update_task_list()
            self.task_var.set("")
            self.due_date_var.set("No due date")
            self.save_tasks()
            self.task_entry.focus()
            self.update_stats()
        else:
            messagebox.showwarning("Warning", "Please enter a task!")
    
    def edit_task(self):
        try:
            selected_index = self.task_listbox.curselection()[0]
            task = self.tasks[selected_index]
            
            edit_window = tk.Toplevel(self.root)
            edit_window.title("Edit Task")
            edit_window.geometry("400x500")  # Increased height for new fields
            
            # Task text
            ttk.Label(edit_window, text="Task:").pack(pady=5)
            task_var = tk.StringVar(value=task["task"])
            task_entry = ttk.Entry(edit_window, textvariable=task_var, width=40)
            task_entry.pack(pady=5)
            
            # Category
            ttk.Label(edit_window, text="Category:").pack(pady=5)
            category_var = tk.StringVar(value=task["category"])
            category_dropdown = ttk.Combobox(edit_window, textvariable=category_var, values=self.categories)
            category_dropdown.pack(pady=5)
            
            # Priority
            ttk.Label(edit_window, text="Priority:").pack(pady=5)
            priority_var = tk.StringVar(value=task["priority"])
            priority_dropdown = ttk.Combobox(edit_window, textvariable=priority_var, values=self.priorities)
            priority_dropdown.pack(pady=5)
            
            # Dependencies
            ttk.Label(edit_window, text="Dependencies:").pack(pady=5)
            dependencies_var = tk.StringVar(value=", ".join(task.get("dependencies", [])))
            dependencies_entry = ttk.Entry(edit_window, textvariable=dependencies_var, width=40)
            dependencies_entry.pack(pady=5)
            ttk.Label(edit_window, text="(Enter task numbers separated by commas)").pack()
            
            # Notes
            ttk.Label(edit_window, text="Notes:").pack(pady=5)
            notes_text = tk.Text(edit_window, height=4, width=40)
            notes_text.insert("1.0", task.get("notes", ""))
            notes_text.pack(pady=5)
            
            # Tags
            ttk.Label(edit_window, text="Tags (comma-separated):").pack(pady=5)
            tags_var = tk.StringVar(value=", ".join(task.get("tags", [])))
            tags_entry = ttk.Entry(edit_window, textvariable=tags_var, width=40)
            tags_entry.pack(pady=5)
            
            def save_changes():
                task["task"] = task_var.get()
                task["category"] = category_var.get()
                task["priority"] = priority_var.get()
                task["notes"] = notes_text.get("1.0", tk.END).strip()
                task["tags"] = [tag.strip() for tag in tags_var.get().split(",") if tag.strip()]
                task["dependencies"] = [dep.strip() for dep in dependencies_var.get().split(",") if dep.strip()]
                self.update_task_list()
                self.save_tasks()
                edit_window.destroy()
            
            ttk.Button(edit_window, text="Save Changes", command=save_changes).pack(pady=20)
            
        except IndexError:
            messagebox.showwarning("Warning", "Please select a task!")
    
    def complete_task(self):
        try:
            selected_index = self.task_listbox.curselection()[0]
            self.tasks[selected_index]["completed"] = not self.tasks[selected_index]["completed"]
            self.update_task_list()
            self.save_tasks()
            self.update_stats()
        except IndexError:
            messagebox.showwarning("Warning", "Please select a task!")
    
    def delete_task(self):
        try:
            selected_index = self.task_listbox.curselection()[0]
            del self.tasks[selected_index]
            self.update_task_list()
            self.save_tasks()
            self.update_stats()
        except IndexError:
            messagebox.showwarning("Warning", "Please select a task!")
    
    def filter_tasks(self, filter_type):
        self.current_filter = filter_type
        self.update_task_list()
    
    def update_task_list(self):
        self.task_listbox.delete(0, tk.END)
        
        # Get search term
        search_term = self.search_var.get().lower()
        if search_term == "🔍 search tasks...":
            search_term = ""
        
        # Filter tasks based on current filter and search term
        filtered_tasks = self.tasks
        if self.current_filter == "active":
            filtered_tasks = [task for task in self.tasks if not task["completed"]]
        elif self.current_filter == "completed":
            filtered_tasks = [task for task in self.tasks if task["completed"]]
        
        # Apply search filter
        if search_term:
            filtered_tasks = [task for task in filtered_tasks if 
                            search_term in task["task"].lower() or
                            search_term in task["category"].lower() or
                            any(search_term in tag.lower() for tag in task.get("tags", []))]
        
        # Sort tasks
        if self.sort_var.get() == "priority":
            priority_order = {"High": 0, "Medium": 1, "Low": 2}
            filtered_tasks.sort(key=lambda x: (priority_order[x["priority"]], x["due_date"]))
        elif self.sort_var.get() == "date":
            filtered_tasks.sort(key=lambda x: (x["due_date"] if x["due_date"] != "No due date" else "9999-99-99"))
        elif self.sort_var.get() == "category":
            filtered_tasks.sort(key=lambda x: (x["category"], x["priority"]))
        
        for i, task in enumerate(filtered_tasks, 1):
            # Create task display string
            prefix = "✓ " if task["completed"] else "○ "
            priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[task["priority"]]
            category_emoji = {"Work": "💼", "Personal": "👤", "Shopping": "🛒", "Health": "❤️", "Other": "📌"}[task["category"]]
            
            task_display = f"{i}. {prefix}{priority_emoji} {category_emoji} {task['task']}"
            if task["due_date"] != "No due date":
                task_display += f" 📅 {task['due_date']}"
            if task.get("tags"):
                task_display += f" 🏷️ {', '.join(task['tags'])}"
            if task.get("notes"):
                task_display += f" 📝"
            if task.get("dependencies"):
                task_display += f" 🔗"
            
            self.task_listbox.insert(tk.END, task_display)
            
            # Set color based on completion status
            color = "#95a5a6" if task["completed"] else "#2c3e50"
            if self.current_theme == "dark":
                color = "#7f8c8d" if task["completed"] else "#ecf0f1"
            self.task_listbox.itemconfig(tk.END, fg=color)
    
    def save_tasks(self):
        with open("tasks.json", "w") as f:
            json.dump(self.tasks, f)
    
    def load_tasks(self):
        try:
            if os.path.exists("tasks.json"):
                with open("tasks.json", "r") as f:
                    self.tasks = json.load(f)
                self.update_task_list()
                self.update_stats()
        except Exception as e:
            messagebox.showerror("Error", f"Error loading tasks: {str(e)}")
    
    def __del__(self):
        self.stop_reminder_thread = True
        if self.reminder_thread:
            self.reminder_thread.join(timeout=1.0)
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        if self.current_theme == "light":
            self.current_theme = "dark"
            self.theme_button.configure(text="☀️ Light Mode")
        else:
            self.current_theme = "light"
            self.theme_button.configure(text="🌙 Dark Mode")
        
        colors = self.theme_colors[self.current_theme]
        
        # Update root window
        self.root.configure(bg=colors["bg"])
        
        # Update styles
        self.style.configure("Custom.TFrame", background=colors["bg"])
        self.style.configure("Title.TLabel", 
                           background=colors["bg"], 
                           foreground=colors["fg"])
        self.style.configure("Subtitle.TLabel", 
                           background=colors["bg"], 
                           foreground=colors["fg"])
        self.style.configure("Stats.TLabel", 
                           background=colors["bg"], 
                           foreground=colors["fg"])
        
        # Update progress bar style
        self.style.configure("Horizontal.TProgressbar",
                           troughcolor=colors["bg"],
                           background=colors["button_bg"],
                           thickness=10)
        
        # Update listbox
        self.task_listbox.configure(
            bg=colors["listbox_bg"],
            fg=colors["listbox_fg"],
            selectbackground=colors["select_bg"],
            selectforeground=colors["select_fg"]
        )
        
        # Update task list colors
        self.update_task_list()

if __name__ == "__main__":
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop() 