# main.py - Your FastAPI Backend (Simplified)
from fastapi import FastAPI, WebSocket
from typing import Dict

app = FastAPI()
canReceiveInput = True

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection established.")
    try:
        while canReceiveInput:
            data = await websocket.receive_text()
            print(f"Received from client: {data}")

            # --- Your Core Backend Logic Here ---
            # 1. Process the 'data' (user query, context, etc.)
            # 2. Interact with LLM, RAG, file system.
            response_text = f"Backend processed: '{data}'. (This is a placeholder response)"
            # ------------------------------------

            await websocket.send_text(response_text)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        print("WebSocket connection closed.")

if __name__ == "__main__":
    import uvicorn
    # Run the server. The host should be '127.0.0.1' or 'localhost' for local communication.
    # You might choose a different port if 8000 is occupied.
    uvicorn.run(app, host="127.0.0.1", port=8000)