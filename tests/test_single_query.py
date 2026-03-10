"""Quick single-query test without interactive loop."""

import os
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from dotenv import load_dotenv

load_dotenv()

# Initialize
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant_client = QdrantClient(path="./qdrant_local_db")

# Test question
QUESTION = "What are common DTMF issues reported in tickets?"

print(f"🔍 Question: {QUESTION}\n")

# 1. Embed question
print("⏳ Embedding question...")
response = openai_client.embeddings.create(
    model="text-embedding-3-large",
    input=QUESTION
)
query_vector = response.data[0].embedding
print(f"✅ Embedded to {len(query_vector)} dimensions\n")

# 2. Search Qdrant
print("⏳ Searching Qdrant...")
results = qdrant_client.query_points(
    collection_name="zendesk_tickets",
    query=query_vector,
    limit=5,
    with_payload=True,
).points

print(f"✅ Found {len(results)} relevant chunks:\n")

# 3. Display results
for i, r in enumerate(results, 1):
    print(f"[{i}] Score: {r.score:.4f} | Ticket #{r.payload['ticket_id']}")
    print(f"    Subject: {r.payload['subject']}")
    print(f"    Product: {r.payload.get('product')} | Issue: {r.payload.get('issue_type')}")
    print(f"    Content: {r.payload['content'][:200]}...")
    print()

# 4. Build prompt and query LLM
print("⏳ Asking GPT-4o...\n")

context_parts = []
for r in results:
    context_parts.append(
        f"Ticket #{r.payload['ticket_id']}: {r.payload['subject']}\n{r.payload['content']}"
    )
context = "\n\n".join(context_parts)

system_prompt = """You are ZenBot, a Zendesk support assistant. Answer based ONLY on the provided ticket context.
Cite sources using [ticket_id] format. Be concise."""

user_message = f"""Context:\n{context}\n\nQuestion: {QUESTION}"""

response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ],
    temperature=0.3,
    max_tokens=500,
)

print("🤖 ZenBot Answer:")
print("=" * 70)
print(response.choices[0].message.content)
print("=" * 70)
