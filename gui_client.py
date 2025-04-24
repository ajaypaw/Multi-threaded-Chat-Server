#!/usr/bin/env python3
import socket
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import argparse
import time
import queue
import platform
import sys
import re
import json
import random

# Client configuration
DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8888
BUFFER_SIZE = 2048

# Color constants
DARK_BG = "#1e1e2e"          # Main background
DARKER_BG = "#181825"         # Darker background for contrast elements
TEXT_BG = "#313244"           # Background for text areas
TEXT_FG = "#cdd6f4"           # Main text color
INPUT_BG = "#45475a"          # Input field background
ACCENT_COLOR = "#89b4fa"      # Primary accent color
ACCENT_COLOR_HOVER = "#74c7ec"  # Hover state for accent color
SERVER_MSG_COLOR = "#89dceb"  # Server message color
SYSTEM_MSG_COLOR = "#94e2d5"  # System message color
ERROR_COLOR = "#f38ba8"       # Error message color
BORDER_COLOR = "#6c7086"      # Border color for elements

# Username colors for chat
USERNAME_COLORS = [
    "#f5c2e7",  # Pink
    "#fab387",  # Peach
    "#a6e3a1",  # Green
    "#cba6f7",  # Purple
    "#f9e2af",  # Yellow
    "#74c7ec",  # Blue
    "#94e2d5",  # Teal
    "#f2cdcd",  # Rosewater
]

class ImprovedChatClient:
    def __init__(self, root, server_ip="127.0.0.1", server_port=8888):
        self.root = root
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket = None
        self.running = False
        self.username = None
        self.is_windows = platform.system() == "Windows"
        self.message_queue = queue.Queue()
        self.username_colors = {}
        self.last_seen_usernames = set()
        
        # Setup UI
        self.setup_gui()
        
        # Connect to server
        self.connect_to_server()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start message processing
        self.process_message_queue()
    
    def setup_gui(self):
        # Configure root window
        self.root.title("Chat Client")
        self.root.geometry("900x600")
        self.root.minsize(600, 400)
        
        # Set theme
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Using clam theme as base
        
        # Configure colors
        self.root.configure(bg=DARK_BG)
        self.style.configure('TFrame', background=DARK_BG)
        self.style.configure('TButton', 
                            background=ACCENT_COLOR, 
                            foreground='white', 
                            font=('Segoe UI', 10, 'bold'),
                            borderwidth=0)
        self.style.map('TButton', 
                      background=[('active', ACCENT_COLOR_HOVER)],
                      foreground=[('active', 'white')])
        self.style.configure('TLabel', background=DARK_BG)
        
        # Create main container with proper configuration
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)
        
        # Main frame
        self.main_frame = ttk.Frame(self.root, style='TFrame')
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Configure main frame weights
        self.main_frame.grid_columnconfigure(0, weight=0)  # Users list
        self.main_frame.grid_columnconfigure(1, weight=1)  # Chat area
        self.main_frame.grid_rowconfigure(0, weight=0)  # Top bar
        self.main_frame.grid_rowconfigure(1, weight=1)  # Content
        
        # Create a top bar with connection info
        self.top_frame = ttk.Frame(self.main_frame, style='TFrame')
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Server info and status
        self.server_label = ttk.Label(self.top_frame, 
                                     text=f"Server: {self.server_ip}:{self.server_port}", 
                                     background=DARK_BG, foreground="#aaaaaa")
        self.server_label.pack(side=tk.LEFT)
        
        self.status_var = tk.StringVar(value="Disconnected")
        self.status_label = ttk.Label(self.top_frame, 
                                     textvariable=self.status_var, 
                                     background=DARK_BG, foreground="#aaaaaa")
        self.status_label.pack(side=tk.RIGHT)
        
        # Content frame with users list and chat area
        self.content_frame = ttk.Frame(self.main_frame, style='TFrame')
        self.content_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=0)  # Users list
        self.content_frame.grid_columnconfigure(1, weight=1)  # Chat area
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Users list frame
        self.users_frame = ttk.Frame(self.content_frame, style='TFrame', width=150)
        self.users_frame.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        self.users_frame.grid_propagate(False)  # Prevent frame from shrinking
        
        # Users header
        self.users_header = ttk.Label(self.users_frame, text="Online Users", 
                                    background=DARK_BG, foreground=TEXT_FG,
                                    font=("Segoe UI", 10, "bold"))
        self.users_header.pack(fill=tk.X, pady=(0, 5))
        
        # Users list
        self.users_list = tk.Listbox(self.users_frame, 
                                   bg=TEXT_BG, fg=TEXT_FG,
                                   selectbackground=ACCENT_COLOR, 
                                   selectforeground=TEXT_FG,
                                   font=("Consolas", 10))
        self.users_list.pack(fill=tk.BOTH, expand=True)
        
        # Chat area
        self.chat_frame = ttk.Frame(self.content_frame, style='TFrame')
        self.chat_frame.grid(row=0, column=1, sticky="nsew")
        self.chat_frame.grid_rowconfigure(0, weight=1)  # Chat display
        self.chat_frame.grid_rowconfigure(1, weight=0)  # Input area
        self.chat_frame.grid_columnconfigure(0, weight=1)
        
        # Create chat display
        self.chat_display = scrolledtext.ScrolledText(self.chat_frame, 
                                                    wrap=tk.WORD, 
                                                    bg=TEXT_BG, fg=TEXT_FG,
                                                    font=("Consolas", 11),
                                                    padx=10, pady=10)
        self.chat_display.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.chat_display.config(state=tk.DISABLED)
        
        # Configure tags for different message types
        self.chat_display.tag_configure("server", foreground=SERVER_MSG_COLOR)
        self.chat_display.tag_configure("error", foreground=ERROR_COLOR)
        
        for i, color in enumerate(USERNAME_COLORS):
            self.chat_display.tag_configure(f"user{i}", foreground=color)
        
        # Create input frame
        self.input_frame = ttk.Frame(self.chat_frame, style='TFrame')
        self.input_frame.grid(row=1, column=0, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)  # Message input
        self.input_frame.grid_columnconfigure(1, weight=0)  # Send button
        
        # Message input
        self.message_input = tk.Entry(self.input_frame, 
                                    bg=INPUT_BG, fg=TEXT_FG,
                                    font=("Consolas", 11),
                                    insertbackground=TEXT_FG,
                                    relief=tk.FLAT,
                                    bd=10)
        self.message_input.grid(row=0, column=0, sticky="ew")
        self.message_input.bind("<Return>", self.send_message)
        self.message_input.focus_set()
        
        # Send button
        self.send_button = ttk.Button(self.input_frame, text="Send", 
                                     command=self.send_message,
                                     style='TButton',
                                     cursor="hand2")
        self.send_button.grid(row=0, column=1, padx=(10, 0))
        
        # Status bar
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                                  background=DARKER_BG, foreground="#aaaaaa",
                                  relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=1, column=0, sticky="ew")
        
        # Welcome message
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "Welcome to the Chat Application!\n", "server")
        self.chat_display.insert(tk.END, "Connecting to server...\n", "server")
        self.chat_display.config(state=tk.DISABLED)
    
    def connect_to_server(self):
        """Connect to the chat server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))
            
            # Update status
            self.running = True
            self.status_var.set(f"Connected to {self.server_ip}:{self.server_port}")
            
            # Start receiving thread
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            self.display_system_message(f"Connected to server at {self.server_ip}:{self.server_port}")
        except Exception as e:
            self.display_error(f"Could not connect to the server: {str(e)}")
            # Schedule reconnect after 5 seconds
            self.root.after(5000, self.reconnect)
    
    def reconnect(self):
        """Attempt to reconnect to the server."""
        if not self.running:
            self.display_system_message("Attempting to reconnect...")
            self.connect_to_server()
    
    def receive_messages(self):
        """Thread function to receive messages from the server."""
        while self.running:
            try:
                data = self.socket.recv(BUFFER_SIZE)
                if not data:
                    self.message_queue.put(("system", "Disconnected from server"))
                    self.running = False
                    # Schedule reconnect after 5 seconds
                    self.root.after(5000, self.reconnect)
                    break
                
                message = data.decode('utf-8')
                
                # Handle username prompt
                if message.startswith("Please enter your username:"):
                    if not self.username:
                        self.root.after(0, self.prompt_username)
                else:
                    # Queue the message for processing in the main thread
                    self.message_queue.put(("message", message))
                    
                    # Extract and update user list
                    self.extract_users(message)
            except Exception as e:
                if self.running:
                    self.message_queue.put(("error", f"Error receiving message: {str(e)}"))
                    self.running = False
                    # Schedule reconnect after 5 seconds
                    self.root.after(5000, self.reconnect)
                break
    
    def process_message_queue(self):
        """Process messages from the queue in the main thread."""
        try:
            messages_processed = 0
            while not self.message_queue.empty() and messages_processed < 10:  # Process max 10 at once to keep UI responsive
                msg_type, message = self.message_queue.get_nowait()
                
                if msg_type == "system":
                    self.display_system_message(message)
                elif msg_type == "error":
                    self.display_error(message)
                else:
                    self.display_message(message)
                
                self.message_queue.task_done()
                messages_processed += 1
                
            # Force update the display
            self.root.update_idletasks()
        except queue.Empty:
            pass
        finally:
            # Schedule to check again
            self.root.after(50, self.process_message_queue)  # Check more frequently (50ms)
    
    def extract_users(self, message):
        """Extract usernames from server messages and update the user list."""
        # Handle different message formats
        if "has joined the chat" in message:
            match = re.search(r"SERVER: (\w+) has joined the chat", message)
            if match:
                username = match.group(1)
                self.add_user(username)
        elif "has left the chat" in message:
            match = re.search(r"SERVER: (\w+) has left the chat", message)
            if match:
                username = match.group(1)
                self.remove_user(username)
        elif "]" in message and ":" in message:
            # Regular chat message
            match = re.search(r"\[\d+:\d+\] (\w+):", message)
            if match:
                username = match.group(1)
                self.add_user(username)
    
    def add_user(self, username):
        """Add a user to the user list if not already there."""
        if username and username != "SERVER" and username not in self.last_seen_usernames:
            self.last_seen_usernames.add(username)
            
            # Add color for this username if not exists
            if username not in self.username_colors:
                color_index = len(self.username_colors) % len(USERNAME_COLORS)
                self.username_colors[username] = color_index
                
            # Check if already in list
            users = list(self.users_list.get(0, tk.END))
            if username not in users:
                self.users_list.insert(tk.END, username)
    
    def remove_user(self, username):
        """Remove a user from the user list."""
        if username in self.last_seen_usernames:
            self.last_seen_usernames.remove(username)
            
        # Find and remove from listbox
        for i in range(self.users_list.size()):
            if self.users_list.get(i) == username:
                self.users_list.delete(i)
                break
    
    def prompt_username(self):
        """Prompt the user for a username."""
        username = simpledialog.askstring("Username", 
                                      "Enter your username:",
                                      parent=self.root)
        if not username:
            username = f"User-{int(time.time()) % 10000}"
        
        self.username = username
        self.add_user(username)  # Add ourselves to the user list
        self.status_var.set(f"Connected as {username}")
        self.socket.send(username.encode('utf-8'))
        
        # Update window title
        self.root.title(f"Chat Client - {username}")
        
        # Ensure input gets focus after username dialog
        self.root.after(100, lambda: self.message_input.focus_set())
    
    def send_message(self, event=None):
        """Send a message to the server."""
        message = self.message_input.get().strip()
        if message:
            # Make sure we have a username before sending
            if not self.username:
                self.display_error("Cannot send message - not connected or username not set.")
                return "break"
            
            try:
                self.socket.send(message.encode('utf-8'))
                self.message_input.delete(0, tk.END)
                
                # Display our own message in the chat
                if message != "/exit":
                    timestamp = time.strftime("%H:%M", time.localtime())
                    formatted_message = f"[{timestamp}] {self.username}: {message}\n"
                    
                    # Add message directly to chat display to ensure immediate feedback
                    self.chat_display.config(state=tk.NORMAL)
                    
                    # Get color for our username
                    color_index = self.username_colors.get(self.username, 0)
                    tag = f"user{color_index}"
                    
                    # Insert with proper formatting
                    prefix = f"[{timestamp}] {self.username}:"
                    self.chat_display.insert(tk.END, prefix, tag)
                    self.chat_display.insert(tk.END, f" {message}\n")
                    self.chat_display.see(tk.END)
                    self.chat_display.config(state=tk.DISABLED)
                
                # Exit check
                if message == "/exit":
                    self.running = False
                    self.status_var.set("Disconnecting...")
                    self.root.after(500, self.root.quit)
            except Exception as e:
                self.display_error(f"Error sending message: {str(e)}")
        return "break"  # Prevent default behavior of Return key
    
    def display_message(self, message):
        """Display a received message in the chat display."""
        self.chat_display.config(state=tk.NORMAL)
        
        # Ensure message ends with newline
        if not message.endswith('\n'):
            message += '\n'
        
        # Handle server messages
        if message.startswith("SERVER:"):
            self.chat_display.insert(tk.END, message, "server")
        elif "Welcome" in message and "connected to the chat server" in message:
            self.chat_display.insert(tk.END, message, "server")
        else:
            # Try to extract username for coloring
            match = re.search(r"\[\d+:\d+\] (\w+):", message)
            if match:
                username = match.group(1)
                # Get color for this username
                color_index = self.username_colors.get(username, 0)
                tag = f"user{color_index}"
                
                # Split message into parts
                parts = message.split(f"{username}:", 1)
                if len(parts) == 2:
                    prefix = parts[0] + f"{username}:"
                    content = parts[1]
                    
                    # Insert with appropriate tags
                    self.chat_display.insert(tk.END, prefix, tag)
                    self.chat_display.insert(tk.END, content)
                else:
                    # Fallback for unexpected format
                    self.chat_display.insert(tk.END, message)
            else:
                # Just insert the message as is
                self.chat_display.insert(tk.END, message)
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        # Update the window title if we have a username
        if self.username:
            self.root.title(f"Chat Client - {self.username}")
    
    def display_system_message(self, message):
        """Display a system message in the chat display."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"SYSTEM: {message}\n", "server")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def display_error(self, message):
        """Display an error message in the chat display."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"ERROR: {message}\n", "error")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        # Also update status bar
        self.status_var.set(f"Error: {message[:30]}..." if len(message) > 30 else f"Error: {message}")
    
    def on_closing(self):
        """Handle window close event."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.running = False
            if self.socket:
                try:
                    self.socket.send("/exit".encode('utf-8'))
                    self.socket.close()
                except:
                    pass
            self.root.destroy()

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Improved Chat Client')
    parser.add_argument('--host', default=DEFAULT_HOST, help='Server IP address')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Server port')
    args = parser.parse_args()
    
    # Create and run the GUI
    root = tk.Tk()
    root.title("Chat Client - Connecting...")
    
    # Set app icon if available
    try:
        if platform.system() == "Windows":
            root.iconbitmap("chat.ico")
        elif platform.system() == "Linux":
            img = tk.PhotoImage(file="chat.png")
            root.tk.call('wm', 'iconphoto', root._w, img)
    except:
        pass  # Icon not found, use default
    
    client = ImprovedChatClient(root, args.host, args.port)
    root.mainloop()

if __name__ == "__main__":
    main() 