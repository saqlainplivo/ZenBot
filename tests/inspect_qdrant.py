from qdrant_client import QdrantClient

client = QdrantClient(path="./qdrant_local_db")
info = client.get_collection("zendesk_tickets")

print("=" * 60)
print("QDRANT COLLECTION: zendesk_tickets")
print("=" * 60)
print(f"Total points      : {info.points_count:,}")
print(f"Vector dimensions : {info.config.params.vectors.size}")
print(f"Distance metric   : {info.config.params.vectors.distance}")
print(f"Status            : {info.status}")
print("=" * 60)

# Get a sample point to show structure
sample = client.scroll(
    collection_name="zendesk_tickets",
    limit=1,
    with_payload=True,
    with_vectors=False,
)[0][0]

print("\nSAMPLE POINT PAYLOAD:")
print("-" * 60)
for key, value in sample.payload.items():
    if key != 'content':
        print(f"{key:15} : {value}")
    else:
        print(f"{key:15} : {value[:100]}...")
print("=" * 60)
