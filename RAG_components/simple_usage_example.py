"""
Simple Usage Example - How to populate your Unity vector database
Uses your existing config system for API key management
"""

from .populate_vector_db import populate_unity_vector_db_auto

def main():
    print("🎮 Unity Vector Database Population Example")
    print("=" * 50)
    
    # This function automatically uses your .env file configuration
    result = populate_unity_vector_db_auto(
        max_pages=10,  # Start small for testing
        clear_existing=True,  # Clear any existing data
        namespace=""  # Use default namespace
    )
    
    if result['status'] == 'success':
        print("\n🎉 SUCCESS!")
        print(f"📊 Scraped {result['documents_scraped']} Unity documentation pages")
        print(f"📝 Created {result['chunks_created']} searchable chunks")
        print(f"☁️ Uploaded {result['vectors_uploaded']} vectors to Pinecone")
        print(f"🗂️ Index: {result['index_name']}")
        print(f"📁 Namespace: {result['namespace']}")
        
        print("\n✅ Your Unity knowledge base is ready!")
        print("Your friend can now search it using the RAG components.")
        
    else:
        print(f"\n❌ FAILED: {result['message']}")
        
        if "Pinecone API key not configured" in result['message']:
            print("\n🔧 To fix this:")
            print("1. Edit your .env file")
            print("2. Set: PINECONE_API_KEY=your-actual-pinecone-api-key")
            print("3. Get your API key from: https://pinecone.io")

if __name__ == "__main__":
    main()
