import asyncio
import websockets
import sys

# Configuration for your FastAPI WebSocket server
SERVER_URL = "ws://127.0.0.1:8000/ws"

async def send_message(websocket):
    """
    Asynchronously sends messages typed by the user to the WebSocket server.
    This runs in a loop, waiting for user input.
    """
    print("Type your message and press Enter to send. Type 'exit' to quit.")
    # Print the initial prompt
    sys.stdout.write("User: ")
    sys.stdout.flush()

    try:
        while True:
            # Get input from the user. input() is blocking, but in a separate task,
            # it won't block the entire event loop.
            message = await asyncio.to_thread(input) # Read input without a prompt string
            if message.lower() == 'exit':
                print("Exiting client...")
                break
            await websocket.send(message)
            
            # After sending, print the prompt again for the next input, but don't flush yet
            # We'll flush after the server response, or if no response, on the next input.
            # For now, just prepare the prompt for the next line.
            sys.stdout.write("You: ")
            sys.stdout.flush() # Flush immediately after sending to show prompt
            
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
            # Use \r to return the cursor to the beginning of the current line,
            # then clear the line (using spaces), then print the server message.
            # This prevents server messages from interleaving with the 'You:' prompt
            # or partial user input.
            sys.stdout.write("\r" + " " * (len("You: ") + 80) + "\r") # Clear the current line (adjust 80 for max line length)
            sys.stdout.write(f"Server: {message}\n")
            sys.stdout.write("User: ") # Re-display the prompt after the server's message
            sys.stdout.flush() # Ensure the prompt is visible immediately
            
    except websockets.exceptions.ConnectionClosedOK:
        print("\nConnection closed by server (OK).")
    except websockets.exceptions.ConnectionClosedError:
        print("\nConnection closed by server (Error).")
    except Exception as e:
        print(f"\nError receiving message: {e}")

async def main():
    """
    Establishes the WebSocket connection and runs send/receive tasks concurrently.
    """
    print(f"Attempting to connect to WebSocket server at {SERVER_URL}...")
    try:
        async with websockets.connect(SERVER_URL) as websocket:
            print("Successfully connected to the WebSocket server!")
            # Run sending and receiving tasks concurrently
            # If one task finishes, cancel the other.
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
            await asyncio.gather(*pending, return_exceptions=True) # Await cancellation

    # Catch the standard Python ConnectionRefusedError
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

