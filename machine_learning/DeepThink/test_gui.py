#!/usr/bin/env python3

import pytest
import os
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from gui import DeepSeekEngineerGUI, MessageBubble, FileToCreate, FileToEdit, AssistantResponse

@pytest.fixture
def app():
    """
    Fixture to create a test instance of the DeepSeekEngineerGUI
    """
    with patch('gui.OpenAI'), \
         patch('gui.load_dotenv'), \
         patch('gui.DatabaseManager'), \
         patch('customtkinter.CTk'), \
         patch('customtkinter.CTkFrame'), \
         patch('customtkinter.CTkButton'), \
         patch('customtkinter.CTkLabel'), \
         patch('customtkinter.CTkTextbox'), \
         patch('customtkinter.CTkScrollableFrame'), \
         patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test_key'}):
        
        app = DeepSeekEngineerGUI()
        yield app
        app.destroy()

def test_initialization(app):
    """Test that the GUI initializes correctly with default values"""
    assert app.current_conversation_name == "New Chat"
    assert len(app.conversation_history) == 1
    assert app.conversation_history[0]["role"] == "system"
    assert isinstance(app.models, dict)
    assert "DeepSeek-V3" in app.models
    assert "DeepSeek-R1" in app.models

def test_create_message_bubble(app):
    """Test message bubble creation"""
    text = "Test message"
    bubble = app.create_message_bubble(text, is_user=True)
    assert isinstance(bubble, MagicMock)

def test_process_message(app):
    """Test message processing"""
    with patch.object(app, 'append_to_conversation') as mock_append:
        app.process_message("Test message")
        mock_append.assert_called()

def test_handle_assistant_response(app):
    """Test handling of assistant responses"""
    response = {
        "assistant_reply": "Test reply",
        "files_to_create": [],
        "files_to_edit": []
    }
    with patch.object(app, 'append_to_conversation') as mock_append:
        app.handle_assistant_response(json.dumps(response))
        mock_append.assert_called_with("Test reply", is_user=False)

def test_file_models():
    """Test the file operation models"""
    file_create = FileToCreate(path="test.py", content="print('test')")
    assert file_create.path == "test.py"
    assert file_create.content == "print('test')"

    file_edit = FileToEdit(
        path="test.py",
        original_snippet="old code",
        new_snippet="new code"
    )
    assert file_edit.path == "test.py"
    assert file_edit.original_snippet == "old code"
    assert file_edit.new_snippet == "new code"
