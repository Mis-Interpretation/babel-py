"""
Unity Knowledge Retriever
Clean interface for querying the Pinecone knowledge base
"""

import json
from typing import List, Dict, Any, Optional
import logging
from openai import OpenAI
try:
    from .pinecone_manager import PineconeManager
except ImportError:
    from pinecone_manager import PineconeManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnityKnowledgeRetriever:
    def __init__(self, pinecone_api_key: Optional[str] = None, openai_api_key: Optional[str] = None, 
                 index_name: str = "unity-knowledge-base"):
        """Initialize the knowledge retriever"""
        self.pinecone_manager = PineconeManager(api_key=pinecone_api_key, index_name=index_name)
        
        # Initialize OpenAI client for query embeddings
        if openai_api_key:
            self.openai_client = OpenAI(api_key=openai_api_key)
        else:
            # Try to get from config
            try:
                from config import get_openai_api_key
                api_key = get_openai_api_key()
                if api_key and api_key != "sk-your-actual-openai-api-key-here":
                    self.openai_client = OpenAI(api_key=api_key)
                else:
                    raise ValueError("OpenAI API key not configured")
            except ImportError:
                raise ValueError("OpenAI API key not provided and config module not found")
    
    def _generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for a query string"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=query
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise
    
    def search_unity_knowledge(self, query: str, max_results: int = 5, 
                              content_type: Optional[str] = None, 
                              source: Optional[str] = None) -> Dict[str, Any]:
        """
        Main search function for Unity knowledge
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            content_type: Filter by content type (api_reference, tutorial, guide, code_example)
            source: Filter by source (unity, unreal, etc.)
        
        Returns:
            Dictionary with search results and metadata
        """
        try:
            # Generate query embedding
            query_embedding = self._generate_query_embedding(query)
            
            # Build filter
            filter_dict = {}
            if content_type:
                filter_dict["content_type"] = content_type
            if source:
                filter_dict["source"] = source
            
            # Search Pinecone
            raw_results = self.pinecone_manager.search_similar(
                query_embedding=query_embedding,
                top_k=max_results,
                filter_dict=filter_dict if filter_dict else None
            )
            
            # Format results
            formatted_results = self._format_search_results(raw_results, query)
            
            return {
                "query": query,
                "results": formatted_results,
                "total_results": len(formatted_results),
                "filters_applied": filter_dict,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error searching Unity knowledge: {e}")
            return {
                "query": query,
                "results": [],
                "total_results": 0,
                "error": str(e),
                "status": "error"
            }
    
    def get_code_examples(self, api_name: str, max_results: int = 3) -> Dict[str, Any]:
        """
        Find code examples for a specific Unity API
        
        Args:
            api_name: Name of the Unity API/class/method
            max_results: Maximum number of examples to return
        
        Returns:
            Dictionary with code examples and metadata
        """
        try:
            # Search for code examples specifically
            query = f"{api_name} code example usage"
            query_embedding = self._generate_query_embedding(query)
            
            # Filter for content with code
            filter_dict = {
                "has_code_in_chunk": True
            }
            
            raw_results = self.pinecone_manager.search_similar(
                query_embedding=query_embedding,
                top_k=max_results * 2,  # Get more results to filter
                filter_dict=filter_dict
            )
            
            # Filter and format results
            code_results = []
            for result in raw_results:
                metadata = result.get("metadata", {})
                if (api_name.lower() in metadata.get("original_title", "").lower() or 
                    api_name.lower() in metadata.get("original_url", "").lower()):
                    code_results.append(result)
                    if len(code_results) >= max_results:
                        break
            
            formatted_results = self._format_search_results(code_results, query)
            
            return {
                "api_name": api_name,
                "results": formatted_results,
                "total_results": len(formatted_results),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error getting code examples: {e}")
            return {
                "api_name": api_name,
                "results": [],
                "total_results": 0,
                "error": str(e),
                "status": "error"
            }
    
    def get_related_concepts(self, topic: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Find related Unity concepts and workflows
        
        Args:
            topic: Unity topic or concept
            max_results: Maximum number of related concepts to return
        
        Returns:
            Dictionary with related concepts and metadata
        """
        try:
            # Search for guides and tutorials related to the topic
            query = f"{topic} Unity guide tutorial workflow"
            query_embedding = self._generate_query_embedding(query)
            
            # Prefer guides and tutorials
            filter_dict = {
                "content_type": {"$in": ["guide", "tutorial", "api_reference"]}
            }
            
            raw_results = self.pinecone_manager.search_similar(
                query_embedding=query_embedding,
                top_k=max_results,
                filter_dict=filter_dict
            )
            
            formatted_results = self._format_search_results(raw_results, query)
            
            return {
                "topic": topic,
                "results": formatted_results,
                "total_results": len(formatted_results),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error getting related concepts: {e}")
            return {
                "topic": topic,
                "results": [],
                "total_results": 0,
                "error": str(e),
                "status": "error"
            }
    
    def search_by_category(self, query: str, category: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Search within a specific Unity category
        
        Args:
            query: Search query
            category: Unity category (physics, rendering, ui, scripting, etc.)
            max_results: Maximum number of results
        
        Returns:
            Dictionary with search results
        """
        try:
            query_embedding = self._generate_query_embedding(query)
            
            # Filter by category if it exists in metadata
            filter_dict = {
                "category": category
            }
            
            raw_results = self.pinecone_manager.search_similar(
                query_embedding=query_embedding,
                top_k=max_results,
                filter_dict=filter_dict
            )
            
            # If no results with category filter, try broader search
            if not raw_results:
                enhanced_query = f"{query} {category} Unity"
                query_embedding = self._generate_query_embedding(enhanced_query)
                raw_results = self.pinecone_manager.search_similar(
                    query_embedding=query_embedding,
                    top_k=max_results
                )
            
            formatted_results = self._format_search_results(raw_results, query)
            
            return {
                "query": query,
                "category": category,
                "results": formatted_results,
                "total_results": len(formatted_results),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error searching by category: {e}")
            return {
                "query": query,
                "category": category,
                "results": [],
                "total_results": 0,
                "error": str(e),
                "status": "error"
            }
    
    def get_contextual_docs(self, query: str, context_type: str = "beginner", 
                           max_results: int = 5) -> Dict[str, Any]:
        """
        Get contextual documentation based on user expertise level
        
        Args:
            query: Search query
            context_type: User context (beginner, intermediate, advanced, programmer, artist, designer)
            max_results: Maximum number of results
        
        Returns:
            Dictionary with contextual results
        """
        try:
            # Enhance query based on context
            if context_type == "beginner":
                enhanced_query = f"{query} Unity getting started tutorial basics"
            elif context_type == "advanced":
                enhanced_query = f"{query} Unity advanced techniques optimization"
            elif context_type == "programmer":
                enhanced_query = f"{query} Unity scripting C# code API"
            elif context_type == "artist":
                enhanced_query = f"{query} Unity visual art graphics rendering"
            elif context_type == "designer":
                enhanced_query = f"{query} Unity game design workflow UI UX"
            else:
                enhanced_query = query
            
            query_embedding = self._generate_query_embedding(enhanced_query)
            
            raw_results = self.pinecone_manager.search_similar(
                query_embedding=query_embedding,
                top_k=max_results
            )
            
            formatted_results = self._format_search_results(raw_results, query)
            
            return {
                "query": query,
                "context_type": context_type,
                "results": formatted_results,
                "total_results": len(formatted_results),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error getting contextual docs: {e}")
            return {
                "query": query,
                "context_type": context_type,
                "results": [],
                "total_results": 0,
                "error": str(e),
                "status": "error"
            }
    
    def _format_search_results(self, raw_results: List[Dict], query: str) -> List[Dict]:
        """Format raw Pinecone results for consumption"""
        formatted_results = []
        
        for result in raw_results:
            metadata = result.get("metadata", {})
            
            formatted_result = {
                "content": self._get_content_preview(metadata),
                "source_url": metadata.get("original_url", ""),
                "title": metadata.get("original_title", "Unity Documentation"),
                "relevance_score": round(result.get("score", 0.0), 3),
                "content_type": metadata.get("content_type", "general"),
                "has_code_example": metadata.get("has_code_in_chunk", False),
                "source": metadata.get("source", "unity"),
                "chunk_info": {
                    "chunk_index": metadata.get("chunk_index", 0),
                    "total_chunks": metadata.get("total_chunks", 1)
                }
            }
            
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def _get_content_preview(self, metadata: Dict, max_length: int = 500) -> str:
        """Get a preview of the content from metadata"""
        # ENHANCED: Use the new text_content field we're now storing
        content = metadata.get("text_content", "")
        
        if not content:
            # Fallback to text_preview if available
            content = metadata.get("text_preview", "")
        
        if not content:
            # Create preview from available metadata as last resort
            title = metadata.get("original_title", "")
            url = metadata.get("original_url", "")
            content_type = metadata.get("content_type", "")
            
            content = f"Unity documentation: {title}"
            if content_type:
                content += f" ({content_type})"
            if url:
                content += f"\nSource: {url}"
        
        # Truncate if too long
        if len(content) > max_length:
            content = content[:max_length] + "..."
        
        return content
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the retriever is working properly"""
        try:
            # Test Pinecone connection
            pinecone_health = self.pinecone_manager.health_check()
            
            # Test OpenAI connection
            try:
                test_embedding = self._generate_query_embedding("test")
                openai_status = "healthy"
            except Exception as e:
                openai_status = f"error: {str(e)}"
            
            return {
                "status": "healthy" if pinecone_health.get("status") == "healthy" and openai_status == "healthy" else "error",
                "pinecone": pinecone_health,
                "openai": openai_status,
                "index_stats": self.pinecone_manager.get_index_stats()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

# Convenience functions for easy integration
def search_unity_knowledge(query: str, max_results: int = 5, content_type: Optional[str] = None) -> Dict[str, Any]:
    """Simple function to search Unity knowledge"""
    retriever = UnityKnowledgeRetriever()
    return retriever.search_unity_knowledge(query, max_results, content_type)

def get_code_examples(api_name: str, max_results: int = 3) -> Dict[str, Any]:
    """Simple function to get code examples"""
    retriever = UnityKnowledgeRetriever()
    return retriever.get_code_examples(api_name, max_results)

def get_related_concepts(topic: str, max_results: int = 5) -> Dict[str, Any]:
    """Simple function to get related concepts"""
    retriever = UnityKnowledgeRetriever()
    return retriever.get_related_concepts(topic, max_results)

if __name__ == "__main__":
    # Test the retriever
    try:
        retriever = UnityKnowledgeRetriever()
        
        # Health check
        health = retriever.health_check()
        print(f"Health check: {health}")
        
        # Test search
        if health.get("status") == "healthy":
            results = retriever.search_unity_knowledge("How to create a rigidbody?", max_results=3)
            print(f"Search results: {results}")
        
    except Exception as e:
        print(f"Error testing retriever: {e}")
        print("Make sure Pinecone and OpenAI API keys are configured")
