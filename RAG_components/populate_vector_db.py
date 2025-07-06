"""
Simple Vector DB Population Script
Standalone function to scrape Unity docs and populate Pinecone without OpenAI dependency
"""

import os
import json
from typing import Optional, Dict, Any
from .generic_scraper import GenericWebScraper
from .content_parser import UniversalContentParser
from .pinecone_manager import PineconeManager

def populate_unity_vector_db(
    pinecone_api_key: str,
    max_pages: Optional[int] = 50,
    index_name: str = "unity-knowledge-base",
    clear_existing: bool = False,
    namespace: str = ""
) -> Dict[str, Any]:
    """
    Simple function to populate Pinecone vector database with Unity documentation
    
    Args:
        pinecone_api_key: Your Pinecone API key
        max_pages: Maximum pages to scrape (None for all, 50 recommended for testing)
        index_name: Name of the Pinecone index to create/use
        clear_existing: Whether to clear existing data first
        namespace: Pinecone namespace (optional, for organizing data)
    
    Returns:
        Dictionary with results and statistics
    """
    
    print("🚀 Starting Unity documentation scraping and indexing...")
    
    try:
        # Step 1: Initialize components
        print("📋 Initializing scraper and database components...")
        scraper = GenericWebScraper("scraping_config.json")
        parser = UniversalContentParser("scraping_config.json", openai_api_key=None)  # No OpenAI needed
        pinecone_manager = PineconeManager(pinecone_api_key, index_name=index_name)
        
        # Step 2: Clear existing data if requested
        if clear_existing:
            print(f"🧹 Clearing existing data in namespace: {namespace or 'default'}")
            pinecone_manager.clear_namespace(namespace)
        
        # Step 3: Scrape Unity documentation
        print(f"🕷️ Scraping Unity documentation (max {max_pages or 'unlimited'} pages)...")
        scraped_docs = scraper.scrape_source("unity", max_pages)
        
        if not scraped_docs:
            return {
                "status": "error",
                "message": "No documents were scraped. Check your internet connection and Unity docs availability."
            }
        
        print(f"✅ Successfully scraped {len(scraped_docs)} documents")
        
        # Step 4: Parse and chunk content (without embeddings)
        print("📝 Parsing and chunking content...")
        chunk_docs = parser.parse_documents(scraped_docs)
        
        if not chunk_docs:
            return {
                "status": "error",
                "message": "No chunks created from scraped content"
            }
        
        print(f"✅ Created {len(chunk_docs)} content chunks")
        
        # Step 5: Generate simple embeddings using a basic method
        print("🔢 Generating simple embeddings...")
        chunk_docs_with_embeddings = generate_simple_embeddings(chunk_docs)
        
        # Step 6: Upload to Pinecone
        print("☁️ Uploading to Pinecone vector database...")
        upload_result = pinecone_manager.upload_documents(chunk_docs_with_embeddings, namespace=namespace)
        
        # Final results
        result = {
            "status": "success",
            "documents_scraped": len(scraped_docs),
            "chunks_created": len(chunk_docs),
            "vectors_uploaded": upload_result.get("uploaded", 0),
            "upload_errors": upload_result.get("errors", 0),
            "index_name": index_name,
            "namespace": namespace or "default"
        }
        
        print("🎉 Vector database population completed!")
        print(f"📊 Results: {result['documents_scraped']} docs → {result['chunks_created']} chunks → {result['vectors_uploaded']} vectors")
        
        return result
        
    except Exception as e:
        error_msg = f"Population failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "status": "error",
            "message": error_msg
        }

def generate_simple_embeddings(chunk_docs):
    """
    Generate simple embeddings without OpenAI - ALWAYS 1536 dimensions
    Uses TF-IDF with guaranteed dimension padding/truncation
    """
    print("   Using simple TF-IDF embeddings (no OpenAI required)...")
    
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD
        import numpy as np
        from sklearn.preprocessing import normalize
        
        # Extract text from chunks
        texts = [doc["text"] for doc in chunk_docs]
        target_dimensions = 1536
        
        print(f"   Processing {len(texts)} text chunks...")
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        print(f"   TF-IDF matrix shape: {tfidf_matrix.shape}")
        n_features = tfidf_matrix.shape[1]
        n_docs = tfidf_matrix.shape[0]
        
        # ALWAYS ensure we get exactly 1536 dimensions
        if n_features >= target_dimensions:
            print(f"   Using SVD to reduce {n_features} features to {target_dimensions} dimensions")
            # Use SVD to reduce to exactly 1536 dimensions
            svd = TruncatedSVD(n_components=target_dimensions, random_state=42)
            embeddings = svd.fit_transform(tfidf_matrix)
            print(f"   SVD completed. Embedding shape: {embeddings.shape}")
        else:
            print(f"   Only {n_features} features available, padding to {target_dimensions} dimensions")
            
            # Use available features with SVD if possible
            if n_features > 1 and n_docs > 1:
                # Use min to avoid issues with small matrices
                n_components = min(n_features - 1, n_docs - 1, target_dimensions)
                svd = TruncatedSVD(n_components=n_components, random_state=42)
                reduced_embeddings = svd.fit_transform(tfidf_matrix)
                print(f"   SVD reduced to {reduced_embeddings.shape[1]} dimensions")
            else:
                # Very small matrix, use raw TF-IDF
                reduced_embeddings = tfidf_matrix.toarray()
                print(f"   Using raw TF-IDF: {reduced_embeddings.shape}")
            
            # Create final embeddings array with exact target dimensions
            embeddings = np.zeros((n_docs, target_dimensions), dtype=np.float32)
            
            # Copy the reduced embeddings to the beginning of the array
            copy_dims = min(reduced_embeddings.shape[1], target_dimensions)
            embeddings[:, :copy_dims] = reduced_embeddings[:, :copy_dims]
            
            print(f"   Padded to final shape: {embeddings.shape}")
        
        # Normalize embeddings for better cosine similarity
        embeddings = normalize(embeddings, norm='l2')
        
        # Verify dimensions before adding to documents
        assert embeddings.shape[1] == target_dimensions, f"Wrong dimensions: {embeddings.shape[1]} != {target_dimensions}"
        assert embeddings.shape[0] == len(chunk_docs), f"Wrong number of embeddings: {embeddings.shape[0]} != {len(chunk_docs)}"
        
        # Add embeddings to chunk documents
        for i, doc in enumerate(chunk_docs):
            embedding_vector = embeddings[i].tolist()
            assert len(embedding_vector) == target_dimensions, f"Embedding {i} has wrong dimensions: {len(embedding_vector)}"
            doc["embedding"] = embedding_vector
        
        print(f"   ✅ Generated {len(embeddings)} TF-IDF embeddings with {len(embeddings[0])} dimensions")
        return chunk_docs
        
    except ImportError as e:
        print(f"   ⚠️ scikit-learn not available ({e}), using random embeddings...")
        return _generate_fallback_embeddings(chunk_docs)
    
    except Exception as e:
        print(f"   ❌ Error generating TF-IDF embeddings: {e}")
        print("   🔄 Falling back to random embeddings...")
        return _generate_fallback_embeddings(chunk_docs)

def _generate_fallback_embeddings(chunk_docs):
    """Generate normalized random 1536-dimensional embeddings as fallback"""
    import random
    import math
    
    target_dimensions = 1536
    
    for doc in chunk_docs:
        # Generate normalized random vector
        vector = [random.gauss(0, 1) for _ in range(target_dimensions)]
        
        # Normalize the vector
        magnitude = math.sqrt(sum(x*x for x in vector))
        if magnitude > 0:
            vector = [x/magnitude for x in vector]
        else:
            # Handle edge case of zero vector
            vector = [1.0/math.sqrt(target_dimensions)] * target_dimensions
        
        assert len(vector) == target_dimensions, f"Fallback embedding has wrong dimensions: {len(vector)}"
        doc["embedding"] = vector
    
    print(f"   ✅ Generated {len(chunk_docs)} fallback random embeddings with {target_dimensions} dimensions")
    return chunk_docs

def quick_populate():
    """
    Quick function that uses environment variables
    """
    pinecone_key = os.getenv("PINECONE_API_KEY")
    
    if not pinecone_key:
        print("❌ PINECONE_API_KEY environment variable not set!")
        print("Set it with: export PINECONE_API_KEY='your-api-key'")
        return
    
    return populate_unity_vector_db(
        pinecone_api_key=pinecone_key,
        max_pages=20,  # Small test
        clear_existing=True
    )

def populate_unity_vector_db_auto(
    max_pages: Optional[int] = 50,
    clear_existing: bool = False,
    namespace: str = ""
) -> Dict[str, Any]:
    """
    Automatic function that uses your existing config system
    
    Args:
        max_pages: Maximum pages to scrape (None for all, 50 recommended for testing)
        clear_existing: Whether to clear existing data first
        namespace: Pinecone namespace (optional, for organizing data)
    
    Returns:
        Dictionary with results and statistics
    """
    pinecone_key = None
    
    # Try multiple ways to get the Pinecone API key
    try:
        # Method 1: Try to import config module from current directory
        import sys
        import os
        
        # Add current directory to Python path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Try importing config
        from config import get_pinecone_api_key
        pinecone_key = get_pinecone_api_key()
        print("🔧 Using your existing config system...")
        
    except ImportError:
        # Method 2: Try direct environment variable access
        print("⚠️ Config module not found, trying environment variables...")
        pinecone_key = os.getenv("PINECONE_API_KEY")
        
        if pinecone_key:
            print("🔧 Using environment variable PINECONE_API_KEY...")
        
    except Exception as e:
        print(f"⚠️ Error with config system: {e}")
        pinecone_key = os.getenv("PINECONE_API_KEY")
    
    # Check if we got a valid API key
    if not pinecone_key or pinecone_key == "your-pinecone-api-key-here":
        return {
            "status": "error",
            "message": "Pinecone API key not configured. Please:\n" +
                      "1. Set PINECONE_API_KEY environment variable, OR\n" +
                      "2. Add PINECONE_API_KEY=your-key to your .env file, OR\n" +
                      "3. Run from the directory containing config.py"
        }
    
    # Use the API key to populate the database
    return populate_unity_vector_db(
        pinecone_api_key=pinecone_key,
        max_pages=max_pages,
        clear_existing=clear_existing,
        namespace=namespace
    )

if __name__ == "__main__":
    print("Unity Vector Database Population Tool")
    print("=" * 50)
    
    # Check for API key
    if not os.getenv("PINECONE_API_KEY"):
        print("Please set your Pinecone API key:")
        print("export PINECONE_API_KEY='your-pinecone-api-key'")
        print("\nOr call the function directly:")
        print("populate_unity_vector_db('your-pinecone-api-key')")
    else:
        # Run with environment variable
        result = quick_populate()
        print(f"\nFinal result: {result}")
