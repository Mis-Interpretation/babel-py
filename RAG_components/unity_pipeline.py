"""
Unity Knowledge Pipeline
Main orchestrator that ties together scraping, parsing, and Pinecone upload
"""

import json
import time
from typing import List, Dict, Any, Optional
import logging
from .generic_scraper import GenericWebScraper
from .content_parser import UniversalContentParser
from .pinecone_manager import PineconeManager
from .knowledge_retriever import UnityKnowledgeRetriever

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnityKnowledgePipeline:
    def __init__(self, pinecone_api_key: Optional[str] = None, openai_api_key: Optional[str] = None,
                 index_name: str = "unity-knowledge-base", config_file: str = "RAG_components/scraping_config.json"):
        """Initialize the complete pipeline"""
        self.scraper = GenericWebScraper(config_file)
        self.parser = UniversalContentParser(config_file, openai_api_key)
        self.pinecone_manager = PineconeManager(pinecone_api_key, index_name=index_name)
        self.retriever = UnityKnowledgeRetriever(pinecone_api_key, openai_api_key, index_name)
        
        self.stats = {
            "last_run": None,
            "total_documents_processed": 0,
            "total_chunks_created": 0,
            "total_vectors_uploaded": 0,
            "errors": []
        }
    
    def scrape_and_index(self, source: str = "unity", max_pages: Optional[int] = None, 
                        namespace: str = "", clear_existing: bool = False) -> Dict[str, Any]:
        """
        Complete pipeline: scrape, parse, and upload to Pinecone
        
        Args:
            source: Source name from config (e.g., "unity")
            max_pages: Maximum pages to scrape (None for all)
            namespace: Pinecone namespace to use
            clear_existing: Whether to clear existing data first
        
        Returns:
            Dictionary with pipeline results and statistics
        """
        start_time = time.time()
        logger.info(f"Starting complete pipeline for source: {source}")
        
        try:
            # Clear existing data if requested
            if clear_existing:
                logger.info(f"Clearing existing data in namespace: {namespace or 'default'}")
                self.pinecone_manager.clear_namespace(namespace)
            
            # Step 1: Scrape content
            logger.info("Step 1: Scraping content...")
            scraped_docs = self.scraper.scrape_source(source, max_pages)
            
            if not scraped_docs:
                return {
                    "status": "error",
                    "message": "No documents scraped",
                    "stats": self.stats
                }
            
            # Step 2: Parse and chunk content
            logger.info("Step 2: Parsing and chunking content...")
            chunk_docs = self.parser.parse_documents(scraped_docs)
            
            if not chunk_docs:
                return {
                    "status": "error",
                    "message": "No chunks created from scraped content",
                    "stats": self.stats
                }
            
            # Step 3: Generate embeddings
            logger.info("Step 3: Generating embeddings...")
            chunk_docs = self.parser.generate_embeddings(chunk_docs)
            
            # Step 4: Upload to Pinecone
            logger.info("Step 4: Uploading to Pinecone...")
            upload_result = self.pinecone_manager.upload_documents(chunk_docs, namespace=namespace)
            
            # Update stats
            end_time = time.time()
            self.stats.update({
                "last_run": end_time,
                "total_documents_processed": len(scraped_docs),
                "total_chunks_created": len(chunk_docs),
                "total_vectors_uploaded": upload_result.get("uploaded", 0),
                "processing_time_seconds": round(end_time - start_time, 2)
            })
            
            result = {
                "status": "success",
                "source": source,
                "documents_scraped": len(scraped_docs),
                "chunks_created": len(chunk_docs),
                "vectors_uploaded": upload_result.get("uploaded", 0),
                "upload_errors": upload_result.get("errors", 0),
                "processing_time": round(end_time - start_time, 2),
                "namespace": namespace,
                "stats": self.stats
            }
            
            logger.info(f"Pipeline completed successfully: {result}")
            return result
            
        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            logger.error(error_msg)
            self.stats["errors"].append({
                "timestamp": time.time(),
                "error": error_msg
            })
            
            return {
                "status": "error",
                "message": error_msg,
                "stats": self.stats
            }
    
    def update_knowledge_base(self, source: str = "unity", max_pages: Optional[int] = None,
                             namespace: str = "") -> Dict[str, Any]:
        """
        Update existing knowledge base with new/changed content
        
        Args:
            source: Source name from config
            max_pages: Maximum pages to scrape
            namespace: Pinecone namespace to use
        
        Returns:
            Dictionary with update results
        """
        logger.info(f"Updating knowledge base for source: {source}")
        
        try:
            # For now, this is the same as scrape_and_index since Pinecone upsert handles updates
            # In the future, we could add change detection here
            return self.scrape_and_index(source, max_pages, namespace, clear_existing=False)
            
        except Exception as e:
            error_msg = f"Update failed: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }
    
    def add_new_source(self, source_config: Dict[str, Any], source_name: str) -> Dict[str, Any]:
        """
        Add a new documentation source to the configuration
        
        Args:
            source_config: Configuration for the new source
            source_name: Name for the new source
        
        Returns:
            Dictionary with operation result
        """
        try:
            # Load current config
            config_file = "RAG_components/scraping_config.json"
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Add new source
            config[source_name] = source_config
            
            # Save updated config
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            # Reload scraper config
            self.scraper = GenericWebScraper(config_file)
            
            logger.info(f"Added new source: {source_name}")
            return {
                "status": "success",
                "message": f"Source '{source_name}' added successfully"
            }
            
        except Exception as e:
            error_msg = f"Failed to add source: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of all pipeline components
        
        Returns:
            Dictionary with health status of all components
        """
        try:
            # Check Pinecone
            pinecone_health = self.pinecone_manager.health_check()
            
            # Check retriever (includes OpenAI)
            retriever_health = self.retriever.health_check()
            
            # Overall status
            overall_status = "healthy" if (
                pinecone_health.get("status") == "healthy" and 
                retriever_health.get("status") == "healthy"
            ) else "error"
            
            return {
                "status": overall_status,
                "components": {
                    "pinecone": pinecone_health,
                    "retriever": retriever_health,
                    "scraper": "healthy",  # Scraper doesn't need external services
                    "parser": "healthy"    # Parser health depends on OpenAI which is checked in retriever
                },
                "pipeline_stats": self.stats
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics and index information"""
        try:
            index_stats = self.pinecone_manager.get_index_stats()
            
            return {
                "pipeline_stats": self.stats,
                "index_stats": index_stats,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def search_knowledge(self, query: str, max_results: int = 5, 
                        content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Search the knowledge base (convenience method)
        
        Args:
            query: Search query
            max_results: Maximum results to return
            content_type: Filter by content type
        
        Returns:
            Search results
        """
        return self.retriever.search_unity_knowledge(query, max_results, content_type)
    
    def get_code_examples(self, api_name: str, max_results: int = 3) -> Dict[str, Any]:
        """
        Get code examples (convenience method)
        
        Args:
            api_name: Unity API name
            max_results: Maximum examples to return
        
        Returns:
            Code examples
        """
        return self.retriever.get_code_examples(api_name, max_results)

# Convenience functions for easy use
def scrape_and_index_unity(max_pages: Optional[int] = None, clear_existing: bool = False) -> Dict[str, Any]:
    """
    One-shot function to scrape Unity docs and upload to Pinecone
    
    Args:
        max_pages: Maximum pages to scrape (None for all)
        clear_existing: Whether to clear existing data first
    
    Returns:
        Pipeline results
    """
    pipeline = UnityKnowledgePipeline()
    return pipeline.scrape_and_index("unity", max_pages, clear_existing=clear_existing)

def search_unity_knowledge(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Simple function to search Unity knowledge base
    
    Args:
        query: Search query
        max_results: Maximum results to return
    
    Returns:
        Search results
    """
    pipeline = UnityKnowledgePipeline()
    return pipeline.search_knowledge(query, max_results)

def get_unity_code_examples(api_name: str, max_results: int = 3) -> Dict[str, Any]:
    """
    Simple function to get Unity code examples
    
    Args:
        api_name: Unity API name
        max_results: Maximum examples to return
    
    Returns:
        Code examples
    """
    pipeline = UnityKnowledgePipeline()
    return pipeline.get_code_examples(api_name, max_results)

if __name__ == "__main__":
    # Test the pipeline
    try:
        pipeline = UnityKnowledgePipeline()
        
        # Health check
        health = pipeline.health_check()
        print(f"Pipeline health: {health}")
        
        # Test with a small scrape
        if health.get("status") == "healthy":
            print("Testing pipeline with small scrape...")
            result = pipeline.scrape_and_index("unity", max_pages=5)
            print(f"Pipeline result: {result}")
            
            # Test search
            if result.get("status") == "success":
                search_result = pipeline.search_knowledge("rigidbody physics")
                print(f"Search test: {search_result}")
        
    except Exception as e:
        print(f"Error testing pipeline: {e}")
        print("Make sure API keys are configured in environment variables:")
        print("- PINECONE_API_KEY")
        print("- OPENAI_API_KEY")
