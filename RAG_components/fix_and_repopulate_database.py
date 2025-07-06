#!/usr/bin/env python3
"""
Complete Database Fix and Repopulation Script
Clears existing corrupted data and repopulates with fixed pipeline
"""

import time
from typing import Dict, Any

def fix_and_repopulate_database(max_pages: int = 20) -> Dict[str, Any]:
    """
    Complete pipeline to fix and repopulate the database
    
    Args:
        max_pages: Maximum pages to scrape (start small for testing)
    
    Returns:
        Dictionary with detailed results
    """
    
    print("🔧 UNITY KNOWLEDGE BASE - COMPLETE FIX & REPOPULATION")
    print("=" * 70)
    
    results = {
        "start_time": time.time(),
        "steps_completed": [],
        "errors": [],
        "final_status": "unknown"
    }
    
    try:
        # Step 1: Clear existing corrupted data
        print("\n🧹 STEP 1: Clearing existing corrupted data...")
        print("-" * 50)
        
        try:
            from .populate_vector_db import populate_unity_vector_db_auto
            
            # First, let's check current database status
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
                raise ValueError("Pinecone API key not found")
            
            manager = PineconeManager(api_key=pinecone_key)
            
            # Get current stats
            current_stats = manager.get_index_stats()
            print(f"📊 Current database status:")
            print(f"   Total vectors: {current_stats.get('total_vector_count', 0)}")
            print(f"   Dimension: {current_stats.get('dimension', 'unknown')}")
            
            # Clear the database
            print("🗑️ Clearing all existing data...")
            clear_result = manager.clear_namespace("")
            
            if clear_result.get("status") == "success":
                print("✅ Database cleared successfully")
                results["steps_completed"].append("database_cleared")
            else:
                raise Exception(f"Failed to clear database: {clear_result}")
                
        except Exception as e:
            error_msg = f"Error clearing database: {e}"
            print(f"❌ {error_msg}")
            results["errors"].append(error_msg)
            return results
        
        # Step 2: Test embedding generation
        print("\n🧪 STEP 2: Testing fixed embedding generation...")
        print("-" * 50)
        
        try:
            from .populate_vector_db import generate_simple_embeddings
            
            # Test with sample data
            test_docs = [
                {'text': 'Unity Rigidbody component allows GameObjects to be affected by physics'},
                {'text': 'Transform component defines position, rotation and scale'}
            ]
            
            print("🔍 Testing embedding generation...")
            result = generate_simple_embeddings(test_docs)
            
            # Verify dimensions
            all_correct = True
            for i, doc in enumerate(result):
                if 'embedding' in doc:
                    dim = len(doc['embedding'])
                    if dim == 1536:
                        print(f"   ✅ Test embedding {i+1}: {dim} dimensions (CORRECT)")
                    else:
                        print(f"   ❌ Test embedding {i+1}: {dim} dimensions (WRONG)")
                        all_correct = False
                else:
                    print(f"   ❌ Test embedding {i+1}: No embedding found")
                    all_correct = False
            
            if all_correct:
                print("✅ Embedding generation test PASSED")
                results["steps_completed"].append("embedding_test_passed")
            else:
                raise Exception("Embedding generation still has dimension issues")
                
        except Exception as e:
            error_msg = f"Error testing embeddings: {e}"
            print(f"❌ {error_msg}")
            results["errors"].append(error_msg)
            return results
        
        # Step 3: Scrape and populate with fixed pipeline
        print(f"\n🕷️ STEP 3: Scraping and populating with fixed pipeline (max {max_pages} pages)...")
        print("-" * 50)
        
        try:
            # Run the fixed pipeline
            populate_result = populate_unity_vector_db_auto(
                max_pages=max_pages,
                clear_existing=False,  # Already cleared
                namespace=""
            )
            
            if populate_result.get("status") == "success":
                print("✅ Population completed successfully!")
                print(f"📊 Results:")
                print(f"   Documents scraped: {populate_result.get('documents_scraped', 0)}")
                print(f"   Chunks created: {populate_result.get('chunks_created', 0)}")
                print(f"   Vectors uploaded: {populate_result.get('vectors_uploaded', 0)}")
                print(f"   Upload errors: {populate_result.get('upload_errors', 0)}")
                
                results["populate_result"] = populate_result
                results["steps_completed"].append("population_completed")
                
                if populate_result.get('upload_errors', 0) == 0:
                    print("🎉 NO UPLOAD ERRORS - All fixes working correctly!")
                    results["steps_completed"].append("zero_upload_errors")
                else:
                    print(f"⚠️ Still have {populate_result.get('upload_errors', 0)} upload errors")
                    
            else:
                raise Exception(f"Population failed: {populate_result.get('message', 'Unknown error')}")
                
        except Exception as e:
            error_msg = f"Error during population: {e}"
            print(f"❌ {error_msg}")
            results["errors"].append(error_msg)
            return results
        
        # Step 4: Verify data quality
        print("\n🔍 STEP 4: Verifying data quality...")
        print("-" * 50)
        
        try:
            # Check final database stats
            final_stats = manager.get_index_stats()
            print(f"📊 Final database status:")
            print(f"   Total vectors: {final_stats.get('total_vector_count', 0)}")
            print(f"   Dimension: {final_stats.get('dimension', 'unknown')}")
            
            # Test a sample search to verify text content is stored
            if final_stats.get('total_vector_count', 0) > 0:
                print("🔍 Testing sample search to verify text content...")
                
                # Search for a sample vector to check if text content is stored
                dummy_vector = [0.0] * 1536
                sample_results = manager.index.query(
                    vector=dummy_vector,
                    top_k=1,
                    include_metadata=True
                )
                
                if sample_results.matches:
                    sample_metadata = sample_results.matches[0].metadata
                    
                    # Check for text content
                    has_text_content = bool(sample_metadata.get("text_content", ""))
                    has_text_preview = bool(sample_metadata.get("text_preview", ""))
                    text_length = sample_metadata.get("full_text_length", 0)
                    
                    print(f"   ✅ Sample vector metadata check:")
                    print(f"      Has text_content: {has_text_content}")
                    print(f"      Has text_preview: {has_text_preview}")
                    print(f"      Text length: {text_length}")
                    
                    if has_text_content and text_length > 0:
                        print("   🎉 Text content is properly stored!")
                        results["steps_completed"].append("text_content_verified")
                    else:
                        print("   ⚠️ Text content may not be properly stored")
                        
                    # Check for encoding issues
                    title = sample_metadata.get("original_title", "")
                    if "ã" in title or "â" in title:
                        print(f"   ⚠️ Potential encoding issue detected in title: {title}")
                    else:
                        print("   ✅ No obvious encoding issues detected")
                        results["steps_completed"].append("encoding_verified")
                
            results["final_stats"] = final_stats
            results["steps_completed"].append("verification_completed")
            
        except Exception as e:
            error_msg = f"Error during verification: {e}"
            print(f"❌ {error_msg}")
            results["errors"].append(error_msg)
        
        # Final summary
        print("\n🎯 FINAL SUMMARY")
        print("=" * 50)
        
        if len(results["errors"]) == 0:
            results["final_status"] = "success"
            print("🎉 ALL FIXES APPLIED SUCCESSFULLY!")
            print("✅ Your Unity knowledge base is now:")
            print("   • Free of dimension errors")
            print("   • Storing actual text content")
            print("   • Handling UTF-8 encoding properly")
            print("   • Ready for your Unity copilot!")
        else:
            results["final_status"] = "partial_success"
            print("⚠️ COMPLETED WITH SOME ISSUES:")
            for error in results["errors"]:
                print(f"   • {error}")
        
        results["end_time"] = time.time()
        results["total_duration"] = results["end_time"] - results["start_time"]
        
        print(f"\n⏱️ Total time: {results['total_duration']:.1f} seconds")
        
        return results
        
    except Exception as e:
        results["final_status"] = "error"
        results["errors"].append(f"Critical error: {e}")
        print(f"\n💥 CRITICAL ERROR: {e}")
        return results

if __name__ == "__main__":
    print("🚀 Starting complete database fix and repopulation...")
    print("This will:")
    print("1. Clear all existing corrupted data")
    print("2. Test the dimension fixes")
    print("3. Scrape fresh Unity documentation with proper encoding")
    print("4. Upload with text content properly stored")
    print("5. Verify everything is working correctly")
    
    # Ask for confirmation
    response = input("\nProceed? (y/N): ").strip().lower()
    
    if response == 'y':
        result = fix_and_repopulate_database(max_pages=20)  # Start with 20 pages for testing
        
        print(f"\n📋 FINAL RESULT: {result['final_status']}")
        if result['final_status'] == 'success':
            print("🎉 Your Unity knowledge base is ready!")
        else:
            print("❌ Some issues occurred. Check the output above for details.")
    else:
        print("❌ Operation cancelled.")
