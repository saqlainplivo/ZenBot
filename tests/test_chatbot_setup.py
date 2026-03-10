"""Quick test to verify all components are ready for the chatbot."""

import os
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from anthropic import Anthropic

load_dotenv()

print("🔍 Checking ZenBot Setup...\n")

# 1. Check API Keys
print("1. API Keys:")
openai_key = os.getenv("OPENAI_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

if openai_key:
    print(f"   ✅ OPENAI_API_KEY found ({openai_key[:8]}...)")
else:
    print("   ❌ OPENAI_API_KEY missing in .env")

if anthropic_key:
    print(f"   ✅ ANTHROPIC_API_KEY found ({anthropic_key[:8]}...)")
else:
    print("   ❌ ANTHROPIC_API_KEY missing in .env")

# 2. Check Qdrant
print("\n2. Qdrant Database:")
try:
    client = QdrantClient(path="./qdrant_local_db")
    info = client.get_collection("zendesk_tickets")
    print(f"   ✅ Collection 'zendesk_tickets' found")
    print(f"   ✅ {info.points_count:,} chunks indexed")
except Exception as e:
    print(f"   ❌ Qdrant error: {e}")

# 3. Test OpenAI Embedding
print("\n3. OpenAI Embedding:")
if openai_key:
    try:
        openai_client = OpenAI(api_key=openai_key)
        response = openai_client.embeddings.create(
            model="text-embedding-3-large",
            input="test"
        )
        dims = len(response.data[0].embedding)
        print(f"   ✅ Embedding model working ({dims} dimensions)")
    except Exception as e:
        print(f"   ❌ OpenAI error: {e}")
else:
    print("   ⏭️  Skipped (no API key)")

# 4. Test Anthropic Claude
print("\n4. Anthropic Claude:")
if anthropic_key:
    try:
        anthropic_client = Anthropic(api_key=anthropic_key)
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=50,
            messages=[{"role": "user", "content": "Say 'ready' if you can receive this."}]
        )
        print(f"   ✅ Claude API working")
        print(f"   ✅ Response: {response.content[0].text}")
    except Exception as e:
        print(f"   ❌ Anthropic error: {e}")
else:
    print("   ⏭️  Skipped (no API key)")

print("\n" + "="*60)
if openai_key and anthropic_key:
    print("✅ All systems ready! Run: python3 7_query_chatbot.py")
else:
    print("⚠️  Add missing API keys to .env file first")
print("="*60)
