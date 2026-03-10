import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INPUT_FILE = "4_rag_cleaned_chunks.json"
OUTPUT_FILE = "5_embedded_chunks.json"
MODEL = "text-embedding-3-large"
BATCH_SIZE = 50


def format_for_embedding(chunk):
    """Combine metadata + content into a single string for better retrieval."""
    parts = []
    if chunk.get("product"):
        parts.append(f"Product: {chunk['product']}")
    if chunk.get("issue_type"):
        parts.append(f"Issue: {chunk['issue_type']}")
    if chunk.get("priority"):
        parts.append(f"Priority: {chunk['priority']}")
    if chunk.get("region"):
        parts.append(f"Region: {chunk['region']}")
    parts.append(f"Subject: {chunk['subject']}")
    parts.append(f"\n{chunk['content']}")
    return "\n".join(parts)


def embed_batch(texts):
    """Send a batch of texts to OpenAI and return embeddings."""
    response = client.embeddings.create(model=MODEL, input=texts)
    return [item.embedding for item in response.data]


def main():
    with open(INPUT_FILE) as f:
        chunks = json.load(f)

    print(f"Embedding {len(chunks)} chunks with {MODEL} (batch size {BATCH_SIZE})")

    embedded = []

    for i in tqdm(range(0, len(chunks), BATCH_SIZE)):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [format_for_embedding(c) for c in batch]

        try:
            embeddings = embed_batch(texts)
        except Exception as e:
            print(f"\n  Batch {i // BATCH_SIZE} failed: {e}, retrying in 5s...")
            time.sleep(5)
            try:
                embeddings = embed_batch(texts)
            except Exception as e2:
                print(f"  Retry failed: {e2}, skipping batch")
                continue

        for chunk, emb in zip(batch, embeddings):
            chunk["embedding"] = emb
            embedded.append(chunk)

        # small delay to stay under rate limits
        time.sleep(0.2)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(embedded, f)

    print(f"\nDone. Saved {len(embedded)} embedded chunks to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
