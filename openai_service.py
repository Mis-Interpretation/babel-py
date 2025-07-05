import httpx
import json
from typing import Optional, List, Dict, Any
import asyncio

class OpenAIService:
    """
    Encapsulated interface for communicating with OpenAI's ChatAPI.
    Provides async methods for sending requests and waiting for results.
    """
    
    def __init__(self, api_token: str, model: str = "gpt-3.5-turbo"):
        """
        Initialize the OpenAI service.
        
        Args:
            api_token (str): Your OpenAI API key
            model (str): The model to use (default: gpt-3.5-turbo)
        """
        self.api_token = api_token
        self.model = model
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    async def send_chat_request(
        self, 
        messages: List[Dict[str, Any]], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to OpenAI API.
        
        Args:
            messages (List[Dict[str, str]]): List of message objects with 'role' and 'content'
            temperature (float): Controls randomness (0.0 to 2.0)
            max_tokens (Optional[int]): Maximum tokens in response
            timeout (float): Request timeout in seconds
        
        Returns:
            Dict[str, Any]: The complete API response
        
        Raises:
            httpx.HTTPError: If the request fails
            json.JSONDecodeError: If response is not valid JSON
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
            
            except httpx.HTTPStatusError as e:
                error_detail = e.response.text if e.response else "No response"
                raise Exception(f"OpenAI API error {e.response.status_code}: {error_detail}")
            except httpx.TimeoutException:
                raise Exception("Request to OpenAI API timed out")
            except Exception as e:
                raise Exception(f"Unexpected error communicating with OpenAI: {str(e)}")
    
    async def get_chat_response(
        self, 
        user_message: str, 
        system_message: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        image_base64: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Simplified method to get a chat response from a user message.
        
        Args:
            user_message (str): The user's message
            system_message (Optional[str]): System message to set context
            conversation_history (Optional[List[Dict[str, Any]]]): Previous conversation
            image_base64 (Optional[str]): Base64 encoded image to include in the message
            **kwargs: Additional parameters passed to send_chat_request
        
        Returns:
            str: The assistant's response text
        """
        messages = []
        
        # Add system message if provided
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user message with optional image
        if image_base64:
            # Format for vision models with image
            user_content = [
                {"type": "text", "text": user_message},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                }
            ]
            messages.append({"role": "user", "content": user_content})
        else:
            # Standard text-only message
            messages.append({"role": "user", "content": user_message})
        
        try:
            response = await self.send_chat_request(messages, **kwargs)
            return response["choices"][0]["message"]["content"]
        except KeyError as e:
            raise Exception(f"Unexpected response format from OpenAI API: missing {e}")
    
    def update_model(self, model: str):
        """Update the model being used for requests."""
        self.model = model
    
    def update_api_token(self, api_token: str):
        """Update the API token."""
        self.api_token = api_token
        self.headers["Authorization"] = f"Bearer {self.api_token}"

# Example usage function for testing
async def test_openai_service():
    """Example usage of the OpenAI service (for testing purposes)."""
    # Note: Replace with your actual API key
    service = OpenAIService(
        api_token="your-openai-api-key-here",
        model="gpt-3.5-turbo"
    )
    
    try:
        response = await service.get_chat_response(
            user_message="Hello, how are you?",
            system_message="You are a helpful assistant."
        )
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Run test if file is executed directly
    asyncio.run(test_openai_service()) 