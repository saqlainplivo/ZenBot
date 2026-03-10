import json
from qdrant_client import QdrantClient

# Load one sample chunk to test query
with open("5_embedded_chunks.json", "r") as f:
    chunks = json.load(f)

# Connect to Qdrant
client = QdrantClient(path="./qdrant_local_db")

# Run a test query using chunk[0]'s embedding
print(f"🔍 Testing query with chunk_id: {chunks[0]['chunk_id']}")
print(f"   Subject: {chunks[0]['subject']}\n")

results = client.query_points(
    collection_name="zendesk_tickets",
    query=chunks[0]["embedding"],
    limit=3,
    with_payload=True,
).points

print(f"Top 3 results (should match chunk_id: {chunks[0]['chunk_id']}):\n")
for i, r in enumerate(results, 1):
    print(f"[{i}] Score     : {r.score:.4f}")
    print(f"    chunk_id  : {r.payload.get('chunk_id')}")
    print(f"    ticket_id : {r.payload.get('ticket_id')}")
    print(f"    subject   : {r.payload.get('subject')[:60]}...")
    print(f"    product   : {r.payload.get('product')}")
    print(f"    issue_type: {r.payload.get('issue_type')}")
    print()
