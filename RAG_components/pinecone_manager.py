"""
Pinecone Vector Database Manager
Handles all Pinecone operations for the knowledge base
"""

import os
import time
import json
from typing import List, Dict, Any, Optional, Tuple
import logging
from pinecone import Pinecone, ServerlessSpec
import hashlib

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PineconeManager:
    def __init__(self, api_key: Optional[str] = None, environment: str = "us-east-1", index_name: str = "unity-knowledge-base"):
        """Initialize Pinecone manager"""
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.environment = environment
        self.index_name = index_name
        
        if not self.api_key:
            raise ValueError("Pinecone API key not provided. Set PINECONE_API_KEY environment variable or pass api_key parameter.")
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.api_key)
        self.index = None
        
        # Connect to or create index
        self._setup_index()
    
    def _setup_index(self):
        """Setup or create Pinecone index"""
        try:
            # Check if index exists
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                self._create_index()
            else:
                logger.info(f"Connecting to existing Pinecone index: {self.index_name}")
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            
            # Verify connection
            stats = self.index.describe_index_stats()
            logger.info(f"Connected to index. Total vectors: {stats.total_vector_count}")
            
        except Exception as e:
            logger.error(f"Error setting up Pinecone index: {e}")
            raise
    
    def _create_index(self):
        """Create a new Pinecone index"""
        try:
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,  # OpenAI text-embedding-3-small dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=self.environment
                )
            )
            
            # Wait for index to be ready
            logger.info("Waiting for index to be ready...")
            while not self.pc.describe_index(self.index_name).status['ready']:
                time.sleep(1)
            
            logger.info(f"Index {self.index_name} created successfully")
            
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            raise
    
    def upload_documents(self, chunk_docs: List[Dict], batch_size: int = 100, namespace: str = "") -> Dict[str, Any]:
        """Upload chunk documents to Pinecone"""
        if not self.index:
            raise ValueError("Pinecone index not initialized")
        
        if not chunk_docs:
            logger.warning("No documents to upload")
            return {"uploaded": 0, "errors": 0}
        
        logger.info(f"Uploading {len(chunk_docs)} documents to Pinecone...")
        
        uploaded_count = 0
        error_count = 0
        
        # Process in batches
        for i in range(0, len(chunk_docs), batch_size):
            batch = chunk_docs[i:i + batch_size]
            
            try:
                vectors = self._prepare_vectors(batch)
                
                if vectors:
                    self.index.upsert(vectors=vectors, namespace=namespace)
                    uploaded_count += len(vectors)
                    logger.info(f"Uploaded batch {i//batch_size + 1}/{(len(chunk_docs) + batch_size - 1)//batch_size}")
                
                # Small delay to avoid rate limits
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error uploading batch {i//batch_size + 1}: {e}")
                error_count += len(batch)
        
        result = {
            "uploaded": uploaded_count,
            "errors": error_count,
            "total": len(chunk_docs)
        }
        
        logger.info(f"Upload complete: {uploaded_count} uploaded, {error_count} errors")
        return result
    
    def _prepare_vectors(self, chunk_docs: List[Dict]) -> List[Dict]:
        """Prepare vectors for Pinecone upload"""
        vectors = []
        
        for doc in chunk_docs:
            # Skip documents without embeddings
            if "embedding" not in doc:
                logger.warning(f"Skipping document without embedding: {doc.get('id', 'unknown')}")
                continue
            
            # Prepare metadata (Pinecone has metadata size limits)
            metadata = self._prepare_metadata(doc.get("metadata", {}))
            
            # CRITICAL FIX: Add text content to metadata
            text_content = doc.get("text", "")
            if text_content:
                # Store full text content (truncated if needed for Pinecone limits)
                metadata["text_content"] = text_content[:3000] if len(text_content) > 3000 else text_content
                metadata["full_text_length"] = len(text_content)
                
                # Add a preview for quick display
                preview_length = 200
                metadata["text_preview"] = (text_content[:preview_length] + "...") if len(text_content) > preview_length else text_content
                
                # Add text hash for verification
                import hashlib
                metadata["text_hash"] = hashlib.md5(text_content.encode('utf-8')).hexdigest()
            else:
                logger.warning(f"Document {doc.get('id', 'unknown')} has no text content")
                metadata["text_content"] = ""
                metadata["text_preview"] = ""
                metadata["full_text_length"] = 0
            
            vector = {
                "id": doc["id"],
                "values": doc["embedding"],
                "metadata": metadata
            }
            
            vectors.append(vector)
        
        return vectors
    
    def _prepare_metadata(self, metadata: Dict) -> Dict:
        """Prepare metadata for Pinecone (handle size limits and data types)"""
        # Pinecone metadata limitations:
        # - Max 40KB per vector
        # - Only supports: strings, numbers, booleans, lists of strings
        
        prepared = {}
        
        for key, value in metadata.items():
            # Convert all values to appropriate types
            if isinstance(value, (str, int, float, bool)):
                # Truncate long strings
                if isinstance(value, str) and len(value) > 1000:
                    prepared[key] = value[:1000] + "..."
                else:
                    prepared[key] = value
            elif isinstance(value, list):
                # Convert list elements to strings and limit size
                str_list = [str(item) for item in value[:10]]  # Limit to 10 items
                prepared[key] = str_list
            else:
                # Convert other types to string
                str_value = str(value)
                if len(str_value) > 1000:
                    prepared[key] = str_value[:1000] + "..."
                else:
                    prepared[key] = str_value
        
        return prepared
    
    def search_similar(self, query_embedding: List[float], top_k: int = 5, 
                      filter_dict: Optional[Dict] = None, namespace: str = "") -> List[Dict]:
        """Search for similar vectors"""
        if not self.index:
            raise ValueError("Pinecone index not initialized")
        
        try:
            response = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=filter_dict,
                namespace=namespace,
                include_metadata=True,
                include_values=False
            )
            
            results = []
            for match in response.matches:
                result = {
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching Pinecone: {e}")
            raise
    
    def search_by_metadata(self, filter_dict: Dict, top_k: int = 100, namespace: str = "") -> List[Dict]:
        """Search vectors by metadata filters only"""
        if not self.index:
            raise ValueError("Pinecone index not initialized")
        
        try:
            # Use a dummy vector for metadata-only search
            dummy_vector = [0.0] * 1536
            
            response = self.index.query(
                vector=dummy_vector,
                top_k=top_k,
                filter=filter_dict,
                namespace=namespace,
                include_metadata=True,
                include_values=False
            )
            
            results = []
            for match in response.matches:
                result = {
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching by metadata: {e}")
            raise
    
    def delete_documents(self, doc_ids: List[str], namespace: str = "") -> Dict[str, Any]:
        """Delete documents by IDs"""
        if not self.index:
            raise ValueError("Pinecone index not initialized")
        
        try:
            self.index.delete(ids=doc_ids, namespace=namespace)
            logger.info(f"Deleted {len(doc_ids)} documents")
            
            return {"deleted": len(doc_ids), "errors": 0}
            
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return {"deleted": 0, "errors": len(doc_ids)}
    
    def delete_by_metadata(self, filter_dict: Dict, namespace: str = "") -> Dict[str, Any]:
        """Delete documents by metadata filter"""
        if not self.index:
            raise ValueError("Pinecone index not initialized")
        
        try:
            self.index.delete(filter=filter_dict, namespace=namespace)
            logger.info(f"Deleted documents matching filter: {filter_dict}")
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"Error deleting by metadata: {e}")
            return {"status": "error", "message": str(e)}
    
    def update_documents(self, chunk_docs: List[Dict], namespace: str = "") -> Dict[str, Any]:
        """Update existing documents (same as upload - upsert operation)"""
        return self.upload_documents(chunk_docs, namespace=namespace)
    
    def get_index_stats(self, namespace: str = "") -> Dict[str, Any]:
        """Get index statistics"""
        if not self.index:
            raise ValueError("Pinecone index not initialized")
        
        try:
            stats = self.index.describe_index_stats()
            
            result = {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": {}
            }
            
            if hasattr(stats, 'namespaces') and stats.namespaces:
                for ns_name, ns_stats in stats.namespaces.items():
                    result["namespaces"][ns_name] = {
                        "vector_count": ns_stats.vector_count
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            raise
    
    def clear_namespace(self, namespace: str = "") -> Dict[str, Any]:
        """Clear all vectors in a namespace"""
        if not self.index:
            raise ValueError("Pinecone index not initialized")
        
        try:
            self.index.delete(delete_all=True, namespace=namespace)
            logger.info(f"Cleared namespace: {namespace or 'default'}")
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"Error clearing namespace: {e}")
            return {"status": "error", "message": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check if Pinecone connection is healthy"""
        try:
            if not self.index:
                return {"status": "error", "message": "Index not initialized"}
            
            stats = self.index.describe_index_stats()
            
            return {
                "status": "healthy",
                "index_name": self.index_name,
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

# Convenience functions for common operations
def create_pinecone_manager(api_key: Optional[str] = None, index_name: str = "unity-knowledge-base") -> PineconeManager:
    """Create a Pinecone manager instance"""
    return PineconeManager(api_key=api_key, index_name=index_name)

def upload_to_pinecone(chunk_docs: List[Dict], api_key: Optional[str] = None, 
                      index_name: str = "unity-knowledge-base", namespace: str = "") -> Dict[str, Any]:
    """Convenience function to upload documents to Pinecone"""
    manager = create_pinecone_manager(api_key, index_name)
    return manager.upload_documents(chunk_docs, namespace=namespace)

if __name__ == "__main__":
    # Test the Pinecone manager
    try:
        manager = PineconeManager()
        health = manager.health_check()
        print(f"Pinecone health check: {health}")
        
        stats = manager.get_index_stats()
        print(f"Index stats: {stats}")
        
    except Exception as e:
        print(f"Error testing Pinecone manager: {e}")
        print("Make sure to set PINECONE_API_KEY environment variable")
