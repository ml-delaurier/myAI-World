#!/usr/bin/env python3

import os
import json
import threading
import time
import requests
import uuid
from pathlib import Path
from textwrap import dedent
from typing import List, Optional
import customtkinter as ctk
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
from rich.console import Console
from tkinter import filedialog
import logging
from database import DatabaseManager  


console = Console()
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class FileToCreate(BaseModel):
    path: str
    content: str

class FileToEdit(BaseModel):
    path: str
    original_snippet: str
    new_snippet: str

class AssistantResponse(BaseModel):
    assistant_reply: str
    files_to_create: Optional[List[FileToCreate]] = None
    files_to_edit: Optional[List[FileToEdit]] = None

def read_local_file(file_path: str) -> str:
    """Return the text content of a local file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def create_file(path: str, content: str):
    """Create (or overwrite) a file at 'path' with the given 'content'."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"✓ Created/updated file at '{file_path}'"

def apply_diff_edit(path: str, original_snippet: str, new_snippet: str) -> str:
    """Apply diff edit and return status message."""
    try:
        content = read_local_file(path)
        if original_snippet in content:
            updated_content = content.replace(original_snippet, new_snippet, 1)
            create_file(path, updated_content)
            return f"✓ Applied diff edit to '{path}'"
        else:
            return f"⚠ Original snippet not found in '{path}'. No changes made."
    except FileNotFoundError:
        return f"✗ File not found for diff editing: '{path}'"

class MessageBubble(ctk.CTkFrame):
    def __init__(self, *args, text="", is_user=True, is_reasoning=False, **kwargs):
        """Initialize a message bubble widget
        
        Version 1.0.4:
            - Hide thinking text by default
            - Added total thinking time tracking
            - Improved timer handling
            - Enhanced preview state
        """
        super().__init__(*args, **kwargs)
        
        self.text = text
        self.is_user = is_user
        self.is_reasoning = is_reasoning
        self.expanded = False
        self.copy_btn = None
        self.start_time = time.time()
        self.thinking_dots = 0
        self.is_thinking = True
        
        # Store reference to root window
        self.root = self.winfo_toplevel()
        
        # Configure frame appearance
        if is_user:
            self.configure(fg_color=("gray85", "gray25"))
        elif is_reasoning:
            self.configure(fg_color=("gray65", "gray45"))
        else:
            self.configure(fg_color=("gray75", "gray35"))
        
        # For reasoning messages, create a header with toggle and timer
        if is_reasoning:
            # Create header frame
            self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
            self.header_frame.pack(fill="x", expand=True)
            
            # Add brain emoji toggle button
            self.toggle_button = ctk.CTkButton(
                self.header_frame,
                text="🧠",  # Brain emoji
                width=30,
                command=self.toggle_content,
                fg_color="transparent",
                hover_color=("gray75", "gray35"),
                font=("Segoe UI Emoji", 14)  # Use emoji font
            )
            self.toggle_button.pack(side="left", padx=5, pady=5)
            
            # Add "Thinking" label with animated dots (initially hidden)
            self.thinking_label = ctk.CTkLabel(
                self.header_frame,
                text="Thinking",
                anchor="w"
            )
            
            # Add timer label (initially hidden)
            self.timer_label = ctk.CTkLabel(
                self.header_frame,
                text="0.0s",
                anchor="e"
            )
            self.timer_label.pack(side="right", padx=5, pady=5)
            
            # Create preview label (initially visible)
            preview = text.split('\n')[0] if text else ""
            if len(preview) > 100:
                preview = preview[:100] + "..."
            elif text and len(text.split('\n')) > 1:
                preview += "..."
                
            self.preview_label = ctk.CTkLabel(
                self,
                text=preview,
                anchor="w",
                justify="left",
                wraplength=800
            )
            self.preview_label.pack(expand=True, fill="both", padx=10)
            
            # Create full content label (initially hidden)
            self.content_label = ctk.CTkLabel(
                self,
                text=text,
                anchor="w",
                justify="left",
                wraplength=800
            )
            
            # Start timer and dots animation
            self.animate_thinking()
        else:
            # For non-reasoning messages, just show the content
            message_label = ctk.CTkLabel(
                self,
                text=text,
                anchor="w",
                justify="left",
                wraplength=800
            )
            message_label.pack(expand=True, fill="both", padx=10, pady=10)
            
            # Add copy button to non-reasoning messages
            self.add_copy_button()

    def stop_thinking(self):
        """Stop the thinking animation and update total thinking time"""
        if not self.is_reasoning or not self.is_thinking:
            return
            
        self.is_thinking = False
        elapsed = time.time() - self.start_time
        
        # Update the timer one last time
        self.timer_label.configure(text=f"{elapsed:.1f}s")
        
        # Update total thinking time if available
        if hasattr(self.root, 'total_thinking_time') and hasattr(self.root, 'thinking_time_label'):
            self.root.total_thinking_time += elapsed
            self.root.thinking_time_label.configure(
                text=f"Total Thinking: {self.root.total_thinking_time:.1f}s"
            )

    def animate_thinking(self):
        """Animate the thinking label with dots and update timer"""
        if not self.is_reasoning or not self.is_thinking:
            return
            
        elapsed = time.time() - self.start_time
        self.timer_label.configure(text=f"{elapsed:.1f}s")
        
        # Animate the thinking dots only when expanded
        if self.expanded:
            self.thinking_dots = (self.thinking_dots + 1) % 4
            dots = "." * self.thinking_dots
            self.thinking_label.configure(text=f"Thinking{dots}")
        
        # Schedule next animation frame if still thinking
        if self.is_thinking:
            self.after(500, self.animate_thinking)

    def add_copy_button(self):
        """Add copy button to the message bubble"""
        if not self.copy_btn:
            self.copy_btn = ctk.CTkButton(
                self,
                text="Copy",
                width=60,
                height=25,
                command=self._copy_text
            )
            self.copy_btn.pack(side="right", padx=5, pady=5)
            
    def _copy_text(self):
        """Copy text to clipboard"""
        if self.root:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.text)
            self.root.update()

    def toggle_content(self):
        """Toggle between preview and full content for reasoning messages"""
        if not self.is_reasoning:
            return
            
        self.expanded = not self.expanded
        if self.expanded:
            self.preview_label.pack_forget()
            self.content_label.pack(expand=True, fill="both", padx=10)
            self.thinking_label.pack(side="left", padx=5, pady=5)  # Show thinking label
            # Show copy button when expanded
            self.add_copy_button()
        else:
            self.content_label.pack_forget()
            self.thinking_label.pack_forget()  # Hide thinking label
            self.preview_label.pack(expand=True, fill="both", padx=10)
            # Hide copy button when collapsed
            if self.copy_btn:
                self.copy_btn.destroy()
                self.copy_btn = None

class DeepSeekEngineerGUI(ctk.CTk):
    """A customtkinter-based GUI application for the DeepSeek Engineer interface.
    
    This class implements a graphical user interface for interacting with the DeepSeek
    language model, providing features for code generation, analysis, and management.
    
    Attributes:
        db (DatabaseManager): Database manager instance for conversation storage
        conversation_id (str): Unique identifier for the current conversation
        client (OpenAI): OpenAI client instance for API communication
        models (dict): Available DeepSeek models
        conversation_history (list): List of conversation messages
        message_widgets (list): List of message bubble widgets
        workspace_files (list): List of files in the workspace
        api_balance (float): Current API credit balance
        
    Version 1.0.1:
        - Added comprehensive docstrings
        - Added proper type hints
        - Added version tracking
    """
    def __init__(self):
        super().__init__()

        # Load environment variables
        load_dotenv()
        
        # Initialize database
        self.db = DatabaseManager()
        
        # Generate unique conversation ID
        self.conversation_id = str(uuid.uuid4())
        
        # Initialize OpenAI client with API key dialog if needed
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            api_key = self.show_api_key_dialog()
        
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        # Available models
        self.models = {
            "DeepSeek-V3": "deepseek-chat",
            "DeepSeek-R1": "deepseek-reasoner"
        }

        # Initialize conversation history
        self.conversation_history = [
            {"role": "system", "content": self.get_system_prompt()}
        ]
        
        # Initialize message widgets list
        self.message_widgets = []
        
        # Initialize thinking animation variables
        self.thinking_animation_id = None
        self.thinking_start_time = None
        self.current_thinking_label = None
        self.thinking_dots = 0  # Initialize thinking_dots here

        # Initialize conversations list
        self.conversations = []
        self.current_conversation_name = "New Chat"
        
        # Initialize workspace files
        self.workspace_files = []  # Initialize workspace_files here
        
        # Initialize API balance
        self.api_balance = 0.0
        self.api_balance_label = None
        self.update_api_balance()  # Initial balance check
        
        # Initialize thinking time tracking
        self.total_thinking_time = 0.0
        self.thinking_time_label = None
        
        # Configure window
        self.title("DeepSeek Engineer")
        self.geometry("1400x800")  # Made window wider for sidebar
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'app_icon.ico')
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        # Create main container with sidebar and content
        self.grid_columnconfigure(1, weight=1)  # Content area expands
        self.grid_rowconfigure(0, weight=1)

        # Create sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        self.create_sidebar()

        # Create main content frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Create UI elements
        self.create_ui_elements()
        
        # Start periodic API balance updates
        self._start_periodic_balance_update()
        
    def create_sidebar(self):
        """Create the sidebar with conversation history"""
        # Title at the top
        title_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="DeepSeek Engineer",
            font=("Arial", 16, "bold")
        )
        title_label.pack(padx=10, pady=(10, 5))

        # New Chat button
        new_chat_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="+ New Chat",
            command=self.start_new_chat,
            height=40,
            fg_color="#2ecc71",
            hover_color="#27ae60"
        )
        new_chat_btn.pack(fill="x", padx=10, pady=(5, 10))

        # Separator
        separator = ctk.CTkFrame(self.sidebar_frame, height=2, fg_color="gray50")
        separator.pack(fill="x", padx=10, pady=5)

        # Conversations list
        self.conversations_frame = ctk.CTkScrollableFrame(
            self.sidebar_frame,
            label_text="Recent Chats"
        )
        self.conversations_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def start_new_chat(self):
        """Start a new chat and save the current one"""
        # Save current conversation if it exists
        if self.conversation_history:
            self.conversations.append({
                "name": self.current_conversation_name,
                "history": self.conversation_history.copy(),
                "id": self.conversation_id
            })
            
        # Generate new conversation ID
        self.conversation_id = str(uuid.uuid4())
        
        # Clear conversation history
        self.conversation_history = [
            {"role": "system", "content": self.get_system_prompt()}
        ]
        
        # Clear message widgets
        for widget in self.message_widgets:
            widget.destroy()
        self.message_widgets.clear()
        
        # Reset thinking time for new conversation
        self.total_thinking_time = 0.0
        if self.thinking_time_label:
            self.thinking_time_label.configure(text="Total Thinking: 0.0s")
        
        # Add to sidebar
        self.add_conversation_to_sidebar({
            "name": "New Chat",
            "history": self.conversation_history.copy(),
            "id": self.conversation_id
        })

    def add_conversation_to_sidebar(self, conversation):
        """Add a conversation button to the sidebar
        
        Version 1.0.2:
            - Added proper error handling
            - Added default values for missing fields
            - Added timestamp formatting
        """
        try:
            # Get current timestamp if not provided
            timestamp = conversation.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M"))
            
            # Get current model if not provided
            model = conversation.get('model', self.model_var.get())
            
            # Create conversation button
            conversation_btn = ctk.CTkButton(
                self.conversations_frame,
                text=f"{model} • {timestamp}",
                command=lambda: self.load_conversation(conversation),
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray75", "gray25")
            )
            conversation_btn.pack(fill="x", padx=5, pady=2)
            
        except Exception as e:
            logging.error(f"Error adding conversation to sidebar: {str(e)}")
            # Create error button
            error_btn = ctk.CTkButton(
                self.conversations_frame,
                text="Error loading conversation",
                state="disabled",
                fg_color="transparent"
            )
            error_btn.pack(fill="x", padx=5, pady=2)

    def show_api_key_dialog(self):
        """Show a dialog to enter the DeepSeek API key."""
        dialog = ctk.CTkInputDialog(
            text="DeepSeek API key:",
            title="API Key Required"
        )
        api_key = dialog.get_input()
        if not api_key:
            self.quit()
            return None
        return api_key

    def create_ui_elements(self):
        # Top frame for controls
        self.controls_frame = ctk.CTkFrame(self.main_frame)
        self.controls_frame.grid(row=0, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        # Add file button
        self.add_file_button = ctk.CTkButton(
            self.controls_frame, 
            text="Add File", 
            command=self.add_file_dialog
        )
        self.add_file_button.pack(side="left", padx=5, pady=5)

        # Add model selection dropdown
        self.model_var = ctk.StringVar(value="DeepSeek-V3")
        self.model_dropdown = ctk.CTkOptionMenu(
            self.controls_frame,
            values=list(self.models.keys()),
            variable=self.model_var
        )
        self.model_dropdown.pack(side="right", padx=5, pady=5)

        # Model selection label
        self.model_label = ctk.CTkLabel(
            self.controls_frame,
            text="Model:"
        )
        self.model_label.pack(side="right", padx=(5, 0), pady=5)

        # Create API balance label
        self.api_balance_label = ctk.CTkLabel(
            self.controls_frame,
            text="API Credits: $0.00",
            anchor="e"
        )
        self.api_balance_label.pack(side="right", padx=(10, 0), pady=5)
        
        # Create thinking time label
        self.thinking_time_label = ctk.CTkLabel(
            self.controls_frame,
            text="Total Thinking: 0.0s",
            anchor="e"
        )
        self.thinking_time_label.pack(side="right", padx=(10, 0), pady=5)

        # Create scrollable conversation frame
        self.conversation_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.conversation_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.conversation_frame.grid_columnconfigure(0, weight=1)

        # Create input frame
        self.input_frame = ctk.CTkFrame(self.main_frame)
        self.input_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        # Create input field
        self.input_field = ctk.CTkTextbox(self.input_frame, height=100)
        self.input_field.grid(row=0, column=0, padx=(5, 5), pady=5, sticky="ew")

        # Create send button
        self.send_button = ctk.CTkButton(
            self.input_frame, 
            text="Send", 
            command=self.send_message
        )
        self.send_button.grid(row=0, column=1, padx=5, pady=5)

        # Bind Enter key to send message
        self.input_field.bind("<Return>", lambda e: self.send_message() if not e.state & 0x1 else None)

    def create_message_bubble(self, text: str, is_user: bool = True, is_reasoning: bool = False):
        """Create a message bubble for the chat"""
        # Create frame for the message
        bubble_frame = MessageBubble(
            self.conversation_frame,
            text=text,
            is_user=is_user,
            is_reasoning=is_reasoning
        )
        
        if is_reasoning:
            self.start_thinking_animation(bubble_frame.header_frame)
            
        bubble_frame.pack(fill="x", padx=10, pady=5)
        return bubble_frame

    def toggle_reasoning(self, bubble_frame):
        """Toggle the visibility of the reasoning content"""
        if hasattr(bubble_frame, 'content_frame'):
            if bubble_frame.content_frame.winfo_manager():
                # Currently visible, hide it
                bubble_frame.content_frame.pack_forget()
                bubble_frame.toggle_button.configure(text="▶")  # Right arrow
            else:
                # Currently hidden, show it
                bubble_frame.content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
                bubble_frame.toggle_button.configure(text="▼")  # Down arrow

    def add_file_dialog(self):
        """Add a file or directory to the workspace"""
        file_path = filedialog.askopenfilename(title="Select File")
        if file_path:
            try:
                # Store the file path in the workspace
                if not hasattr(self, 'workspace_files'):
                    self.workspace_files = set()
                
                abs_path = os.path.abspath(file_path)
                self.workspace_files.add(abs_path)
                
                # Read the file content
                content = read_local_file(abs_path)
                
                # Add file content as a user message
                self.conversation_history.append({
                    "role": "user",
                    "content": f"I'm adding this file: {abs_path}\n\nFile contents:\n{content}"
                })
                
                # Add assistant acknowledgment
                self.conversation_history.append({
                    "role": "assistant",
                    "content": f"I've received the file {os.path.basename(abs_path)}. I can help you analyze or modify this file. What would you like me to do with it?"
                })
                
                # Show notification in UI
                filename = os.path.basename(file_path)
                self.append_to_conversation(f"Added file to workspace: {filename}", is_user=True)
                self.append_to_conversation(f"I've received the file {filename}. I can help you analyze or modify this file. What would you like me to do with it?", is_user=False)
                
            except Exception as e:
                self.append_to_conversation(f"Error adding file: {str(e)}", is_user=False)

    def get_system_prompt(self) -> str:
        return dedent("""\
You are an elite software engineer called DeepSeek Engineer with decades of experience across all programming domains.
Your expertise spans system design, algorithms, testing, and best practices.
You provide thoughtful, well-structured solutions while explaining your reasoning.

Core capabilities:
1. Code Analysis & Discussion
   - Analyze code with expert-level insight
   - Explain complex concepts clearly
   - Suggest optimizations and best practices
   - Debug issues with precision

2. File Operations:
   When files are added to the workspace:
   - You can automatically read their contents
   - You can analyze multiple files together
   - You can make changes or create new files
   - You will be notified when files are added

When working with files:
1. First analyze the code and explain what you understand
2. Propose specific changes or improvements
3. Use the file operation JSON format to make changes
4. Confirm what was changed and explain the improvements

Output Format for File Operations:
{
  "assistant_reply": "Your explanation of the changes",
  "files_to_create": [
    {
      "path": "relative/path/to/new/file",
      "content": "complete file content with proper formatting"
    }
  ],
  "files_to_edit": [
    {
      "path": "path/to/file",
      "original_snippet": "exact code to replace (include enough context)",
      "new_snippet": "new code with proper indentation"
    }
  ]
}

Guidelines:
1. When a file is added:
   - Automatically read and analyze it
   - Suggest improvements if needed
   - Make changes using the JSON format
2. For new files:
   - Include complete, properly formatted code
   - Add necessary imports and dependencies
3. For editing files:
   - Use precise, minimal edits
   - Maintain code style and formatting
4. After changes:
   - Confirm what was changed
   - Explain how to test the changes

Remember: You're a senior engineer - be thorough, precise, and thoughtful in your solutions.
""")

    def process_message(self):
        try:
            # Get the selected model
            model = self.models[self.model_var.get()]
            
            # Prepare conversation history based on model
            if model == "deepseek-reasoner":
                # For reasoner, ensure system message is first
                messages = [{"role": "system", "content": self.get_system_prompt()}]
                # Add other messages, skipping any previous system messages
                messages.extend([msg for msg in self.conversation_history if msg["role"] != "system"])
            else:
                # For chat model, use history as is
                messages = self.conversation_history
            
            # If we have workspace files that aren't in the history, add them
            if hasattr(self, 'workspace_files') and self.workspace_files:
                for file_path in self.workspace_files:
                    # Check if this file is already in the conversation
                    if not any(file_path in msg.get('content', '') for msg in self.conversation_history):
                        try:
                            content = read_local_file(file_path)
                            # Add file as user message
                            messages.append({
                                "role": "user",
                                "content": f"I'm adding this file: {file_path}\n\nFile contents:\n{content}"
                            })
                            # Add assistant acknowledgment
                            messages.append({
                                "role": "assistant",
                                "content": f"I've received the file {os.path.basename(file_path)}. I can help you analyze or modify this file. What would you like me to do with it?"
                            })
                        except Exception as e:
                            self.append_to_conversation(f"Error reading {file_path}: {str(e)}", is_user=False)
            
            # Get completion from API
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                stream=True
            )

            # Process the streaming response
            collected_chunks = []
            json_started = False
            json_content = ""
            current_response = None
            current_reasoning = None
            reasoning_content = ""
            content = ""
            
            for chunk in completion:
                # Handle reasoning content for deepseek-reasoner model
                if model == "deepseek-reasoner" and hasattr(chunk.choices[0].delta, 'reasoning_content'):
                    token = chunk.choices[0].delta.reasoning_content
                    if token is not None:
                        reasoning_content += token
                        
                        # Update or create reasoning bubble
                        if current_reasoning is None and token.strip():
                            current_reasoning = self.append_to_conversation("", is_user=False, is_reasoning=True)
                            # Start thinking animation for the header label
                            self.start_thinking_animation(current_reasoning.header_frame)
                        
                        if current_reasoning:
                            # Get the content label from the content frame
                            content_frame = current_reasoning.content_frame
                            label = content_frame.winfo_children()[0]
                            current_text = label.cget("text")
                            label.configure(text=current_text + token)
                
                # Handle regular content
                if chunk.choices[0].delta.content is not None:
                    # If we were showing thinking animation, stop it
                    if current_reasoning:
                        self.stop_thinking_animation()
                    
                    token = chunk.choices[0].delta.content
                    collected_chunks.append(token)
                    content += token
                    
                    # Check if this is the start of JSON
                    if not json_started and token.strip().startswith("{"):
                        json_started = True
                        json_content = token
                        continue
                    
                    if json_started:
                        json_content += token
                        # Try to parse the JSON to see if it's complete
                        try:
                            json.loads(json_content)
                            # If we get here, JSON is valid and complete
                            self.handle_assistant_response(json_content)
                            json_started = False
                            json_content = ""
                        except json.JSONDecodeError:
                            # JSON is not complete yet, keep collecting
                            continue
                    else:
                        # Only create response bubble when we have actual content to show
                        if current_response is None and token.strip():
                            current_response = self.append_to_conversation("", is_user=False)
                        
                        if current_response:
                            # Update the current response with new token
                            message_label = current_response.winfo_children()[0]
                            current_text = message_label.cget("text")
                            message_label.configure(text=current_text + token)

            # Make sure to stop thinking animation if it's still running
            self.stop_thinking_animation()

            # Join all chunks for the final response
            full_response = "".join(collected_chunks)

            # If we still have incomplete JSON content, try one last time
            if json_started and json_content:
                try:
                    self.handle_assistant_response(json_content)
                except json.JSONDecodeError as e:
                    self.append_to_conversation(f"Error parsing JSON response: {str(e)}", is_user=False)

            # Add to conversation history (excluding reasoning content)
            self.conversation_history.append({"role": "assistant", "content": content})

        except Exception as e:
            self.stop_thinking_animation()  # Make sure to stop animation on error
            self.append_to_conversation(f"Error: {str(e)}", is_user=False)
        finally:
            # Re-enable input
            self.after(0, lambda: self.input_field.configure(state="normal"))
            self.after(0, lambda: self.send_button.configure(state="normal"))

    def handle_assistant_response(self, response_text: str) -> None:
        """
        Handle the assistant's response by processing file operations and displaying messages.
        
        Args:
            response_text (str): The raw response text from the assistant
            
        Version 1.0.1:
            - Added type safety for file operations
            - Improved error handling
            - Added proper return types
        """
        try:
            # Parse the response text as JSON
            response_data = json.loads(response_text)
            
            # Handle files_to_create
            if 'files_to_create' in response_data:
                files_to_create = response_data.get('files_to_create', []) or []
                if isinstance(files_to_create, dict):
                    files_to_create = [files_to_create]
                response_data['files_to_create'] = [
                    FileToCreate(**item) if isinstance(item, dict) else item 
                    for item in files_to_create
                ]
            else:
                response_data['files_to_create'] = []
                
            # Handle files_to_edit
            if 'files_to_edit' in response_data:
                files_to_edit = response_data.get('files_to_edit', []) or []
                if isinstance(files_to_edit, dict):
                    files_to_edit = [files_to_edit]
                response_data['files_to_edit'] = [
                    FileToEdit(**item) if isinstance(item, dict) else item 
                    for item in files_to_edit
                ]
            else:
                response_data['files_to_edit'] = []
            
            # Convert response to proper objects
            response = AssistantResponse(**response_data)

            # Display the assistant's reply first
            self.append_to_conversation(response.assistant_reply, is_user=False)

            # Handle file creations
            if response.files_to_create:
                for file in response.files_to_create:
                    try:
                        # Ensure path is relative to current directory
                        if os.path.isabs(file.path):
                            file.path = os.path.relpath(file.path)
                        
                        create_file(file.path, file.content)
                        self.append_to_conversation(f"✓ Created file: {file.path}", is_user=False)
                    except Exception as e:
                        logging.error(f"Error creating file {file.path}: {str(e)}")
                        self.append_to_conversation(f"❌ Error creating file {file.path}: {str(e)}", is_user=False)

            # Handle file edits
            if response.files_to_edit:
                for file in response.files_to_edit:
                    try:
                        result = apply_diff_edit(file.path, file.original_snippet, file.new_snippet)
                        if result:  # Only show success message if edit was successful
                            self.append_to_conversation(f"✓ Updated file: {file.path}", is_user=False)
                    except Exception as e:
                        logging.error(f"Error editing file {file.path}: {str(e)}")
                        self.append_to_conversation(f"❌ Error editing file {file.path}: {str(e)}", is_user=False)
                    
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing assistant response: {str(e)}")
            self.append_to_conversation(f"❌ Error parsing assistant response: {str(e)}", is_user=False)
        except Exception as e:
            logging.error(f"Unexpected error in handle_assistant_response: {str(e)}")
            self.append_to_conversation(f"❌ Unexpected error: {str(e)}", is_user=False)

    def get_api_balance(self) -> float:
        """Get the current API credit balance.
        
        Returns:
            float: Current balance in credits
            
        Version 1.0.1:
            - Added proper error handling
            - Added timeout to request
            - Added type hints
        """
        try:
            response = requests.get(
                "https://api.deepseek.com/user/balance",
                headers={
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {self.client.api_key}'
                },
                timeout=10  # Add timeout to prevent hanging
            )
            response.raise_for_status()  # Raise exception for bad status codes
            data = response.json()
            return float(data.get('balance', 0.0))
        except requests.RequestException as e:
            logging.error(f"API request failed: {str(e)}")
            return 0.0
        except (ValueError, KeyError) as e:
            logging.error(f"Error parsing API response: {str(e)}")
            return 0.0
        except Exception as e:
            logging.error(f"Unexpected error getting API balance: {str(e)}")
            return 0.0

    def update_api_balance(self) -> None:
        """Update the API balance display.
        
        Version 1.0.1:
            - Added type hints
            - Added error handling
        """
        try:
            self.api_balance = self.get_api_balance()
            if hasattr(self, 'api_balance_label') and self.api_balance_label:
                self.api_balance_label.configure(text=f"API Credits: ${self.api_balance:.2f}")
        except Exception as e:
            logging.error(f"Error updating API balance display: {str(e)}")

    def copy_to_clipboard(self, text: str) -> None:
        """Copy text to clipboard
        
        Args:
            text (str): Text to copy to clipboard
            
        Version 1.0.1:
            - Added type hints
            - Added error handling
        """
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
        except Exception as e:
            logging.error(f"Error copying to clipboard: {str(e)}")
            self.append_to_conversation("❌ Failed to copy text to clipboard", is_user=False)

    def send_message(self) -> None:
        """Send a message to the assistant and process the response.
        
        Version 1.0.1:
            - Added type hints
            - Added error handling
            - Added input validation
        """
        try:
            # Get message from input field
            message = self.input_field.get("1.0", "end-1c").strip()
            if not message:
                return

            # Clear input field and disable it
            self.input_field.delete("1.0", "end")
            self.input_field.configure(state="disabled")
            self.send_button.configure(state="disabled")

            # Display user message
            self.append_to_conversation(message, is_user=True)

            # Add to conversation history
            self.conversation_history.append({"role": "user", "content": message})

            # Get selected model
            selected_model = self.models[self.model_var.get()]
            
            # Create completion in a separate thread
            threading.Thread(target=self._process_completion, args=(selected_model,), daemon=True).start()
            
            # Update API balance after request
            threading.Thread(target=self.update_api_balance, daemon=True).start()
            
        except Exception as e:
            logging.error(f"Error sending message: {str(e)}")
            self.append_to_conversation(f"❌ Error sending message: {str(e)}", is_user=False)
            # Re-enable input on error
            self.input_field.configure(state="normal")
            self.send_button.configure(state="normal")

    def _start_periodic_balance_update(self) -> None:
        """Start periodic API balance updates every 5 minutes.
        
        Version 1.0.1:
            - Added type hints
            - Added error handling
        """
        def update_loop() -> None:
            while True:
                try:
                    self.update_api_balance()
                except Exception as e:
                    logging.error(f"Error in balance update loop: {str(e)}")
                time.sleep(300)  # 5 minutes
                
        threading.Thread(target=update_loop, daemon=True).start()

    def _process_completion(self, model: str) -> None:
        """Process the completion request in a separate thread
        
        Version 1.0.4:
            - Added proper thinking animation handling
            - Added thinking time tracking
            - Improved error handling
            - Enhanced content updates
        """
        try:
            # Start thinking animation
            self.start_thinking_animation(self.current_thinking_label)
            
            # Get completion from API
            completion = self.client.chat.completions.create(
                model=model,
                messages=self.conversation_history,
                temperature=0.7,
                stream=True
            )
            
            # Record API usage
            self.db.add_api_usage(0.002, "chat_completion", self.conversation_id)  # Approximate usage
            
            # Initialize response buffers
            reasoning_text = ""
            response_text = ""
            
            # Create reasoning bubble immediately
            reasoning_bubble = None
            
            # Process the streaming response
            for chunk in completion:
                # Handle reasoning content
                if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
                    if not reasoning_bubble:
                        reasoning_bubble = self.append_to_conversation("", is_user=False, is_reasoning=True)
                    reasoning_text += chunk.choices[0].delta.reasoning_content
                    reasoning_bubble.text = reasoning_text
                    
                    # Update content label
                    if hasattr(reasoning_bubble, 'content_label'):
                        reasoning_bubble.content_label.configure(text=reasoning_text)
                    
                    # Update preview label with first line or truncated text
                    if hasattr(reasoning_bubble, 'preview_label'):
                        preview = reasoning_text.split('\n')[0] if reasoning_text else ""
                        if len(preview) > 100:
                            preview = preview[:100] + "..."
                        elif len(reasoning_text.split('\n')) > 1:
                            preview += "..."
                        reasoning_bubble.preview_label.configure(text=preview)
            
                # Handle final content
                if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                    response_text += chunk.choices[0].delta.content
        
            # Stop thinking animation for reasoning bubble
            if reasoning_bubble:
                reasoning_bubble.stop_thinking()
        
            # Handle the complete response
            if response_text:
                self.handle_assistant_response(response_text)
        
        except Exception as e:
            self.append_to_conversation(f"Error: {str(e)}", is_user=False)
        finally:
            # Stop thinking animation
            self.stop_thinking_animation()
            
            # Re-enable input
            self.input_field.configure(state="normal")
            self.send_button.configure(state="normal")

    def append_to_conversation(self, text: str, replace_last_line: bool = False, 
                             is_user: bool = False, is_reasoning: bool = False) -> MessageBubble:
        """Add a new message to the conversation
        
        Args:
            text (str): The message text to add
            replace_last_line (bool): Whether to replace the last line
            is_user (bool): Whether this is a user message
            is_reasoning (bool): Whether this is a reasoning message
        
        Returns:
            MessageBubble: The created message bubble widget
            
        Version 1.0.1:
            - Added proper type hints
            - Added error handling
            - Added return type
        """
        try:
            # Create message bubble
            bubble = MessageBubble(
                self.conversation_frame,
                text=text,
                is_user=is_user,
                is_reasoning=is_reasoning
            )
            bubble.pack(fill="x", padx=10, pady=5)
            
            # Store in database
            role = "user" if is_user else "assistant"
            self.db.add_chat_message(role, text, self.conversation_id, is_reasoning)
            
            # Update UI
            self.message_widgets.append(bubble)
            self.conversation_frame._parent_canvas.yview_moveto(1.0)
            
            return bubble
        except Exception as e:
            logging.error(f"Error appending to conversation: {str(e)}")
            # Create a simple error message if bubble creation fails
            error_bubble = MessageBubble(
                self.conversation_frame,
                text=f"❌ Error displaying message: {str(e)}",
                is_user=False
            )
            error_bubble.pack(fill="x", padx=10, pady=5)
            return error_bubble

    def animate_thinking(self, header_frame: ctk.CTkFrame) -> None:
        """Animate the thinking text with dots and update timer.
        
        Args:
            header_frame (ctk.CTkFrame): The frame containing the thinking animation
            
        Version 1.0.2:
            - Added proper error handling
            - Added type hints
            - Added version tracking
        """
        try:
            if not hasattr(self, 'thinking_dots'):
                self.thinking_dots = 0
                
            if not header_frame:
                return
                
            # Get the thinking label from the header frame
            thinking_label = None
            for child in header_frame.winfo_children():
                if isinstance(child, ctk.CTkLabel) and "Thinking" in child.cget("text"):
                    thinking_label = child
                    break
                    
            if not thinking_label:
                return
                
            # Update dots
            self.thinking_dots = (self.thinking_dots + 1) % 4
            dots = "." * self.thinking_dots
            thinking_label.configure(text=f"Thinking{dots}")
            
            # Schedule next animation frame
            self.thinking_animation_id = self.after(500, lambda: self.animate_thinking(header_frame))
            
        except Exception as e:
            logging.error(f"Error in thinking animation: {str(e)}")

    def start_thinking_animation(self, header_frame: ctk.CTkFrame) -> None:
        """Start the thinking animation and timer
        
        Args:
            header_frame (ctk.CTkFrame): The frame containing the thinking animation
            
        Version 1.0.1:
            - Added proper error handling
            - Added type hints
        """
        try:
            if header_frame:
                self.current_thinking_label = header_frame
                self.thinking_start_time = time.time()
                self.animate_thinking(header_frame)
        except Exception as e:
            logging.error(f"Error starting thinking animation: {str(e)}")

    def stop_thinking_animation(self) -> None:
        """Stop the thinking animation and show final time
        
        Version 1.0.1:
            - Added proper error handling
            - Added type hints
        """
        try:
            if self.thinking_animation_id:
                self.after_cancel(self.thinking_animation_id)
                self.thinking_animation_id = None
                
            if self.current_thinking_label and self.thinking_start_time:
                elapsed = time.time() - self.thinking_start_time
                self.total_thinking_time += elapsed
                
                # Update the timer label if it exists
                for child in self.current_thinking_label.winfo_children():
                    if isinstance(child, ctk.CTkLabel) and "s" in child.cget("text"):
                        child.configure(text=f"{elapsed:.1f}s")
                        break
                        
                self.current_thinking_label = None
                self.thinking_start_time = None
                
        except Exception as e:
            logging.error(f"Error stopping thinking animation: {str(e)}")
            
def main():
    app = DeepSeekEngineerGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
