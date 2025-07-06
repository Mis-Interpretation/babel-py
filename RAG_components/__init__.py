"""
RAG Components Package
Modular components for building a scraper-to-Pinecone knowledge base pipeline
"""

# Import main classes for easy access
from .generic_scraper import GenericWebScraper
from .content_parser import UniversalContentParser
from .pinecone_manager import PineconeManager
from .knowledge_retriever import UnityKnowledgeRetriever
from .unity_pipeline import UnityKnowledgePipeline

# Import convenience functions
from .unity_pipeline import (
    scrape_and_index_unity,
    search_unity_knowledge,
    get_unity_code_examples
)

from .knowledge_retriever import (
    search_unity_knowledge as search_knowledge,
    get_code_examples,
    get_related_concepts
)

__version__ = "1.0.0"
__author__ = "Unity Copilot Team"

# Package-level convenience functions
def quick_setup():
    """Quick setup guide for the RAG components"""
    setup_guide = """
    Unity Knowledge Base RAG Components Setup:
    
    1. Install dependencies:
       pip install -r requirements.txt
    
    2. Set environment variables:
       - PINECONE_API_KEY: Your Pinecone API key
       - OPENAI_API_KEY: Your OpenAI API key
    
    3. Basic usage:
       from RAG_components import scrape_and_index_unity, search_unity_knowledge
       
       # Populate knowledge base
       result = scrape_and_index_unity(max_pages=10)
       
       # Search knowledge base
       results = search_unity_knowledge("How to create a rigidbody?")
    
    4. Advanced usage:
       from RAG_components import UnityKnowledgePipeline
       
       pipeline = UnityKnowledgePipeline()
       pipeline.scrape_and_index("unity", max_pages=50)
       results = pipeline.search_knowledge("physics simulation")
    """
    print(setup_guide)

def health_check():
    """Check if all components are properly configured"""
    try:
        pipeline = UnityKnowledgePipeline()
        return pipeline.health_check()
    except Exception as e:
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}",
            "suggestion": "Run RAG_components.quick_setup() for setup instructions"
        }

# Export all main components
__all__ = [
    # Main classes
    "GenericWebScraper",
    "UniversalContentParser", 
    "PineconeManager",
    "UnityKnowledgeRetriever",
    "UnityKnowledgePipeline",
    
    # Convenience functions
    "scrape_and_index_unity",
    "search_unity_knowledge",
    "get_unity_code_examples",
    "search_knowledge",
    "get_code_examples", 
    "get_related_concepts",
    
    # Utility functions
    "quick_setup",
    "health_check"
]
