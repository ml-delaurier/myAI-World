#!/usr/bin/env python3

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

# Version 1.0.0
# This module handles all database operations for the DeepSeek Engineer GUI
# It manages chat history, API credit balance, and thinking time tracking

class DatabaseManager:
    def __init__(self, db_path: str = "deepseek_engineer_history.db"):
        """Initialize database connection and create tables if they don't exist.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self) -> None:
        """Create necessary tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create chat_history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    is_reasoning BOOLEAN DEFAULT 0
                )
            """)
            
            # Create api_usage table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    credits_used REAL NOT NULL,
                    request_type TEXT NOT NULL,
                    conversation_id TEXT NOT NULL
                )
            """)
            
            # Create thinking_time table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS thinking_time (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    duration_seconds REAL NOT NULL,
                    conversation_id TEXT NOT NULL
                )
            """)
            
            conn.commit()
    
    def add_chat_message(self, role: str, content: str, conversation_id: str, is_reasoning: bool = False) -> None:
        """Add a new chat message to the history.
        
        Args:
            role (str): Message role ('user' or 'assistant')
            content (str): Message content
            conversation_id (str): Unique conversation identifier
            is_reasoning (bool): Whether this is a reasoning message
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO chat_history (timestamp, role, content, conversation_id, is_reasoning)
                VALUES (?, ?, ?, ?, ?)
                """,
                (datetime.now().isoformat(), role, content, conversation_id, is_reasoning)
            )
            conn.commit()
    
    def get_chat_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Retrieve chat history for a specific conversation.
        
        Args:
            conversation_id (str): Unique conversation identifier
            
        Returns:
            List[Dict[str, str]]: List of chat messages
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT role, content, is_reasoning
                FROM chat_history
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
                """,
                (conversation_id,)
            )
            return [{"role": role, "content": content, "is_reasoning": bool(is_reasoning)} 
                   for role, content, is_reasoning in cursor.fetchall()]
    
    def add_api_usage(self, credits_used: float, request_type: str, conversation_id: str) -> None:
        """Record API credit usage.
        
        Args:
            credits_used (float): Number of API credits used
            request_type (str): Type of API request
            conversation_id (str): Unique conversation identifier
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO api_usage (timestamp, credits_used, request_type, conversation_id)
                VALUES (?, ?, ?, ?)
                """,
                (datetime.now().isoformat(), credits_used, request_type, conversation_id)
            )
            conn.commit()
    
    def get_total_credits_used(self, conversation_id: Optional[str] = None) -> float:
        """Get total API credits used.
        
        Args:
            conversation_id (Optional[str]): If provided, get credits for specific conversation
            
        Returns:
            float: Total credits used
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if conversation_id:
                cursor.execute(
                    """
                    SELECT SUM(credits_used)
                    FROM api_usage
                    WHERE conversation_id = ?
                    """,
                    (conversation_id,)
                )
            else:
                cursor.execute("SELECT SUM(credits_used) FROM api_usage")
            
            result = cursor.fetchone()[0]
            return float(result) if result else 0.0
    
    def add_thinking_time(self, duration_seconds: float, conversation_id: str) -> None:
        """Record thinking time duration.
        
        Args:
            duration_seconds (float): Duration in seconds
            conversation_id (str): Unique conversation identifier
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO thinking_time (timestamp, duration_seconds, conversation_id)
                VALUES (?, ?, ?)
                """,
                (datetime.now().isoformat(), duration_seconds, conversation_id)
            )
            conn.commit()
    
    def get_total_thinking_time(self, conversation_id: Optional[str] = None) -> float:
        """Get total thinking time.
        
        Args:
            conversation_id (Optional[str]): If provided, get time for specific conversation
            
        Returns:
            float: Total thinking time in seconds
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if conversation_id:
                cursor.execute(
                    """
                    SELECT SUM(duration_seconds)
                    FROM thinking_time
                    WHERE conversation_id = ?
                    """,
                    (conversation_id,)
                )
            else:
                cursor.execute("SELECT SUM(duration_seconds) FROM thinking_time")
            
            result = cursor.fetchone()[0]
            return float(result) if result else 0.0
