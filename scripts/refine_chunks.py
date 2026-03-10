import json
import re

INPUT_FILE = "3_rag_ready_chunks.json"
OUTPUT_FILE = "4_rag_cleaned_chunks.json"

# --- Low-signal patterns to strip ---
LOW_SIGNAL_PATTERNS = [
    r"hi team,?",
    r"hello team,?",
    r"hi \w+,?",
    r"hello \w+,?",
    r"dear \w+,?",
    r"thank you for contacting.*?[.!]",
    r"have a nice day[.!]?",
    r"hope you'?r?e doing.*?[.!]",
    r"we are following up.*?[.!]",
    r"please let us know.*?[.!]",
    r"any updates\??",
    r"marking this ticket as solved.*?[.!]",
    r"looking forward to hearing.*?[.!]",
    r"greetings for the day[.!]?",
    r"we shall wait for your response[.!]?",
    r"awaiting your (response|confirmation)[.!]?",
    r"we will be happy to assist you further[.!]?",
    r"updates to follow[.!]?",
    r"sure,? team[.!]?",
]

# --- Tag-based metadata extraction ---
PRODUCT_TAGS = {"voice", "sms", "call", "messaging", "phone_numbers", "phlo"}
PRIORITY_TAGS = {"p1", "p2", "p3", "p4"}
REGION_TAGS = {"emea", "apac", "us", "latam", "americas"}

ISSUE_TYPE_MAP = {
    "voice_issue__dtmf": "dtmf",
    "sender_id_issues": "sender_id",
    "sender_id_registration_internationalsms": "sender_id_registration",
    "short_code_": "short_code",
    "number_porting": "number_porting",
    "call_quality": "call_quality",
    "sms_delivery": "sms_delivery",
    "product_query_csm": "product_query",
    "internal_support": "internal_support",
}


def clean_content(text):
    for pattern in LOW_SIGNAL_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # emails
    text = re.sub(r"\S+@\S+\.\S+", "", text)
    # urls
    text = re.sub(r"https?://\S+", "", text)
    # phone numbers
    text = re.sub(r"\+?\d[\d\s\-\(\)]{8,}\d", "", text)
    # leftover markdown bold markers
    text = re.sub(r"\*\*", "", text)
    # stray separators
    text = re.sub(r"\* \* \*", "", text)
    text = re.sub(r"--+", "", text)
    # normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_metadata(tags):
    tags_lower = {t.lower() for t in tags}

    product = next((t for t in tags_lower if t in PRODUCT_TAGS), None)
    priority = next((t for t in tags_lower if t in PRIORITY_TAGS), None)
    region = next((t for t in tags_lower if t in REGION_TAGS), None)

    issue_type = None
    for tag_key, issue_val in ISSUE_TYPE_MAP.items():
        if tag_key in tags_lower:
            issue_type = issue_val
            break

    return {
        "product": product,
        "priority": priority,
        "region": region,
        "issue_type": issue_type,
    }


def main():
    with open(INPUT_FILE) as f:
        chunks = json.load(f)

    cleaned = []
    empty_count = 0

    for chunk in chunks:
        content = clean_content(chunk["content"])

        # drop chunks that became too short after cleaning
        if len(content.split()) < 20:
            empty_count += 1
            continue

        meta = extract_metadata(chunk.get("tags", []))

        cleaned.append({
            "ticket_id": chunk["ticket_id"],
            "chunk_id": chunk["chunk_id"],
            "subject": chunk["subject"],
            "product": meta["product"],
            "issue_type": meta["issue_type"],
            "priority": meta["priority"],
            "region": meta["region"],
            "status": chunk["status"],
            "content": content,
            "source": "zendesk_ticket",
        })

    with open(OUTPUT_FILE, "w") as f:
        json.dump(cleaned, f, indent=2)

    print(f"Input:    {len(chunks)} chunks")
    print(f"Dropped:  {empty_count} (too short after cleaning)")
    print(f"Output:   {len(cleaned)} chunks → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
