import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import time
import sqlite3
import random
import string
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import csv
import os

# Initialize database with improved schema
conn = sqlite3.connect("typing_test.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wpm REAL,
    accuracy REAL,
    test_duration REAL,
    test_length INTEGER,
    difficulty TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

class TypingSpeedTest:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Typing Speed Test")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Arial', 11))
        self.style.configure('TButton', font=('Arial', 10))
        self.style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        
        # Application variables
        self.sample_texts = {
            'easy': [
                "The quick brown fox jumps over the lazy dog.",
                "Programming is fun with Python and Tkinter.",
                "Practice makes perfect when learning to type quickly."
            ],
            'medium': [
                "The Python interpreter is a virtual machine that executes bytecode.",
                "Computer science is no more about computers than astronomy is about telescopes.",
                "The best way to predict the future is to invent it."
            ],
            'hard': [
                "The Zen of Python states: Explicit is better than implicit, simple is better than complex.",
                "In computer science, a hash table is a data structure that implements an associative array.",
                "Asymptotic analysis provides estimates of time and space complexity for algorithms."
            ]
        }
        
        self.current_difficulty = 'medium'
        self.sample_text = ""
        self.start_time = None
        self.end_time = None
        self.typed_text = ""
        self.running = False
        self.test_duration = 0
        self.caps_lock_on = False
        self.dark_mode = False
        
        # Create GUI
        self.create_widgets()
        self.generate_sample_text()
        
        # Check caps lock initially
        self.root.bind('<KeyPress>', self.check_caps_lock)
        
    def create_widgets(self):
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Advanced Typing Speed Test", style='Title.TLabel').pack(side=tk.LEFT)
        
        # Theme toggle button
        self.theme_btn = ttk.Button(header_frame, text="☀️", width=3, 
                                   command=self.toggle_theme)
        self.theme_btn.pack(side=tk.RIGHT, padx=5)
        
        # Caps lock indicator
        self.caps_lock_label = ttk.Label(header_frame, text="CAPS", foreground='red')
        self.caps_lock_label.pack(side=tk.RIGHT, padx=5)
        self.caps_lock_label.pack_forget()
        
        # Content frame
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel (controls and stats)
        left_panel = ttk.Frame(content_frame, width=200)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Test controls
        controls_frame = ttk.LabelFrame(left_panel, text="Test Controls")
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(controls_frame, text="Start Test", command=self.start_test).pack(fill=tk.X, pady=2)
        self.reset_btn = ttk.Button(controls_frame, text="Reset", state=tk.DISABLED, 
                                  command=self.reset_test)
        self.reset_btn.pack(fill=tk.X, pady=2)
        
        # Difficulty selection
        diff_frame = ttk.LabelFrame(left_panel, text="Difficulty")
        diff_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.diff_var = tk.StringVar(value=self.current_difficulty)
        ttk.Radiobutton(diff_frame, text="Easy", variable=self.diff_var, 
                       value='easy', command=self.change_difficulty).pack(anchor=tk.W)
        ttk.Radiobutton(diff_frame, text="Medium", variable=self.diff_var, 
                       value='medium', command=self.change_difficulty).pack(anchor=tk.W)
        ttk.Radiobutton(diff_frame, text="Hard", variable=self.diff_var, 
                       value='hard', command=self.change_difficulty).pack(anchor=tk.W)
        
        # Test customization
        custom_frame = ttk.LabelFrame(left_panel, text="Custom Test")
        custom_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(custom_frame, text="Random Characters", 
                  command=lambda: self.set_custom_test('random')).pack(fill=tk.X, pady=2)
        ttk.Button(custom_frame, text="Custom Text", 
                  command=lambda: self.set_custom_test('custom')).pack(fill=tk.X, pady=2)
        
        # Statistics
        stats_frame = ttk.LabelFrame(left_panel, text="Statistics")
        stats_frame.pack(fill=tk.X)
        
        self.stats_text = tk.Text(stats_frame, height=10, width=25, 
                                font=('Arial', 9), wrap=tk.WORD)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        self.update_stats()
        
        # Right panel (typing area)
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Sample text display with scrollbar
        sample_frame = ttk.LabelFrame(right_panel, text="Type the following text:")
        sample_frame.pack(fill=tk.BOTH, pady=(0, 10))
        
        self.sample_text_display = tk.Text(sample_frame, height=8, wrap=tk.WORD, 
                                         font=('Arial', 12), padx=5, pady=5)
        scrollbar = ttk.Scrollbar(sample_frame, command=self.sample_text_display.yview)
        self.sample_text_display.configure(yscrollcommand=scrollbar.set)
        
        self.sample_text_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Typing area with scrollbar
        typing_frame = ttk.LabelFrame(right_panel, text="Your typing:")
        typing_frame.pack(fill=tk.BOTH, expand=True)
        
        self.typing_entry = tk.Text(typing_frame, height=10, wrap=tk.WORD, 
                                   font=('Arial', 12), padx=5, pady=5)
        scrollbar2 = ttk.Scrollbar(typing_frame, command=self.typing_entry.yview)
        self.typing_entry.configure(yscrollcommand=scrollbar2.set)
        
        self.typing_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        self.typing_entry.bind("<KeyRelease>", self.check_typing)
        
        # Results display
        results_frame = ttk.Frame(right_panel)
        results_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.wpm_label = ttk.Label(results_frame, text="WPM: 0", font=('Arial', 12, 'bold'))
        self.wpm_label.pack(side=tk.LEFT, padx=5)
        
        self.accuracy_label = ttk.Label(results_frame, text="Accuracy: 0%", font=('Arial', 12, 'bold'))
        self.accuracy_label.pack(side=tk.LEFT, padx=5)
        
        self.time_label = ttk.Label(results_frame, text="Time: 0s", font=('Arial', 12, 'bold'))
        self.time_label.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(results_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        
        # Bottom panel (additional controls)
        bottom_panel = ttk.Frame(self.main_frame)
        bottom_panel.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(bottom_panel, text="View History", command=self.show_history).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom_panel, text="View Progress", command=self.show_progress).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom_panel, text="Export Results", command=self.export_results).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom_panel, text="Help", command=self.show_help).pack(side=tk.RIGHT, padx=2)
    
    def toggle_theme(self):
        """Toggle between light and dark mode."""
        self.dark_mode = not self.dark_mode
        
        if self.dark_mode:
            self.theme_btn.config(text="🌙")
            bg_color = '#2d2d2d'
            fg_color = '#ffffff'
            entry_bg = '#3d3d3d'
            entry_fg = '#ffffff'
        else:
            self.theme_btn.config(text="☀️")
            bg_color = '#f0f0f0'
            fg_color = '#000000'
            entry_bg = '#ffffff'
            entry_fg = '#000000'
        
        # Update all widgets
        self.style.configure('.', background=bg_color, foreground=fg_color)
        self.root.configure(background=bg_color)
        
        # Update text widgets
        for widget in [self.sample_text_display, self.typing_entry, self.stats_text]:
            widget.configure(
                background=entry_bg,
                foreground=entry_fg,
                insertbackground=fg_color
            )
    
    def check_caps_lock(self, event):
        """Check if caps lock is on and update indicator."""
        if event.keysym == 'Caps_Lock':
            self.caps_lock_on = not self.caps_lock_on
        
        # Check the actual state by looking at the shift state
        if event.state & 0x0001:
            self.caps_lock_on = True
        else:
            self.caps_lock_on = False
        
        if self.caps_lock_on:
            self.caps_lock_label.pack(side=tk.RIGHT, padx=5)
        else:
            self.caps_lock_label.pack_forget()
    
    def change_difficulty(self):
        """Change the difficulty level and generate new text."""
        self.current_difficulty = self.diff_var.get()
        self.generate_sample_text()
    
    def generate_sample_text(self):
        """Generate sample text based on current difficulty."""
        texts = self.sample_texts[self.current_difficulty]
        self.sample_text = random.choice(texts)
        self.display_sample_text()
    
    def display_sample_text(self):
        """Display the sample text in the text widget."""
        self.sample_text_display.config(state=tk.NORMAL)
        self.sample_text_display.delete(1.0, tk.END)
        self.sample_text_display.insert(tk.END, self.sample_text)
        self.sample_text_display.config(state=tk.DISABLED)
        self.typing_entry.focus()
    
    def set_custom_test(self, test_type):
        """Set up a custom test."""
        if test_type == 'random':
            length = simpledialog.askinteger("Random Characters", 
                                           "How many characters?", 
                                           parent=self.root,
                                           minvalue=10, maxvalue=1000)
            if length:
                # Generate random characters (letters, numbers, symbols)
                chars = string.ascii_letters + string.digits + string.punctuation + ' '
                self.sample_text = ''.join(random.choice(chars) for _ in range(length))
                self.display_sample_text()
        elif test_type == 'custom':
            text = simpledialog.askstring("Custom Text", 
                                        "Enter your custom text:", 
                                        parent=self.root)
            if text and text.strip():
                self.sample_text = text.strip()
                self.display_sample_text()
    
    def start_test(self):
        """Start the typing test."""
        if not self.running:
            self.running = True
            self.start_time = time.time()
            self.typed_text = ""
            self.typing_entry.delete(1.0, tk.END)
            self.reset_btn.config(state=tk.NORMAL)
            self.progress['value'] = 0
            self.update_timer()
    
    def reset_test(self):
        """Reset the current test."""
        self.running = False
        self.start_time = None
        self.typed_text = ""
        self.typing_entry.delete(1.0, tk.END)
        self.reset_btn.config(state=tk.DISABLED)
        self.wpm_label.config(text="WPM: 0")
        self.accuracy_label.config(text="Accuracy: 0%")
        self.time_label.config(text="Time: 0s")
        self.progress['value'] = 0
        if hasattr(self, 'timer_id'):
            self.root.after_cancel(self.timer_id)
    
    def update_timer(self):
        """Update the timer display during the test."""
        if self.running:
            elapsed = time.time() - self.start_time
            self.time_label.config(text=f"Time: {elapsed:.1f}s")
            self.timer_id = self.root.after(100, self.update_timer)
    
    def check_typing(self, event):
        """Check the user's typing against the sample text."""
        if not self.running:
            return
        
        self.typed_text = self.typing_entry.get(1.0, tk.END).strip()
        self.end_time = time.time()
        
        # Calculate test duration
        self.test_duration = self.end_time - self.start_time
        
        # Calculate WPM (Words Per Minute)
        words_typed = len(self.typed_text.split())
        minutes = self.test_duration / 60
        wpm = words_typed / minutes if minutes > 0 else 0
        
        # Calculate Accuracy
        correct_chars = 0
        min_length = min(len(self.sample_text), len(self.typed_text))
        
        for i in range(min_length):
            if self.sample_text[i] == self.typed_text[i]:
                correct_chars += 1
        
        total_chars = max(len(self.sample_text), len(self.typed_text))
        accuracy = (correct_chars / total_chars) * 100 if total_chars > 0 else 0
        
        # Update progress
        progress = (len(self.typed_text) / len(self.sample_text)) * 100
        self.progress['value'] = min(progress, 100)
        
        # Update display
        self.wpm_label.config(text=f"WPM: {wpm:.1f}")
        self.accuracy_label.config(text=f"Accuracy: {accuracy:.1f}%")
        
        # Color feedback for accuracy
        if accuracy > 90:
            self.accuracy_label.config(foreground='green')
        elif accuracy > 70:
            self.accuracy_label.config(foreground='orange')
        else:
            self.accuracy_label.config(foreground='red')
        
        # Auto-save when full text is typed or time limit reached
        if len(self.typed_text) >= len(self.sample_text) or self.test_duration >= 300:  # 5-minute limit
            self.save_result(wpm, accuracy)
            self.reset_test()
    
    def save_result(self, wpm, accuracy):
        """Save the test results to the database."""
        cursor.execute(
            "INSERT INTO results (wpm, accuracy, test_duration, test_length, difficulty) VALUES (?, ?, ?, ?, ?)",
            (wpm, accuracy, self.test_duration, len(self.sample_text), self.current_difficulty)
        )
        conn.commit()
        
        # Show results
        result_str = f"Test Complete!\n\nWPM: {wpm:.1f}\nAccuracy: {accuracy:.1f}%\n"
        result_str += f"Time: {self.test_duration:.1f}s\nDifficulty: {self.current_difficulty.capitalize()}"
        
        messagebox.showinfo("Results", result_str)
        self.update_stats()
    
    def update_stats(self):
        """Update statistics display with database results."""
        try:
            # Initialize default values
            total_tests = 0
            avg_wpm = 0.0
            max_wpm = 0.0
            avg_acc = 0.0
            difficulty_stats = []

            # Get basic stats
            cursor.execute("SELECT COUNT(*) FROM results")
            total_tests = cursor.fetchone()[0] or 0

            if total_tests > 0:
                cursor.execute("SELECT AVG(wpm), MAX(wpm), AVG(accuracy) FROM results")
                stats = cursor.fetchone()
                avg_wpm = stats[0] or 0.0
                max_wpm = stats[1] or 0.0
                avg_acc = stats[2] or 0.0

                # Get difficulty stats if difficulty column exists
                cursor.execute("PRAGMA table_info(results)")
                columns = [column[1] for column in cursor.fetchall()]
                if 'difficulty' in columns:
                    cursor.execute("""
                        SELECT difficulty, AVG(wpm), AVG(accuracy), COUNT(*) 
                        FROM results 
                        GROUP BY difficulty
                    """)
                    difficulty_stats = cursor.fetchall()

            # Build stats text
            stats_text = f"Total Tests: {total_tests}\n"
            if total_tests > 0:
                stats_text += f"Average WPM: {avg_wpm:.1f}\n"
                stats_text += f"Best WPM: {max_wpm:.1f}\n"
                stats_text += f"Average Accuracy: {avg_acc:.1f}%\n"
                
                if difficulty_stats:
                    stats_text += "\nBy Difficulty:\n"
                    for row in difficulty_stats:
                        diff = row[0]
                        wpm = row[1] or 0.0
                        acc = row[2] or 0.0
                        count = row[3] or 0
                        stats_text += f"\n{diff.capitalize()}:\n"
                        stats_text += f"  Tests: {count}\n"
                        stats_text += f"  Avg WPM: {wpm:.1f}\n"
                        stats_text += f"  Avg Acc: {acc:.1f}%\n"
            else:
                stats_text += "\nNo test data available"

            # Update display
            self.stats_text.config(state=tk.NORMAL)
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, stats_text)
            self.stats_text.config(state=tk.DISABLED)
    
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error accessing database: {str(e)}")
    
    def show_history(self):
        """Show a window with test history."""
        history_window = tk.Toplevel(self.root)
        history_window.title("Test History")
        history_window.geometry("800x500")
        
        # Create a treeview to display results
        columns = ("id", "wpm", "accuracy", "duration", "length", "difficulty", "timestamp")
        tree = ttk.Treeview(history_window, columns=columns, show="headings")
        
        # Define headings
        tree.heading("id", text="ID")
        tree.heading("wpm", text="WPM")
        tree.heading("accuracy", text="Accuracy")
        tree.heading("duration", text="Duration (s)")
        tree.heading("length", text="Length")
        tree.heading("difficulty", text="Difficulty")
        tree.heading("timestamp", text="Date/Time")
        
        # Configure columns
        tree.column("id", width=40, anchor=tk.CENTER)
        tree.column("wpm", width=60, anchor=tk.CENTER)
        tree.column("accuracy", width=70, anchor=tk.CENTER)
        tree.column("duration", width=80, anchor=tk.CENTER)
        tree.column("length", width=60, anchor=tk.CENTER)
        tree.column("difficulty", width=80, anchor=tk.CENTER)
        tree.column("timestamp", width=150, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(history_window, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Load data
        cursor.execute("SELECT * FROM results ORDER BY timestamp DESC")
        for row in cursor.fetchall():
            tree.insert("", tk.END, values=row)
        
        # Add delete button
        def delete_selected():
            selected = tree.selection()
            if not selected:
                return
            
            for item in selected:
                test_id = tree.item(item)['values'][0]
                cursor.execute("DELETE FROM results WHERE id = ?", (test_id,))
                conn.commit()
                tree.delete(item)
            
            self.update_stats()
        
        delete_btn = ttk.Button(history_window, text="Delete Selected", command=delete_selected)
        delete_btn.pack(pady=5)
    
    def show_progress(self):
        """Show a progress chart of WPM over time."""
        cursor.execute("SELECT timestamp, wpm, difficulty FROM results ORDER BY timestamp")
        results = cursor.fetchall()
        
        if not results:
            messagebox.showinfo("No Data", "No test results available to show progress.")
            return
        
        # Prepare data
        dates = []
        wpms = []
        difficulties = []
        
        for row in results:
            try:
                # Handle different timestamp formats
                timestamp_str = row[0]
                if '.' in timestamp_str:  # Contains fractional seconds
                    dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
                else:
                    dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                dates.append(dt)
                wpms.append(row[1])
                difficulties.append(row[2])
            except ValueError:
                continue
        
        if not dates:
            messagebox.showinfo("No Data", "No valid test results to show progress.")
            return
        
        # Create figure
        fig, ax = plt.subplots(figsize=(8, 5))
        
        # Plot WPM over time with color coding by difficulty
        colors = {'easy': 'green', 'medium': 'blue', 'hard': 'red'}
        for i in range(len(dates)):
            ax.scatter(dates[i], wpms[i], color=colors.get(difficulties[i], 'black'))
        
        # Add trend line using built-in functions
        if len(dates) > 1:
            try:
                date_nums = [d.timestamp() for d in dates]
                # Simple linear regression
                n = len(date_nums)
                sum_x = sum(date_nums)
                sum_y = sum(wpms)
                sum_xy = sum(x * y for x, y in zip(date_nums, wpms))
                sum_x2 = sum(x*x for x in date_nums)
                
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
                intercept = (sum_y - slope * sum_x) / n
                
                # Create trend line points
                trend_x = [min(date_nums), max(date_nums)]
                trend_y = [slope * x + intercept for x in trend_x]
                trend_dates = [datetime.fromtimestamp(x) for x in trend_x]
                
                ax.plot(trend_dates, trend_y, "r--", linewidth=1, label='Trend')
            except ZeroDivisionError:
                pass
        
        # Format plot
        ax.set_title("Typing Speed Progress")
        ax.set_xlabel("Date")
        ax.set_ylabel("WPM")
        ax.grid(True)
        fig.autofmt_xdate()
        
        # Add legend for difficulties
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', label='Easy', 
                  markerfacecolor='green', markersize=10),
            Line2D([0], [0], marker='o', color='w', label='Medium', 
                  markerfacecolor='blue', markersize=10),
            Line2D([0], [0], marker='o', color='w', label='Hard', 
                  markerfacecolor='red', markersize=10)
        ]
        
        # Only add trend to legend if we have a trend line
        if len(dates) > 1:
            legend_elements.append(Line2D([0], [0], color='red', linestyle='--', label='Trend'))
        
        ax.legend(handles=legend_elements)
        
        # Display in Tkinter window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Typing Progress")
        
        canvas = FigureCanvasTkAgg(fig, master=progress_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add close button
        ttk.Button(progress_window, text="Close", 
                  command=progress_window.destroy).pack(pady=5)
    
    def export_results(self):
        """Export test results to a CSV file."""
        from tkinter import filedialog
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Save Results As"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                # Write header
                writer.writerow([
                    "ID", "WPM", "Accuracy", "Duration (s)", 
                    "Text Length", "Difficulty", "Timestamp"
                ])
                
                # Write data
                cursor.execute("SELECT * FROM results ORDER BY timestamp")
                for row in cursor.fetchall():
                    writer.writerow(row)
            
            messagebox.showinfo("Success", f"Results exported to {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def show_help(self):
        """Show help information."""
        help_text = """
        Advanced Typing Speed Test Help
        
        How to Use:
        1. Select a difficulty level (Easy, Medium, Hard)
        2. Click "Start Test" to begin typing
        3. Type the text shown in the top box
        4. Your speed (WPM) and accuracy will be displayed
        
        Features:
        - Multiple difficulty levels
        - Custom text options
        - Progress tracking
        - Detailed statistics
        - Dark/light theme
        
        Tips:
        - Try to maintain accuracy over speed
        - Practice regularly to see improvement
        - Use the progress charts to track your performance
        
        Keyboard Shortcuts:
        - Ctrl+Enter: Start/Reset test
        - Ctrl+D: Change difficulty
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Help")
        
        text = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        text.insert(tk.END, help_text)
        text.config(state=tk.DISABLED)
        text.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(help_window, text="Close", command=help_window.destroy).pack(pady=5)

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = TypingSpeedTest(root)
    root.mainloop()
    conn.close()