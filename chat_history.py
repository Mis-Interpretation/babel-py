"""
Chat History Module

This module handles storing and managing chat messages with configurable limits
for recent message history.
"""

import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path
import asyncio
from threading import Lock
from config import get_config

class ChatMessage:
    """Represents a single chat message."""
    
    def __init__(self, role: str, content: str, timestamp: Optional[str] = None, 
                 message_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a chat message.
        
        Args:
            role (str): The role of the message sender (user, assistant, system)
            content (str): The content of the message
            timestamp (Optional[str]): ISO timestamp, auto-generated if not provided
            message_id (Optional[str]): Unique identifier, auto-generated if not provided
            metadata (Optional[Dict[str, Any]]): Additional metadata
        """
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()
        self.message_id = message_id or self._generate_message_id()
        self.metadata = metadata or {}
    
    def _generate_message_id(self) -> str:
        """Generate a unique message ID."""
        import uuid
        return str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "message_id": self.message_id,
            "metadata": self.metadata
        }
    
    def to_openai_format(self) -> Dict[str, str]:
        """Convert message to OpenAI API format."""
        return {
            "role": self.role,
            "content": self.content
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create a ChatMessage from dictionary data."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp"),
            message_id=data.get("message_id"),
            metadata=data.get("metadata", {})
        )

class ChatHistory:
    """
    Manages chat message history with configurable limits and persistence.
    """
    
    def __init__(self, 
                 max_recent_messages: Optional[int] = None,
                 auto_save: bool = True,
                 history_file: Optional[str] = None):
        """
        Initialize the chat history manager.
        
        Args:
            max_recent_messages (Optional[int]): Maximum number of recent messages to keep in memory 
                                               (defaults to config value)
            auto_save (bool): Whether to automatically save messages to file
            history_file (Optional[str]): Path to history file for persistence
        """
        # Use config value if not provided
        if max_recent_messages is None:
            max_recent_messages = get_config().max_recent_messages
        self.max_recent_messages = max_recent_messages
        self.auto_save = auto_save
        self.history_file = Path(history_file) if history_file else Path("chat_history.json")
        
        # Thread-safe operations
        self._lock = Lock()
        
        # In-memory storage
        self._messages: List[ChatMessage] = []
        self._sessions: Dict[str, List[str]] = {}  # session_id -> [message_ids]
        
        # Load existing history if available
        if self.history_file.exists():
            self._load_history()
    
    def add_message(self, 
                   role: str, 
                   content: str, 
                   session_id: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a new message to the chat history.
        
        Args:
            role (str): The role of the message sender
            content (str): The content of the message
            session_id (Optional[str]): Session identifier for grouping messages
            metadata (Optional[Dict[str, Any]]): Additional metadata
        
        Returns:
            str: The message ID of the added message
        """
        with self._lock:
            # Create new message
            message = ChatMessage(role, content, metadata=metadata)
            
            # Add to messages list
            self._messages.append(message)
            
            # Track session if provided
            if session_id:
                if session_id not in self._sessions:
                    self._sessions[session_id] = []
                self._sessions[session_id].append(message.message_id)
            
            # Enforce message limit
            self._enforce_message_limit()
            
            # Auto-save if enabled
            if self.auto_save:
                self._save_history()
            
            return message.message_id
    
    def get_recent_messages(self, 
                          count: Optional[int] = None,
                          session_id: Optional[str] = None,
                          include_metadata: bool = False) -> List[Dict[str, Any]]:
        """
        Get recent messages.
        
        Args:
            count (Optional[int]): Number of messages to return (default: max_recent_messages)
            session_id (Optional[str]): Filter by session ID
            include_metadata (bool): Whether to include metadata in results
        
        Returns:
            List[Dict[str, Any]]: List of recent messages
        """
        with self._lock:
            # Ensure count is always a valid integer
            actual_count = count if count is not None else self.max_recent_messages
            actual_count = max(0, actual_count)  # Ensure non-negative
            
            if session_id:
                # Filter by session
                if session_id not in self._sessions:
                    return []
                
                message_ids = self._sessions[session_id][-actual_count:] if actual_count > 0 else []
                messages = [msg for msg in self._messages if msg.message_id in message_ids]
            else:
                # Get all recent messages
                messages = self._messages[-actual_count:] if actual_count > 0 else []
            
            if include_metadata:
                return [msg.to_dict() for msg in messages]
            else:
                return [msg.to_openai_format() for msg in messages]
    
    def get_conversation_history(self, 
                               session_id: Optional[str] = None,
                               openai_format: bool = True) -> List[Dict[str, Any]]:
        """
        Get conversation history formatted for OpenAI API.
        
        Args:
            session_id (Optional[str]): Session ID to filter by
            openai_format (bool): Whether to format for OpenAI API
        
        Returns:
            List[Dict[str, Any]]: Conversation history
        """
        messages = self.get_recent_messages(
            session_id=session_id,
            include_metadata=not openai_format
        )
        
        if openai_format:
            return [{"role": msg["role"], "content": msg["content"]} for msg in messages]
        else:
            return messages
    
    def clear_history(self, session_id: Optional[str] = None):
        """
        Clear chat history.
        
        Args:
            session_id (Optional[str]): Clear specific session or all if None
        """
        with self._lock:
            if session_id:
                # Clear specific session
                if session_id in self._sessions:
                    message_ids = self._sessions[session_id]
                    self._messages = [msg for msg in self._messages if msg.message_id not in message_ids]
                    del self._sessions[session_id]
            else:
                # Clear all history
                self._messages.clear()
                self._sessions.clear()
            
            # Save changes
            if self.auto_save:
                self._save_history()
    
    def get_message_count(self, session_id: Optional[str] = None) -> int:
        """
        Get the number of messages in history.
        
        Args:
            session_id (Optional[str]): Session ID to count, or None for all
        
        Returns:
            int: Number of messages
        """
        with self._lock:
            if session_id:
                return len(self._sessions.get(session_id, []))
            else:
                return len(self._messages)
    
    def update_message_limit(self, new_limit: int):
        """
        Update the maximum number of recent messages to keep.
        
        Args:
            new_limit (int): New message limit
        """
        with self._lock:
            self.max_recent_messages = new_limit
            self._enforce_message_limit()
            
            if self.auto_save:
                self._save_history()
    
    def get_sessions(self) -> List[str]:
        """
        Get all session IDs.
        
        Returns:
            List[str]: List of session IDs
        """
        with self._lock:
            return list(self._sessions.keys())
    
    def export_history(self, filename: Optional[str] = None) -> str:
        """
        Export chat history to a JSON file.
        
        Args:
            filename (Optional[str]): Output filename
        
        Returns:
            str: Path to the exported file
        """
        if filename is None:
            filename = f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_path = Path(filename)
        
        with self._lock:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "total_messages": len(self._messages),
                "sessions": dict(self._sessions),
                "messages": [msg.to_dict() for msg in self._messages]
            }
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return str(export_path)
    
    def import_history(self, filename: str):
        """
        Import chat history from a JSON file.
        
        Args:
            filename (str): Path to the import file
        """
        import_path = Path(filename)
        
        if not import_path.exists():
            raise FileNotFoundError(f"Import file not found: {filename}")
        
        with open(import_path, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        
        with self._lock:
            # Clear existing history
            self._messages.clear()
            self._sessions.clear()
            
            # Import messages
            for msg_data in import_data.get("messages", []):
                message = ChatMessage.from_dict(msg_data)
                self._messages.append(message)
            
            # Import sessions
            self._sessions = import_data.get("sessions", {})
            
            # Enforce limits
            self._enforce_message_limit()
            
            # Save
            if self.auto_save:
                self._save_history()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the chat history.
        
        Returns:
            Dict[str, Any]: Statistics
        """
        with self._lock:
            role_counts = {}
            for msg in self._messages:
                role_counts[msg.role] = role_counts.get(msg.role, 0) + 1
            
            return {
                "total_messages": len(self._messages),
                "total_sessions": len(self._sessions),
                "max_recent_messages": self.max_recent_messages,
                "role_distribution": role_counts,
                "auto_save_enabled": self.auto_save,
                "history_file": str(self.history_file),
                "oldest_message": self._messages[0].timestamp if self._messages else None,
                "newest_message": self._messages[-1].timestamp if self._messages else None
            }
    
    def _enforce_message_limit(self):
        """Enforce the maximum message limit."""
        if len(self._messages) > self.max_recent_messages:
            # Remove oldest messages
            excess_count = len(self._messages) - self.max_recent_messages
            removed_messages = self._messages[:excess_count]
            self._messages = self._messages[excess_count:]
            
            # Update session tracking
            removed_ids = {msg.message_id for msg in removed_messages}
            for session_id in list(self._sessions.keys()):
                self._sessions[session_id] = [
                    msg_id for msg_id in self._sessions[session_id] 
                    if msg_id not in removed_ids
                ]
                # Remove empty sessions
                if not self._sessions[session_id]:
                    del self._sessions[session_id]
    
    def _save_history(self):
        """Save history to file."""
        try:
            history_data = {
                "max_recent_messages": self.max_recent_messages,
                "auto_save": self.auto_save,
                "last_saved": datetime.now().isoformat(),
                "sessions": dict(self._sessions),
                "messages": [msg.to_dict() for msg in self._messages]
            }
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"❌ Error saving chat history: {e}")
    
    def _load_history(self):
        """Load history from file."""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            
            # Load configuration
            self.max_recent_messages = history_data.get("max_recent_messages", self.max_recent_messages)
            self.auto_save = history_data.get("auto_save", self.auto_save)
            
            # Load messages
            self._messages = []
            for msg_data in history_data.get("messages", []):
                message = ChatMessage.from_dict(msg_data)
                self._messages.append(message)
            
            # Load sessions
            self._sessions = history_data.get("sessions", {})
            
            print(f"✅ Loaded {len(self._messages)} messages from {self.history_file}")
            
        except Exception as e:
            print(f"❌ Error loading chat history: {e}")

# Global instance
chat_history = ChatHistory()

def get_chat_history_instance() -> ChatHistory:
    """Get the global chat history instance."""
    return chat_history

# Convenience functions
def add_message(role: str, content: str, session_id: Optional[str] = None, **kwargs) -> str:
    """Add a message using the global chat history."""
    return chat_history.add_message(role, content, session_id, **kwargs)

def get_recent_messages(count: Optional[int] = None, session_id: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
    """Get recent messages using the global chat history."""
    return chat_history.get_recent_messages(count, session_id, **kwargs)

def get_conversation_history(session_id: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
    """Get conversation history using the global chat history."""
    return chat_history.get_conversation_history(session_id, **kwargs)

def clear_history(session_id: Optional[str] = None):
    """Clear history using the global chat history."""
    chat_history.clear_history(session_id)

if __name__ == "__main__":
    # Test the chat history
    print("🔧 Chat History Test")
    print("=" * 50)
    
    history = ChatHistory()
    
    # Add some test messages
    history.add_message("user", "Hello!", session_id="test_session")
    history.add_message("assistant", "Hi there! How can I help you?", session_id="test_session")
    history.add_message("user", "What's the weather like?", session_id="test_session")
    history.add_message("assistant", "I don't have access to current weather data.", session_id="test_session")
    
    # Test retrieval
    recent = history.get_recent_messages(count=5, session_id="test_session")
    print(f"Recent messages: {len(recent)}")
    for msg in recent:
        print(f"  {msg['role']}: {msg['content']}")
    
    # Test statistics
    stats = history.get_statistics()
    print(f"\nStatistics:")
    print(json.dumps(stats, indent=2))
    
    # Test export
    export_file = history.export_history("test_export.json")
    print(f"\nExported to: {export_file}")
    
    print("\n✅ Chat History test completed!") 