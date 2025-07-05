# main.py - Your FastAPI Backend with OpenAI Integration
# Import config FIRST to ensure environment variables are loaded properly
from config import get_config
from fastapi import FastAPI, WebSocket
from typing import Dict, Optional
import json
from openai_service import OpenAIService

# Get configuration instance (this loads .env with force override)
config = get_config()

app = FastAPI()
canReceiveInput = True

# Initialize OpenAI service with config
openai_service = OpenAIService(
    api_token=config.openai_api_key,
    model=config.openai_model
)

# Chat Endpoint
@app.websocket("/chat")
async def chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Chat connection established.")
    try:
        while canReceiveInput:
            data = await websocket.receive_text()
            print(f"Received from client: {data}")

            # Parse message data (could be JSON with screenshot or plain text)
            try:
                message_data = json.loads(data)
                user_message = message_data.get("text", "")
                screenshot_base64 = message_data.get("screenshot")
                
                if screenshot_base64:
                    print(f"Received message with screenshot (length: {len(screenshot_base64)})")
                else:
                    print("Received text-only message")
                    
            except json.JSONDecodeError:
                # Fallback to plain text for backward compatibility
                user_message = data
                screenshot_base64 = None
                print("Received plain text message")

            # --- OpenAI Integration ---
            if not config.is_api_configured:
                response_text = "⚠️ OpenAI API key not configured. Please check your .env file."
                print("OpenAI API not properly configured")
            else:
                try:
                    # Send user message to OpenAI and get response
                    response_text = await openai_service.get_chat_response(
                        user_message=user_message,
                        system_message="You are a helpful assistant. Provide clear and concise responses. If you receive a screenshot, analyze it and describe what you see.",
                        image_base64=screenshot_base64,
                        temperature=0.7,
                        max_tokens=1000
                    )
                    print(f"OpenAI response: {response_text}")
                    
                except Exception as e:
                    # Handle OpenAI API errors gracefully
                    error_message = f"Sorry, I encountered an error: {str(e)}"
                    print(f"OpenAI API error: {error_message}")
                    response_text = error_message
            # ------------------------

            await websocket.send_text(response_text)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        print("WebSocket connection closed.")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "model": config.openai_model,
        "api_configured": config.is_api_configured
    }

# Configuration endpoint to check current settings
@app.get("/config")
async def get_config_endpoint():
    return config.get_config_summary()

# Endpoint to update configuration dynamically
@app.post("/config/update")
async def update_config_endpoint(api_key: Optional[str] = None, model: Optional[str] = None):
    global openai_service
    
    if api_key or model:
        # Update configuration
        config.update_openai_config(api_key=api_key, model=model)
        
        # Reinitialize OpenAI service with new config
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
    
    print("🚀 Starting FastAPI Backend with OpenAI Integration")
    print("=" * 60)
    
    # Display configuration summary
    config_summary = config.get_config_summary()
    for key, value in config_summary.items():
        print(f"📋 {key}: {value}")
    
    print("=" * 60)
    
    if config.is_api_configured:
        print("✅ All systems ready! OpenAI API is configured.")
    else:
        print("⚠️  OpenAI API not configured - check your .env file")
    
    print(f"🌐 Server starting on http://{config.server_host}:{config.server_port}")
    
    # Run the server using config values
    uvicorn.run(
        app, 
        host=config.server_host, 
        port=config.server_port
    )