import asyncio
import websockets
import sys
import json
from screenshot_service import ScreenshotService

# Configuration for your FastAPI WebSocket server
SERVER_URL = "ws://127.0.0.1:8000"
CHAT_ENDPOINT = "/chat"

class ChatClient:
    """Chat client with proper state management for input/output coordination."""
    
    def __init__(self, debug_mode: bool = False):
        self.waiting_for_response = False
        self.response_received = asyncio.Event()
        self.input_enabled = True
        self.screenshot_service = ScreenshotService()
        self.screenshot_enabled = True
        # Enable debug mode for saving screenshots to files
        self.screenshot_service.enable_debug(debug_mode)
        
    def set_waiting_state(self, waiting: bool):
        """Set the waiting state and update the display accordingly."""
        self.waiting_for_response = waiting
        if waiting:
            self.input_enabled = False
            self.response_received.clear()
            # Clear current line and show waiting message
            sys.stdout.write("\r" + " " * 80 + "\r")
            sys.stdout.write("⏳ Waiting for backend response...")
            sys.stdout.flush()
        else:
            self.input_enabled = True
            self.response_received.set()
    
    def show_user_prompt(self):
        """Show the user input prompt."""
        if not self.waiting_for_response:
            sys.stdout.write("\r" + " " * 80 + "\r")
            sys.stdout.write("😺User: ")
            sys.stdout.flush()

# Global client instance (will be initialized in main)
client = None

async def send_message(websocket, chat_client):
    """
    Asynchronously sends messages typed by the user to the WebSocket server.
    This runs in a loop, waiting for user input.
    """
    print("Type your message and press Enter to send. Type 'exit' to quit.")
    chat_client.show_user_prompt()

    try:
        while True:
            # Wait for input to be enabled
            while not chat_client.input_enabled:
                await asyncio.sleep(0.1)
            
            # Get input from the user
            message = await asyncio.to_thread(input)
            
            if message.lower() == 'exit':
                print("Exiting client...")
                break
            
            # Set waiting state before sending
            chat_client.set_waiting_state(True)
            
            # Prepare message data with optional screenshot
            message_data = {
                "text": message,
                "screenshot": None
            }
            
            # Capture screenshot if enabled
            if chat_client.screenshot_enabled:
                try:
                    sys.stdout.write("\r" + " " * 80 + "\r")
                    sys.stdout.write("📸 Capturing screenshot...")
                    sys.stdout.flush()
                    
                    screenshot_base64 = await asyncio.to_thread(
                        chat_client.screenshot_service.capture_primary_monitor, 
                        70  # Quality setting
                    )
                    message_data["screenshot"] = screenshot_base64
                    
                    sys.stdout.write("\r" + " " * 80 + "\r")
                    sys.stdout.write("⏳ Sending message with screenshot...")
                    sys.stdout.flush()
                    
                except Exception as e:
                    sys.stdout.write("\r" + " " * 80 + "\r")
                    sys.stdout.write(f"⚠️ Screenshot failed: {e}")
                    sys.stdout.flush()
            
            # Send the message data as JSON
            await websocket.send(json.dumps(message_data))
            
            # Wait for response to be received before allowing next input
            await chat_client.response_received.wait()
            
    except websockets.exceptions.ConnectionClosedOK:
        print("\nConnection closed by server (OK).")
    except websockets.exceptions.ConnectionClosedError:
        print("\nConnection closed by server (Error).")
    except Exception as e:
        print(f"\nError sending message: {e}")

async def receive_message(websocket, chat_client):
    """
    Asynchronously receives messages from the WebSocket server and prints them.
    """
    try:
        while True:
            message = await websocket.recv()
            
            # Clear the waiting message and display server response
            sys.stdout.write("\r" + " " * 80 + "\r")
            sys.stdout.write(f"🤖Server: {message}\n")
            
            # Reset waiting state and show user prompt
            chat_client.set_waiting_state(False)
            chat_client.show_user_prompt()
            
    except websockets.exceptions.ConnectionClosedOK:
        print("\nConnection closed by server (OK).")
    except websockets.exceptions.ConnectionClosedError:
        print("\nConnection closed by server (Error).")
    except Exception as e:
        print(f"\nError receiving message: {e}")
        # Reset state on error
        chat_client.set_waiting_state(False)
        chat_client.show_user_prompt()

async def main():
    """
    Establishes the WebSocket connection and runs send/receive tasks concurrently.
    """
    # Check for debug mode flag
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv
    
    # Create chat client instance
    chat_client = ChatClient(debug_mode=debug_mode)
    
    print(f"Attempting to connect to WebSocket server at {SERVER_URL}{CHAT_ENDPOINT}...")
    try:
        async with websockets.connect(SERVER_URL+CHAT_ENDPOINT) as websocket:
            print("Successfully connected to the WebSocket server ChatEndpoint!")
            print("🤖 You are now chatting with OpenAI ChatGPT!")
            if debug_mode:
                print("🐛 Debug mode enabled - screenshots will be saved to debug_screenshots/ folder")
            print("-" * 60)
            
            # Run sending and receiving tasks concurrently
            send_task = asyncio.create_task(send_message(websocket, chat_client))
            receive_task = asyncio.create_task(receive_message(websocket, chat_client))

            # Wait for either task to complete (e.g., user types 'exit' or connection closes)
            done, pending = await asyncio.wait(
                [send_task, receive_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel any remaining pending tasks
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)

    except ConnectionRefusedError:
        print(f"\nConnection refused. Is the FastAPI server running at {SERVER_URL}?")
        print("Please ensure your FastAPI server is started in another terminal.")
    except Exception as e:
        print(f"\nCould not connect to WebSocket server: {e}")

if __name__ == "__main__":
    # For Windows, asyncio needs a specific event loop policy for some environments
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())

