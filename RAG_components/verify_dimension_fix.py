#!/usr/bin/env python3
"""
Verification script to test the dimension fix
Run this to verify that embeddings are now generating 1536 dimensions
"""

def test_embedding_dimensions():
    print("🧪 TESTING EMBEDDING DIMENSION FIX")
    print("=" * 50)
    
    try:
        # Import the fixed function
        from populate_vector_db import generate_simple_embeddings
        
        # Create test data
        test_docs = [
            {'text': 'Unity Rigidbody component allows GameObjects to be affected by physics forces'},
            {'text': 'Transform component defines position, rotation and scale of GameObject'},
            {'text': 'Collider components define shape for physical collisions in Unity engine'},
            {'text': 'MonoBehaviour is the base class for Unity scripts and components'}
        ]
        
        print(f"📝 Testing with {len(test_docs)} sample documents...")
        print()
        
        # Generate embeddings
        result = generate_simple_embeddings(test_docs)
        
        print()
        print("🔍 VERIFICATION RESULTS:")
        print("-" * 30)
        
        all_correct = True
        for i, doc in enumerate(result):
            if 'embedding' in doc:
                dim = len(doc['embedding'])
                if dim == 1536:
                    print(f"✅ Document {i+1}: {dim} dimensions (CORRECT)")
                else:
                    print(f"❌ Document {i+1}: {dim} dimensions (WRONG - should be 1536)")
                    all_correct = False
            else:
                print(f"❌ Document {i+1}: No embedding found")
                all_correct = False
        
        print()
        if all_correct:
            print("🎉 SUCCESS! All embeddings have correct 1536 dimensions")
            print("✅ The dimension fix is working correctly")
            print("🚀 You can now run simple_usage_example.py without dimension errors")
            return True
        else:
            print("❌ FAILED! Some embeddings have wrong dimensions")
            print("🔧 The fix needs more work")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("🔧 Make sure you're in the correct directory with populate_vector_db.py")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("🔧 Check the error details above")
        return False

if __name__ == "__main__":
    success = test_embedding_dimensions()
    
    print()
    print("=" * 50)
    if success:
        print("🎯 NEXT STEPS:")
        print("1. Run: python simple_usage_example.py")
        print("2. You should see '✅ Generated X TF-IDF embeddings with 1536 dimensions'")
        print("3. Upload to Pinecone should succeed without dimension errors")
    else:
        print("🔧 TROUBLESHOOTING NEEDED:")
        print("1. Check that scikit-learn is installed: pip install scikit-learn")
        print("2. Verify you're in the correct directory")
        print("3. Check for any error messages above")
