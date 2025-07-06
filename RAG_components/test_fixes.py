#!/usr/bin/env python3
"""
Quick test to verify all fixes are working
"""

def test_all_fixes():
    print("🧪 TESTING ALL FIXES")
    print("=" * 40)
    
    # Test 1: Embedding dimensions
    print("\n1️⃣ Testing embedding dimensions...")
    try:
        from .populate_vector_db import generate_simple_embeddings
        
        test_docs = [
            {'text': 'Unity Rigidbody test'},
            {'text': 'Transform component test'}
        ]
        
        result = generate_simple_embeddings(test_docs)
        
        for i, doc in enumerate(result):
            if 'embedding' in doc:
                dim = len(doc['embedding'])
                if dim == 1536:
                    print(f"   ✅ Embedding {i+1}: {dim} dimensions (CORRECT)")
                else:
                    print(f"   ❌ Embedding {i+1}: {dim} dimensions (WRONG)")
                    return False
            else:
                print(f"   ❌ Embedding {i+1}: No embedding found")
                return False
        
        print("   🎉 Embedding dimension fix: WORKING")
        
    except Exception as e:
        print(f"   ❌ Embedding test failed: {e}")
        return False
    
    # Test 2: Pinecone connection
    print("\n2️⃣ Testing Pinecone connection...")
    try:
        from .pinecone_manager import PineconeManager
        
        # Get API key
        import os
        pinecone_key = None
        try:
            from config import get_pinecone_api_key
            pinecone_key = get_pinecone_api_key()
        except:
            pinecone_key = os.getenv("PINECONE_API_KEY")
        
        if not pinecone_key:
            print("   ❌ Pinecone API key not found")
            return False
        
        manager = PineconeManager(api_key=pinecone_key)
        health = manager.health_check()
        
        if health.get("status") == "healthy":
            print("   ✅ Pinecone connection: WORKING")
            stats = manager.get_index_stats()
            print(f"   📊 Current vectors: {stats.get('total_vector_count', 0)}")
        else:
            print(f"   ❌ Pinecone connection failed: {health}")
            return False
            
    except Exception as e:
        print(f"   ❌ Pinecone test failed: {e}")
        return False
    
    # Test 3: Text content storage
    print("\n3️⃣ Testing text content storage...")
    try:
        # Test the _prepare_vectors method
        test_chunk = {
            'id': 'test_123',
            'text': 'This is test content for Unity Rigidbody component',
            'embedding': [0.1] * 1536,
            'metadata': {
                'title': 'Test Document',
                'url': 'https://test.com'
            }
        }
        
        vectors = manager._prepare_vectors([test_chunk])
        
        if vectors and len(vectors) > 0:
            metadata = vectors[0]['metadata']
            
            has_text_content = bool(metadata.get('text_content', ''))
            has_text_preview = bool(metadata.get('text_preview', ''))
            text_length = metadata.get('full_text_length', 0)
            
            print(f"   ✅ Text content stored: {has_text_content}")
            print(f"   ✅ Text preview stored: {has_text_preview}")
            print(f"   ✅ Text length tracked: {text_length}")
            
            if has_text_content and text_length > 0:
                print("   🎉 Text content storage: WORKING")
            else:
                print("   ❌ Text content storage: NOT WORKING")
                return False
        else:
            print("   ❌ Vector preparation failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Text content test failed: {e}")
        return False
    
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ Your fixes are working correctly")
    return True

if __name__ == "__main__":
    success = test_all_fixes()
    
    if success:
        print("\n🚀 READY TO REPOPULATE DATABASE")
        print("Run: python fix_and_repopulate_database.py")
        print("Or: python simple_usage_example.py")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Check the errors above before proceeding")
