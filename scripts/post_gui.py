#!/usr/bin/env python3
import os
import sys
import tkinter as tk
from tkinter import filedialog, ttk
from datetime import datetime
from pathlib import Path

from post_generator import PostGenerator
from sync_db import DatabaseSyncService

class PostCreatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Post Creator")
        self.root.geometry("600x400")  # Reduced height since we removed Obsidian selection
        
        # Variables to store user input
        self.file_path = tk.StringVar()
        self.post_title = tk.StringVar()
        self.post_date = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        self.post_type = tk.StringVar(value="works")  # Default to "works"
        
        # Create GUI elements
        self._create_widgets()
        
    def _create_widgets(self):
        # File selection
        file_frame = ttk.LabelFrame(self.root, text="Markdown File", padding="10")
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path, width=50)
        file_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="Browse...", command=self._browse_file).pack(side=tk.LEFT)
        
        # Post details
        details_frame = ttk.LabelFrame(self.root, text="Post Details", padding="10")
        details_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Title input
        title_frame = ttk.Frame(details_frame)
        title_frame.pack(fill=tk.X, pady=5)
        ttk.Label(title_frame, text="Title:").pack(side=tk.LEFT)
        ttk.Entry(title_frame, textvariable=self.post_title, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Date input
        date_frame = ttk.Frame(details_frame)
        date_frame.pack(fill=tk.X, pady=5)
        ttk.Label(date_frame, text="Date:").pack(side=tk.LEFT)
        ttk.Entry(date_frame, textvariable=self.post_date, width=20).pack(side=tk.LEFT, padx=5)
        
        # Post type selection
        type_frame = ttk.Frame(details_frame)
        type_frame.pack(fill=tk.X, pady=5)
        ttk.Label(type_frame, text="Type:").pack(side=tk.LEFT)
        ttk.Radiobutton(type_frame, text="Works", variable=self.post_type, value="works").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="Blog", variable=self.post_type, value="blog").pack(side=tk.LEFT, padx=5)
        
        # Status message
        status_frame = ttk.LabelFrame(self.root, text="Status", padding="10")
        status_frame.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)
        
        self.status_text = tk.Text(status_frame, wrap=tk.WORD, height=8, state=tk.DISABLED)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        # Add scrollbar for status
        scrollbar = ttk.Scrollbar(status_frame, command=self.status_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        # Create button
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=tk.X)
        ttk.Button(button_frame, text="Create Post", command=self._create_post).pack(pady=10)
        
    def _browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Markdown File",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )
        if file_path:
            self.file_path.set(file_path)
            # Auto-fill title from filename if title is empty
            if not self.post_title.get():
                self.post_title.set(Path(file_path).stem)
    
    def _log_status(self, message):
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.root.update()
        
    def _create_post(self):
        # Clear status
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)
        
        # Validate inputs
        if not self.file_path.get():
            self._log_status("Error: Please select a markdown file.")
            return
        
        file_path = Path(self.file_path.get())
        if not file_path.exists():
            self._log_status(f"Error: File {file_path} does not exist.")
            return
        
        if not self.post_title.get():
            self._log_status("Error: Please enter a post title.")
            return
        
        try:
            datetime.strptime(self.post_date.get(), '%Y-%m-%d')
        except ValueError:
            self._log_status("Error: Date must be in YYYY-MM-DD format.")
            return
        
        # Set environment variables
        os.environ['POST_TYPE'] = self.post_type.get()
        os.environ['POST_TITLE'] = self.post_title.get()
        os.environ['POST_DATE'] = self.post_date.get()
        
        # Get the file path relative to the Obsidian mount
        obsidian_dir = "/app/obsidian"  # This matches your Docker mount
        
        try:
            # Try to make the path relative to the Obsidian directory
            abs_file_path = str(file_path.absolute())
            if abs_file_path.startswith(obsidian_dir):
                # File is already in the mounted Obsidian directory
                docker_file_path = abs_file_path
            else:
                # File is outside the Obsidian directory, can't use it directly
                self._log_status(f"Error: File must be in the Obsidian directory: {obsidian_dir}")
                return
                
            os.environ['POST_PATH'] = docker_file_path
            os.environ['OBSIDIAN_PATH'] = '/input/obsidian'  # Path for PostGenerator to use
            
            self._log_status(f"Using file path: {docker_file_path}")
        except Exception as e:
            self._log_status(f"Error with file path: {str(e)}")
            return
        
        self._log_status("Creating post...")
        
        try:
            # Generate post
            generator = PostGenerator()
            output_dir = generator.generate()
            
            self._log_status(f"Post generated successfully in {output_dir}")
            
            # Sync database
            self._log_status("Syncing database...")
            sync_service = DatabaseSyncService()
            sync_service.sync_database()
            
            self._log_status("Database synced successfully!")
            self._log_status("Your website has been updated with the new post.")
            
        except Exception as e:
            self._log_status(f"Error: {str(e)}")
            import traceback
            self._log_status(traceback.format_exc())

if __name__ == "__main__":
    root = tk.Tk()
    app = PostCreatorGUI(root)
    root.mainloop()