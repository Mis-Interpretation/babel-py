"""
Test to verify the dimension fix works across all components
"""

def test_all_embedding_methods():
    print("🧪 Testing All Embedding Generation Methods")
    print("=" * 60)
    
    # Test data
    test_docs = [
        {
            "title": "Unity Rigidbody",
            "text": "The Rigidbody component allows a GameObject to be affected by physics forces and gravity in Unity engine",
            "content_type": "api_reference",
            "metadata": {"source": "unity", "url": "test1"}
        },
        {
            "title": "Unity Transform", 
            "text": "Transform component defines the position, rotation, and scale of a GameObject in 3D space within Unity",
            "content_type": "api_reference",
            "metadata": {"source": "unity", "url": "test2"}
        }
    ]
    
    # Test 1: populate_vector_db embedding generation
    print("\n1️⃣ Testing populate_vector_db.generate_simple_embeddings...")
    try:
        from populate_vector_db import generate_simple_embeddings
        
        # Create chunks first
        from RAG_components.content_parser import UniversalContentParser
        parser = UniversalContentParser("RAG_components/scraping_config.json", openai_api_key=None)
        chunks = parser.parse_documents(test_docs)
        
        # Generate embeddings
        result = generate_simple_embeddings(chunks)
        
        for i, doc in enumerate(result):
            if 'embedding' in doc:
                dim = len(doc['embedding'])
                print(f"   ✅ Chunk {i}: {dim} dimensions")
                if dim != 1536:
                    print(f"   ❌ ERROR: Expected 1536, got {dim}")
                    return False
            else:
                print(f"   ❌ Chunk {i}: No embedding found")
                return False
        
        print("   ✅ populate_vector_db embeddings: PASSED")
        
    except Exception as e:
        print(f"   ❌ populate_vector_db embeddings: FAILED - {e}")
        return False
    
    # Test 2: Content parser embedding generation (should skip since no OpenAI key)
    print("\n2️⃣ Testing content_parser.generate_embeddings...")
    try:
        from RAG_components.content_parser import UniversalContentParser
        
        parser = UniversalContentParser("RAG_components/scraping_config.json", openai_api_key=None)
        chunks = parser.parse_documents(test_docs)
        
        # This should skip embedding generation since no OpenAI key
        chunks_with_embeddings = parser.generate_embeddings(chunks)
        
        embeddings_found = 0
        for i, doc in enumerate(chunks_with_embeddings):
            if 'embedding' in doc:
                embeddings_found += 1
                dim = len(doc['embedding'])
                print(f"   ⚠️ Chunk {i}: {dim} dimensions (unexpected - should skip without OpenAI key)")
                if dim != 1536:
                    print(f"   ❌ ERROR: Wrong dimensions {dim}")
                    return False
        
        if embeddings_found == 0:
            print("   ✅ content_parser correctly skipped embedding generation (no OpenAI key)")
        else:
            print(f"   ⚠️ content_parser generated {embeddings_found} embeddings despite no OpenAI key")
        
    except Exception as e:
        print(f"   ❌ content_parser embeddings: FAILED - {e}")
        return False
    
    # Test 3: Full pipeline
    print("\n3️⃣ Testing full pipeline...")
    try:
        from populate_vector_db import populate_unity_vector_db_auto
        
        # Run with minimal pages to test
        result = populate_unity_vector_db_auto(max_pages=1, clear_existing=False)
        
        if result['status'] == 'success':
            print("   ✅ Full pipeline: SUCCESS!")
            print(f"   📊 Scraped: {result.get('documents_scraped', 0)} docs")
            print(f"   📊 Chunks: {result.get('chunks_created', 0)} chunks") 
            print(f"   📊 Uploaded: {result.get('vectors_uploaded', 0)} vectors")
            print(f"   📊 Errors: {result.get('upload_errors', 0)} errors")
            
            if result.get('upload_errors', 0) == 0:
                print("   🎉 NO UPLOAD ERRORS - DIMENSION ISSUE FIXED!")
                return True
            else:
                print("   ⚠️ Still have upload errors")
                return False
                
        else:
            print(f"   ❌ Full pipeline failed: {result.get('message', 'Unknown error')}")
            if "dimension" in result.get('message', '').lower():
                print("   🚨 DIMENSION ERROR STILL EXISTS!")
            return False
            
    except Exception as e:
        print(f"   ❌ Full pipeline: FAILED - {e}")
        return False

if __name__ == "__main__":
    success = test_all_embedding_methods()
    
    if success:
        print("\n🎉 ALL TESTS PASSED! Your dimension issue is fixed!")
    else:
        print("\n❌ Some tests failed. The dimension issue may still exist.")
