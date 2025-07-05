"""
Prompt Assembler Module

This module handles reading prompt files from a prompts folder and assembling them
into complete prompts for the OpenAI service.
"""

import os
from typing import Dict, List, Optional, Any
import json
from pathlib import Path

class PromptAssembler:
    """
    Handles reading and assembling prompts from text files in a prompts folder.
    """
    
    def __init__(self, prompts_folder: str = "prompts"):
        """
        Initialize the PromptAssembler.
        
        Args:
            prompts_folder (str): Path to the folder containing prompt files
        """
        self.prompts_folder = Path(prompts_folder)
        self.prompts_cache: Dict[str, str] = {}
        self._ensure_prompts_folder()
    
    def _ensure_prompts_folder(self):
        """Create the prompts folder if it doesn't exist."""
        if not self.prompts_folder.exists():
            self.prompts_folder.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created prompts folder: {self.prompts_folder}")
            
            # Create some example prompt files
            self._create_example_prompts()
    
    def _create_example_prompts(self):
        """Create example prompt files for demonstration."""
        example_prompts = {
            "system_default.txt": "You are a helpful AI assistant. Provide clear, concise, and accurate responses.",
            "system_creative.txt": "You are a creative AI assistant. Be imaginative and think outside the box while remaining helpful.",
            "system_technical.txt": "You are a technical AI assistant. Provide detailed, accurate technical information and explanations.",
            "greeting.txt": "Hello! How can I help you today?",
            "closing.txt": "Is there anything else you'd like to know?",
        }
        
        for filename, content in example_prompts.items():
            prompt_file = self.prompts_folder / filename
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"✅ Created example prompt files in {self.prompts_folder}")
    
    def load_prompt(self, filename: str, use_cache: bool = True) -> Optional[str]:
        """
        Load a prompt from a text file.
        
        Args:
            filename (str): Name of the prompt file (with or without .txt extension)
            use_cache (bool): Whether to use cached prompts for better performance
        
        Returns:
            Optional[str]: The prompt content or None if file doesn't exist
        """
        # Add .txt extension if not present
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        # Check cache first
        if use_cache and filename in self.prompts_cache:
            return self.prompts_cache[filename]
        
        prompt_file = self.prompts_folder / filename
        
        if not prompt_file.exists():
            print(f"⚠️  Prompt file not found: {prompt_file}")
            return None
        
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Cache the prompt
            if use_cache:
                self.prompts_cache[filename] = content
            
            return content
            
        except Exception as e:
            print(f"❌ Error reading prompt file {filename}: {e}")
            return None
    
    def list_prompts(self) -> List[str]:
        """
        List all available prompt files.
        
        Returns:
            List[str]: List of prompt filenames
        """
        try:
            return [f.name for f in self.prompts_folder.iterdir() if f.suffix == '.txt']
        except Exception as e:
            print(f"❌ Error listing prompts: {e}")
            return []
    
    def assemble_prompt(self, 
                       system_prompt: Optional[str] = None,
                       user_prompt: Optional[str] = None,
                       additional_prompts: Optional[List[str]] = None,
                       template_vars: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Assemble a complete prompt from multiple sources.
        
        Args:
            system_prompt (Optional[str]): System prompt filename or direct content
            user_prompt (Optional[str]): User prompt filename or direct content
            additional_prompts (Optional[List[str]]): Additional prompt filenames to include
            template_vars (Optional[Dict[str, str]]): Variables to substitute in prompts
        
        Returns:
            Dict[str, Any]: Assembled prompt with system and user messages
        """
        messages = []
        
        # Handle system prompt
        if system_prompt:
            system_content = self._resolve_prompt_content(system_prompt, template_vars)
            if system_content:
                messages.append({"role": "system", "content": system_content})
        
        # Handle additional prompts (add to system or as separate messages)
        if additional_prompts:
            for prompt in additional_prompts:
                content = self._resolve_prompt_content(prompt, template_vars)
                if content:
                    # You can modify this logic based on your needs
                    messages.append({"role": "system", "content": content})
        
        # Handle user prompt
        if user_prompt:
            user_content = self._resolve_prompt_content(user_prompt, template_vars)
            if user_content:
                messages.append({"role": "user", "content": user_content})
        
        return {
            "messages": messages,
            "total_prompts": len(messages),
            "assembled_at": self._get_timestamp()
        }
    
    def _resolve_prompt_content(self, prompt: str, template_vars: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Resolve prompt content from filename or direct content.
        
        Args:
            prompt (str): Either a filename or direct prompt content
            template_vars (Optional[Dict[str, str]]): Variables to substitute
        
        Returns:
            Optional[str]: Resolved prompt content
        """
        # Check if it's a filename (contains .txt or exists as file)
        if prompt.endswith('.txt') or (self.prompts_folder / f"{prompt}.txt").exists():
            content = self.load_prompt(prompt)
        else:
            # Treat as direct content
            content = prompt
        
        # Apply template variable substitution
        if content and template_vars:
            try:
                content = content.format(**template_vars)
            except KeyError as e:
                print(f"⚠️  Template variable not found: {e}")
            except Exception as e:
                print(f"⚠️  Template substitution error: {e}")
        
        return content
    
    def create_prompt_template(self, filename: str, content: str, overwrite: bool = False) -> bool:
        """
        Create a new prompt template file.
        
        Args:
            filename (str): Name of the prompt file
            content (str): Content of the prompt
            overwrite (bool): Whether to overwrite existing files
        
        Returns:
            bool: Success status
        """
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        prompt_file = self.prompts_folder / filename
        
        if prompt_file.exists() and not overwrite:
            print(f"⚠️  Prompt file already exists: {filename}")
            return False
        
        try:
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Clear cache for this file
            if filename in self.prompts_cache:
                del self.prompts_cache[filename]
            
            print(f"✅ Created prompt template: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating prompt template {filename}: {e}")
            return False
    
    def clear_cache(self):
        """Clear the prompts cache."""
        self.prompts_cache.clear()
        print("🗑️  Prompts cache cleared")
    
    def get_prompt_info(self) -> Dict[str, Any]:
        """
        Get information about the prompt assembler.
        
        Returns:
            Dict[str, Any]: Information about prompts and cache
        """
        return {
            "prompts_folder": str(self.prompts_folder),
            "available_prompts": self.list_prompts(),
            "cached_prompts": list(self.prompts_cache.keys()),
            "total_prompts": len(self.list_prompts()),
            "cache_size": len(self.prompts_cache)
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for metadata."""
        from datetime import datetime
        return datetime.now().isoformat()

# Global instance
prompt_assembler = PromptAssembler()

def get_prompt_assembler() -> PromptAssembler:
    """Get the global prompt assembler instance."""
    return prompt_assembler

# Convenience functions
def load_prompt(filename: str) -> Optional[str]:
    """Load a prompt using the global assembler."""
    return prompt_assembler.load_prompt(filename)

def assemble_prompt(**kwargs) -> Dict[str, Any]:
    """Assemble a prompt using the global assembler."""
    return prompt_assembler.assemble_prompt(**kwargs)

def list_prompts() -> List[str]:
    """List all available prompts."""
    return prompt_assembler.list_prompts()

if __name__ == "__main__":
    # Test the prompt assembler
    print("🔧 Prompt Assembler Test")
    print("=" * 50)
    
    assembler = PromptAssembler()
    
    # Show available prompts
    prompts = assembler.list_prompts()
    print(f"Available prompts: {prompts}")
    
    # Test loading a prompt
    if prompts:
        first_prompt = prompts[0]
        content = assembler.load_prompt(first_prompt)
        print(f"\nContent of '{first_prompt}':")
        print(content)
    
    # Test assembling a prompt
    assembled = assembler.assemble_prompt(
        system_prompt="system_default.txt",
        user_prompt="Hello, can you help me with Python?",
        template_vars={"name": "User"}
    )
    
    print(f"\nAssembled prompt:")
    print(json.dumps(assembled, indent=2))
    
    # Show info
    info = assembler.get_prompt_info()
    print(f"\nPrompt Assembler Info:")
    print(json.dumps(info, indent=2)) 