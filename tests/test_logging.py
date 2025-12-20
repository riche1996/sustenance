"""Test script for bug logging functionality."""
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import Config
from src.services.opensearch_client import OpenSearchClient
from src.services.embedding_service import EmbeddingService

def test_opensearch_connection():
    """Test OpenSearch connection."""
    print("\n" + "="*60)
    print("Test 1: OpenSearch Connection")
    print("="*60)
    
    try:
        client = OpenSearchClient(
            host=Config.OPENSEARCH_HOST,
            port=Config.OPENSEARCH_PORT,
            index_name=Config.OPENSEARCH_INDEX
        )
        print("✓ Connected to OpenSearch")
        print(f"✓ Index: {Config.OPENSEARCH_INDEX}")
        client.close()
        return True
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return False


def test_embedding_service():
    """Test embedding generation."""
    print("\n" + "="*60)
    print("Test 2: Embedding Service")
    print("="*60)
    
    try:
        print(f"Loading model from: {Config.EMBEDDING_MODEL}")
        embedding_service = EmbeddingService(model_name=Config.EMBEDDING_MODEL)
        
        # Test embedding generation
        test_text = "This is a test bug about login redirect loop"
        print(f"\nGenerating embedding for: '{test_text}'")
        
        embedding = embedding_service.embed_text(test_text)
        
        print(f"✓ Embedding generated")
        print(f"  Type: {type(embedding)}")
        print(f"  Dimension: {len(embedding)}")
        print(f"  First 5 values: {embedding[:5]}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to generate embedding: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_log():
    """Test simple log indexing."""
    print("\n" + "="*60)
    print("Test 3: Simple Log Indexing")
    print("="*60)
    
    try:
        # Initialize components
        client = OpenSearchClient(
            host=Config.OPENSEARCH_HOST,
            port=Config.OPENSEARCH_PORT,
            index_name=Config.OPENSEARCH_INDEX
        )
        
        embedding_service = EmbeddingService(model_name=Config.EMBEDDING_MODEL)
        
        # Create test log
        test_bug_summary = "Test Bug: Login Redirect Loop"
        test_bug_description = "When user tries to login, they get redirected back to login page"
        test_analysis = "Found issue in views.py line 45: Missing authentication check"
        
        print("\nGenerating embedding...")
        embedding = embedding_service.embed_text(
            f"{test_bug_summary} {test_bug_description} {test_analysis}"
        )
        
        print(f"✓ Embedding generated (dimension: {len(embedding)})")
        
        # Prepare log data
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'log_type': 'bug_analysis',
            'bug_id': 'TEST-001',
            'bug_summary': test_bug_summary,
            'bug_description': test_bug_description,
            'bug_status': 'Open',
            'bug_priority': 'High',
            'analysis_result': test_analysis,
            'findings': [
                {
                    'file': 'views.py',
                    'line': 45,
                    'issue': 'Missing authentication check',
                    'severity': 'High'
                }
            ],
            'files_analyzed': ['views.py', 'urls.py'],
            'total_findings': 1,
            'embedding': embedding,
            'metadata': {
                'test': True,
                'project': 'TEST'
            }
        }
        
        print("\nIndexing log to OpenSearch...")
        doc_id = client.index_log(log_data)
        
        print(f"✓ Log indexed successfully")
        print(f"  Document ID: {doc_id}")
        
        # Verify by retrieving
        print("\nVerifying log was indexed...")
        recent = client.get_recent_logs(size=1)
        
        if recent and recent[0].get('bug_id') == 'TEST-001':
            print("✓ Log verified in OpenSearch")
            print(f"  Retrieved bug: {recent[0].get('bug_summary')}")
        else:
            print("⚠ Could not verify log")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to index log: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_semantic_search():
    """Test semantic search."""
    print("\n" + "="*60)
    print("Test 4: Semantic Search")
    print("="*60)
    
    try:
        client = OpenSearchClient(
            host=Config.OPENSEARCH_HOST,
            port=Config.OPENSEARCH_PORT,
            index_name=Config.OPENSEARCH_INDEX
        )
        
        embedding_service = EmbeddingService(model_name=Config.EMBEDDING_MODEL)
        
        # Search for similar bugs
        search_query = "authentication problems"
        print(f"\nSearching for: '{search_query}'")
        
        query_embedding = embedding_service.embed_text(search_query)
        results = client.semantic_search(query_embedding, size=3)
        
        print(f"✓ Found {len(results)} results")
        
        for i, result in enumerate(results, 1):
            print(f"\n  {i}. {result.get('bug_id', 'N/A')}: {result.get('bug_summary', 'N/A')[:50]}...")
            print(f"     Score: {result.get('score', 0):.4f}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Semantic search failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Bug Logging Test Suite")
    print("="*60)
    
    print(f"\nConfiguration:")
    print(f"  OpenSearch: {Config.OPENSEARCH_HOST}:{Config.OPENSEARCH_PORT}")
    print(f"  Index: {Config.OPENSEARCH_INDEX}")
    print(f"  Model: {Config.EMBEDDING_MODEL}")
    print(f"  Enabled: {Config.ENABLE_LOG_HISTORY}")
    
    results = []
    
    # Run tests
    results.append(("OpenSearch Connection", test_opensearch_connection()))
    results.append(("Embedding Service", test_embedding_service()))
    results.append(("Simple Log Indexing", test_simple_log()))
    results.append(("Semantic Search", test_semantic_search()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠ {total - passed} test(s) failed")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
