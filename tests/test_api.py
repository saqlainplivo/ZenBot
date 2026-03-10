"""
Test script for ZenBot API endpoints.

Make sure the API server is running first:
    python3 8_api_server.py
    # or
    uvicorn 8_api_server:app --reload --port 8000

Then run this test:
    python3 test_api.py
"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_health():
    """Test health check endpoint."""
    print("🔍 Testing GET / (health check)...")
    response = requests.get(f"{API_BASE}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    assert response.status_code == 200


def test_stats():
    """Test stats endpoint."""
    print("🔍 Testing GET /stats...")
    response = requests.get(f"{API_BASE}/stats")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Collection: {data['collection_name']}")
    print(f"Total chunks: {data['total_chunks']:,}")
    print(f"Dimensions: {data['vector_dimensions']}")
    print(f"Distance: {data['distance_metric']}")
    print(f"Status: {data['status']}\n")
    assert response.status_code == 200


def test_search():
    """Test raw search endpoint."""
    print("🔍 Testing POST /search (raw semantic search)...")
    payload = {
        "question": "DTMF issues",
        "top_k": 3
    }
    response = requests.post(f"{API_BASE}/search", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()

    print(f"Retrieved {data['metadata']['retrieval_count']} chunks")
    print(f"Top score: {data['metadata']['top_score']:.4f}")
    print(f"Time: {data['metadata']['total_time_ms']}ms\n")

    print("Top 3 chunks:")
    for i, chunk in enumerate(data['chunks'][:3], 1):
        print(f"  [{i}] Score: {chunk['score']:.4f} | Ticket #{chunk['ticket_id']}")
        print(f"      Subject: {chunk['subject'][:60]}...")
    print()

    assert response.status_code == 200


def test_query():
    """Test full RAG query endpoint."""
    print("🔍 Testing POST /query (full RAG pipeline)...")
    payload = {
        "question": "What are common DTMF issues?",
        "filters": {},
        "top_k": 5,
        "include_chunks": True
    }
    response = requests.post(f"{API_BASE}/query", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()

    print(f"\n📊 Metadata:")
    print(f"   Retrieval count: {data['metadata']['retrieval_count']}")
    print(f"   Top score: {data['metadata']['top_score']:.4f}")
    print(f"   Embed time: {data['metadata']['embed_time_ms']}ms")
    print(f"   Search time: {data['metadata']['search_time_ms']}ms")
    print(f"   LLM time: {data['metadata']['llm_time_ms']}ms")
    print(f"   Total time: {data['metadata']['total_time_ms']}ms")

    print(f"\n📚 Citations: {data['citations']}")

    print(f"\n🤖 Answer:")
    print("="*70)
    print(data['answer'])
    print("="*70)

    assert response.status_code == 200


def test_query_with_filter():
    """Test query with metadata filter."""
    print("\n🔍 Testing POST /query with filter (product=call)...")
    payload = {
        "question": "What issues are reported?",
        "filters": {"product": "call"},
        "top_k": 3,
        "include_chunks": False
    }
    response = requests.post(f"{API_BASE}/query", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()

    print(f"Filters applied: {data['metadata']['filters_applied']}")
    print(f"Retrieved: {data['metadata']['retrieval_count']} chunks")
    print(f"\n🤖 Answer:\n{data['answer']}\n")

    assert response.status_code == 200


def main():
    print("="*70)
    print("ZenBot API Test Suite")
    print("="*70 + "\n")

    try:
        test_health()
        test_stats()
        test_search()
        test_query()
        test_query_with_filter()

        print("\n" + "="*70)
        print("✅ All tests passed!")
        print("="*70)

    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: Make sure the API server is running:")
        print("   python3 8_api_server.py")
        print("   # or")
        print("   uvicorn 8_api_server:app --reload --port 8000")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
