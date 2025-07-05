# main_with_new_features.py - Enhanced FastAPI Backend with Prompt Assembler and Chat History
# This file demonstrates how to integrate the new features with your existing main.py

from config import get_config
from fastapi import FastAPI, WebSocket
from typing import Dict, Optional
import json
from openai_service import OpenAIService

# Import the new modules
from prompt_assembler import get_prompt_assembler, assemble_prompt
from chat_history import get_chat_history_instance, add_message, get_conversation_history

# Get configuration instance
config = get_config()

app = FastAPI()
canReceiveInput = True

# Initialize services
openai_service = OpenAIService(
    api_token=config.openai_api_key,
    model=config.openai_model
)

# Initialize new services
prompt_assembler = get_prompt_assembler()
chat_history = get_chat_history_instance()

# Chat Endpoint with enhanced features
@app.websocket("/chat")
async def chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Chat connection established.")
    
    # Generate a unique session ID for this WebSocket connection
    import uuid
    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")
    
    try:
        while canReceiveInput:
            data = await websocket.receive_text()
            print(f"Received from client: {data}")

            # Parse message data
            try:
                message_data = json.loads(data)
                user_message = message_data.get("text", "")
                screenshot_base64 = message_data.get("screenshot")
                
                # Optional: Use custom system prompt from prompt files
                custom_system_prompt = message_data.get("system_prompt", "system_default")
                
                if screenshot_base64:
                    print(f"Received message with screenshot (length: {len(screenshot_base64)})")
                else:
                    print("Received text-only message")
                    
            except json.JSONDecodeError:
                # Fallback to plain text
                user_message = data
                screenshot_base64 = None
                custom_system_prompt = "system_default"
                print("Received plain text message")

            # Store the user message in chat history
            add_message("user", user_message, session_id=session_id)

            # --- Enhanced OpenAI Integration with Prompt Assembler ---
            if not config.is_api_configured:
                response_text = "⚠️ OpenAI API key not configured. Please check your .env file."
                print("OpenAI API not properly configured")
            else:
                try:
                    # Assemble the prompt using the prompt assembler
                    assembled_prompt = assemble_prompt(
                        system_prompt=custom_system_prompt,
                        additional_prompts=["greeting"] if not get_conversation_history(session_id) else None,
                        template_vars={"user_name": "User", "timestamp": "now"}
                    )
                    
                    # Get conversation history for context
                    conversation_history = get_conversation_history(session_id=session_id)
                    
                    # Combine system messages from prompt assembler
                    system_messages = [msg for msg in assembled_prompt["messages"] if msg["role"] == "system"]
                    system_content = " ".join([msg["content"] for msg in system_messages])
                    
                    # Send to OpenAI with conversation history
                    response_text = await openai_service.get_chat_response(
                        user_message=user_message,
                        system_message=system_content,
                        conversation_history=conversation_history,
                        image_base64=screenshot_base64,
                        temperature=0.7,
                        max_tokens=config.max_tokens
                    )
                    
                    print(f"OpenAI response: {response_text}")
                    
                except Exception as e:
                    error_message = f"Sorry, I encountered an error: {str(e)}"
                    print(f"OpenAI API error: {error_message}")
                    response_text = error_message

            # Store the assistant response in chat history
            add_message("assistant", response_text, session_id=session_id)

            await websocket.send_text(response_text)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        print(f"WebSocket connection closed for session: {session_id}")

# Enhanced health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "model": config.openai_model,
        "api_configured": config.is_api_configured,
        "prompt_assembler_info": prompt_assembler.get_prompt_info(),
        "chat_history_stats": chat_history.get_statistics()
    }

# New endpoint to get chat history
@app.get("/chat/history")
async def get_chat_history_endpoint(session_id: Optional[str] = None, count: Optional[int] = 10):
    """Get chat history for a session or all sessions."""
    try:
        history = get_conversation_history(session_id=session_id)
        return {
            "session_id": session_id,
            "message_count": len(history),
            "messages": history[-count:] if count else history
        }
    except Exception as e:
        return {"error": str(e)}

# New endpoint to manage prompts
@app.get("/prompts")
async def list_prompts():
    """List all available prompt templates."""
    return {
        "available_prompts": prompt_assembler.list_prompts(),
        "prompts_info": prompt_assembler.get_prompt_info()
    }

@app.post("/prompts/create")
async def create_prompt(filename: str, content: str, overwrite: bool = False):
    """Create a new prompt template."""
    success = prompt_assembler.create_prompt_template(filename, content, overwrite)
    return {
        "success": success,
        "filename": filename,
        "message": "Prompt created successfully" if success else "Failed to create prompt"
    }

@app.get("/prompts/{filename}")
async def get_prompt(filename: str):
    """Get a specific prompt template."""
    content = prompt_assembler.load_prompt(filename)
    if content:
        return {
            "filename": filename,
            "content": content
        }
    else:
        return {"error": f"Prompt '{filename}' not found"}

# New endpoint to test prompt assembly
@app.post("/prompts/assemble")
async def assemble_prompt_endpoint(
    system_prompt: Optional[str] = None,
    user_prompt: Optional[str] = None,
    additional_prompts: Optional[list] = None,
    template_vars: Optional[dict] = None
):
    """Test prompt assembly with given parameters."""
    try:
        assembled = assemble_prompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            additional_prompts=additional_prompts,
            template_vars=template_vars
        )
        return assembled
    except Exception as e:
        return {"error": str(e)}

# New endpoint to clear chat history
@app.delete("/chat/history")
async def clear_chat_history(session_id: Optional[str] = None):
    """Clear chat history for a session or all sessions."""
    try:
        chat_history.clear_history(session_id)
        return {
            "message": f"Chat history cleared for session: {session_id}" if session_id else "All chat history cleared"
        }
    except Exception as e:
        return {"error": str(e)}

# Configuration endpoint (unchanged)
@app.get("/config")
async def get_config_endpoint():
    return config.get_config_summary()

# Update configuration endpoint (unchanged)
@app.post("/config/update")
async def update_config_endpoint(api_key: Optional[str] = None, model: Optional[str] = None):
    global openai_service
    
    if api_key or model:
        config.update_openai_config(api_key=api_key, model=model)
        openai_service = OpenAIService(
            api_token=config.openai_api_key,
            model=config.openai_model
        )
        return {
            "message": "Configuration updated successfully",
            "config": config.get_config_summary()
        }
    else:
        return {"error": "No configuration changes provided"}

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Enhanced FastAPI Backend")
    print("=" * 60)
    
    # Display configuration summary
    config_summary = config.get_config_summary()
    for key, value in config_summary.items():
        print(f"📋 {key}: {value}")
    
    # Display prompt assembler info
    prompt_info = prompt_assembler.get_prompt_info()
    print(f"📝 Available prompts: {len(prompt_info['available_prompts'])}")
    print(f"📝 Prompts folder: {prompt_info['prompts_folder']}")
    
    # Display chat history info
    history_stats = chat_history.get_statistics()
    print(f"💬 Chat history limit: {history_stats['max_recent_messages']}")
    print(f"💬 Auto-save enabled: {history_stats['auto_save_enabled']}")
    
    print("=" * 60)
    
    if config.is_api_configured:
        print("✅ All systems ready! Enhanced features enabled.")
    else:
        print("⚠️  OpenAI API not configured - check your .env file")
    
    print(f"🌐 Server starting on http://{config.server_host}:{config.server_port}")
    print("\n🆕 New Features Available:")
    print("  - GET /prompts - List available prompt templates")
    print("  - POST /prompts/create - Create new prompt template")
    print("  - GET /prompts/{filename} - Get specific prompt")
    print("  - POST /prompts/assemble - Test prompt assembly")
    print("  - GET /chat/history - Get chat history")
    print("  - DELETE /chat/history - Clear chat history")
    
    # Run the server
    uvicorn.run(
        app, 
        host=config.server_host, 
        port=config.server_port
    ) 