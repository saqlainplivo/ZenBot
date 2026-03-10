# pip install qdrant-client tqdm

import json
import uuid
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    PayloadSchemaType,
)

# ── Config ─────────────────────────────────────────────────────────────────────
CHUNKS_FILE     = "5_embedded_chunks.json"
QDRANT_PATH     = "./qdrant_local_db"       # local folder, no Docker needed
COLLECTION_NAME = "zendesk_tickets"
EMBED_DIMS      = 3072                      # text-embedding-3-large output size
BATCH_SIZE      = 100


# ── 1. Load your embedded chunks ───────────────────────────────────────────────
with open(CHUNKS_FILE, "r") as f:
    chunks = json.load(f)

print(f"✅ Loaded {len(chunks)} chunks from {CHUNKS_FILE}")

# Quick validation — make sure embeddings look right
sample = chunks[0]
assert "embedding" in sample, "No 'embedding' field found in chunk"
assert len(sample["embedding"]) == EMBED_DIMS, \
    f"Expected {EMBED_DIMS} dims, got {len(sample['embedding'])}"
print(f"✅ Embedding dimension confirmed: {len(sample['embedding'])}")


# ── 2. Connect to Qdrant (local file mode — no server needed) ──────────────────
client = QdrantClient(path=QDRANT_PATH)
print(f"✅ Qdrant connected at: {QDRANT_PATH}")


# ── 3. Create collection (skip if already exists) ──────────────────────────────
existing = [c.name for c in client.get_collections().collections]

if COLLECTION_NAME not in existing:
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBED_DIMS, distance=Distance.COSINE),
    )

    # Create payload indexes for filtered search
    for field, schema in [
        ("product",     PayloadSchemaType.KEYWORD),
        ("issue_type",  PayloadSchemaType.KEYWORD),
        ("priority",    PayloadSchemaType.KEYWORD),
        ("region",      PayloadSchemaType.KEYWORD),
        ("status",      PayloadSchemaType.KEYWORD),
    ]:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name=field,
            field_schema=schema,
        )

    print(f"✅ Collection '{COLLECTION_NAME}' created with payload indexes")
else:
    print(f"⚠️  Collection '{COLLECTION_NAME}' already exists — skipping creation")


# ── 4. Build and upsert points ─────────────────────────────────────────────────
points = []

for chunk in chunks:
    payload = {
        # ── For display / citations in the chatbot response ──
        "ticket_id":  chunk.get("ticket_id"),
        "chunk_id":   chunk.get("chunk_id"),
        "subject":    chunk.get("subject"),
        "content":    chunk.get("content"),
        "source":     chunk.get("source", "zendesk_ticket"),
        "product":    chunk.get("product"),
        "issue_type": chunk.get("issue_type"),
        "priority":   chunk.get("priority"),
        "region":     chunk.get("region"),
        "status":     chunk.get("status"),
    }

    points.append(
        PointStruct(
            id=str(uuid.uuid4()),           # Qdrant needs a unique UUID per point
            vector=chunk["embedding"],
            payload={k: v for k, v in payload.items() if v is not None},
        )
    )

# Upsert in batches
for i in tqdm(range(0, len(points), BATCH_SIZE), desc="Upserting to Qdrant"):
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points[i : i + BATCH_SIZE],
    )

print(f"✅ Upserted {len(points)} chunks into '{COLLECTION_NAME}'")


# ── 5. Verify — check collection stats ────────────────────────────────────────
info = client.get_collection(COLLECTION_NAME)
print(f"\n📊 Collection stats:")
print(f"   Points count  : {info.points_count}")
print(f"   Vector size   : {info.config.params.vectors.size}")
print(f"   Distance      : {info.config.params.vectors.distance}")


# ── 6. Sanity check — run a test query using an existing embedding ─────────────
# We re-use chunk[0]'s embedding as a test query vector (should return itself as #1)
print(f"\n🔍 Running sanity check query...")
results = client.query_points(
    collection_name=COLLECTION_NAME,
    query=chunks[0]["embedding"],
    limit=3,
    with_payload=True,
).points

print(f"\nTop 3 results for test query (should match chunk_id: {chunks[0]['chunk_id']}):")
for i, r in enumerate(results, 1):
    print(f"\n  [{i}] Score     : {r.score:.4f}")
    print(f"       chunk_id  : {r.payload.get('chunk_id')}")
    print(f"       ticket_id : {r.payload.get('ticket_id')}")
    print(f"       subject   : {r.payload.get('subject')}")
    print(f"       product   : {r.payload.get('product')}")
    print(f"       issue_type: {r.payload.get('issue_type')}")
