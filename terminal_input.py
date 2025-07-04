import asyncio
import websockets
import sys

# Configuration for your FastAPI WebSocket server
SERVER_URL = "ws://127.0.0.1:8000"
CHAT_ENDPOINT = "/chat"

class ChatClient:
    """Chat client with proper state management for input/output coordination."""
    
    def __init__(self):
        self.waiting_for_response = False
        self.response_received = asyncio.Event()
        self.input_enabled = True
        
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
            sys.stdout.write("User: ")
            sys.stdout.flush()

# Global client instance
client = ChatClient()

async def send_message(websocket):
    """
    Asynchronously sends messages typed by the user to the WebSocket server.
    This runs in a loop, waiting for user input.
    """
    print("Type your message and press Enter to send. Type 'exit' to quit.")
    client.show_user_prompt()

    try:
        while True:
            # Wait for input to be enabled
            while not client.input_enabled:
                await asyncio.sleep(0.1)
            
            # Get input from the user
            message = await asyncio.to_thread(input)
            
            if message.lower() == 'exit':
                print("Exiting client...")
                break
            
            # Set waiting state before sending
            client.set_waiting_state(True)
            
            # Send the message
            await websocket.send(message)
            
            # Wait for response to be received before allowing next input
            await client.response_received.wait()
            
    except websockets.exceptions.ConnectionClosedOK:
        print("\nConnection closed by server (OK).")
    except websockets.exceptions.ConnectionClosedError:
        print("\nConnection closed by server (Error).")
    except Exception as e:
        print(f"\nError sending message: {e}")

async def receive_message(websocket):
    """
    Asynchronously receives messages from the WebSocket server and prints them.
    """
    try:
        while True:
            message = await websocket.recv()
            
            # Clear the waiting message and display server response
            sys.stdout.write("\r" + " " * 80 + "\r")
            sys.stdout.write(f"Server: {message}\n")
            
            # Reset waiting state and show user prompt
            client.set_waiting_state(False)
            client.show_user_prompt()
            
    except websockets.exceptions.ConnectionClosedOK:
        print("\nConnection closed by server (OK).")
    except websockets.exceptions.ConnectionClosedError:
        print("\nConnection closed by server (Error).")
    except Exception as e:
        print(f"\nError receiving message: {e}")
        # Reset state on error
        client.set_waiting_state(False)
        client.show_user_prompt()

async def main():
    """
    Establishes the WebSocket connection and runs send/receive tasks concurrently.
    """
    print(f"Attempting to connect to WebSocket server at {SERVER_URL}+{CHAT_ENDPOINT}...")
    try:
        async with websockets.connect(SERVER_URL+CHAT_ENDPOINT) as websocket:
            print("Successfully connected to the WebSocket server ChatEndpoint!")
            print("🤖 You are now chatting with OpenAI ChatGPT!")
            print("-" * 60)
            
            # Run sending and receiving tasks concurrently
            send_task = asyncio.create_task(send_message(websocket))
            receive_task = asyncio.create_task(receive_message(websocket))

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

