import json
import re

INPUT_FILE = "2_cleaned_tickets.json"
OUTPUT_FILE = "3_rag_ready_chunks.json"

CHUNK_SIZE = 500


def clean_text(text):
    text = re.sub(r"\*\*\*.*?\*\*\*", "", text)
    text = re.sub(r"Important Notice:.*", "", text, flags=re.DOTALL)
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_text(text, chunk_size=500):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks


def process_ticket(ticket):
    text = clean_text(ticket["conversation_text"])
    chunks = chunk_text(text)

    processed_chunks = []
    for i, chunk in enumerate(chunks):
        processed_chunks.append({
            "ticket_id": ticket["ticket_id"],
            "chunk_id": f"{ticket['ticket_id']}_{i}",
            "subject": ticket["subject"],
            "tags": ticket["tags"],
            "status": ticket["status"],
            "content": chunk,
            "source": "zendesk_ticket",
        })
    return processed_chunks


def main():
    with open(INPUT_FILE) as f:
        tickets = json.load(f)

    rag_chunks = []
    for ticket in tickets:
        rag_chunks.extend(process_ticket(ticket))

    with open(OUTPUT_FILE, "w") as f:
        json.dump(rag_chunks, f, indent=2)

    print(f"Created {len(rag_chunks)} chunks from {len(tickets)} tickets")


if __name__ == "__main__":
    main()
