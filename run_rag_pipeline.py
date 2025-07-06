#!/usr/bin/env python3
"""
Unity RAG Pipeline Launcher
Simple script to run the RAG components from the root directory
"""

import sys
import os

def main():
    print("🎮 Unity RAG Pipeline Launcher")
    print("=" * 40)
    
    # Add RAG_components to Python path
    rag_path = os.path.join(os.path.dirname(__file__), 'RAG_components')
    if rag_path not in sys.path:
        sys.path.insert(0, rag_path)
    
    print("Available options:")
    print("1. Test all fixes")
    print("2. Populate database (simple)")
    print("3. Fix and repopulate database (complete)")
    print("4. Search knowledge base")
    print("5. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == "1":
                print("\n🧪 Running fix tests...")
                from RAG_components.test_fixes import test_all_fixes
                success = test_all_fixes()
                if success:
                    print("\n✅ All tests passed! Your fixes are working.")
                else:
                    print("\n❌ Some tests failed. Check the output above.")
                    
            elif choice == "2":
                print("\n🚀 Running simple database population...")
                from RAG_components.simple_usage_example import main as simple_main
                simple_main()
                
            elif choice == "3":
                print("\n🔧 Running complete fix and repopulation...")
                from RAG_components.fix_and_repopulate_database import fix_and_repopulate_database
                result = fix_and_repopulate_database(max_pages=20)
                print(f"\n📋 Final result: {result['final_status']}")
                
            elif choice == "4":
                print("\n🔍 Testing knowledge base search...")
                try:
                    from RAG_components.knowledge_retriever import UnityKnowledgeRetriever
                    
                    retriever = UnityKnowledgeRetriever()
                    
                    # Test search
                    query = input("Enter your Unity question: ").strip()
                    if query:
                        print(f"\n🔍 Searching for: {query}")
                        results = retriever.search_unity_knowledge(query, max_results=3)
                        
                        if results['status'] == 'success' and results['total_results'] > 0:
                            print(f"\n✅ Found {results['total_results']} results:")
                            for i, result in enumerate(results['results'], 1):
                                print(f"\n{i}. {result['title']}")
                                print(f"   Score: {result['relevance_score']}")
                                print(f"   URL: {result['source_url']}")
                                print(f"   Content: {result['content'][:200]}...")
                        else:
                            print("❌ No results found or search failed")
                            if 'error' in results:
                                print(f"Error: {results['error']}")
                    
                except Exception as e:
                    print(f"❌ Search failed: {e}")
                    print("Make sure your database is populated first (option 2 or 3)")
                
            elif choice == "5":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-5.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or check your configuration.")

if __name__ == "__main__":
    main()
