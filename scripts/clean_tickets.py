import json
import re
from pathlib import Path

INPUT_FILE = "1_zendesk_conversations.json"
OUTPUT_FILE = "2_cleaned_tickets.json"


# -----------------------------
# Cleaning Rules
# -----------------------------

def remove_images(text):
    return re.sub(r'!\[.*?\]\(.*?\)', '', text)


def remove_email_headers(text):
    patterns = [
        r"From:.*",
        r"Sent:.*",
        r"Subject:.*",
        r"To:.*",
        r"Cc:.*"
    ]
    for p in patterns:
        text = re.sub(p, '', text, flags=re.IGNORECASE)
    return text


def remove_signatures(text):
    patterns = [
        r"Regards,.*",
        r"Best regards,.*",
        r"Thanks,.*",
        r"Thank you,.*",
    ]

    for p in patterns:
        text = re.sub(p, '', text, flags=re.IGNORECASE | re.DOTALL)

    return text


def remove_low_signal_messages(text):
    low_signal_patterns = [
        r"any updates\??",
        r"is there an update\??",
        r"please provide an update",
        r"thanks",
        r"ok thanks"
    ]

    for p in low_signal_patterns:
        if re.search(p, text.lower()):
            return ""

    return text


def normalize_whitespace(text):
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_message(text):

    text = remove_images(text)
    text = remove_email_headers(text)
    text = remove_signatures(text)

    text = normalize_whitespace(text)

    text = remove_low_signal_messages(text)

    return text.strip()


# -----------------------------
# Conversation Formatter
# -----------------------------

def build_conversation(messages):

    cleaned_msgs = []

    for msg in messages:

        text = msg.get("message", "")

        cleaned = clean_message(text)

        if cleaned:
            cleaned_msgs.append(cleaned)

    return "\n".join(cleaned_msgs)


# -----------------------------
# Ticket Processing
# -----------------------------

def process_ticket(ticket):

    conversation = build_conversation(ticket.get("conversation", []))

    cleaned_ticket = {
        "ticket_id": ticket.get("ticket_id"),
        "subject": ticket.get("subject"),
        "tags": ticket.get("tags", []),
        "status": ticket.get("status"),
        "conversation_text": conversation
    }

    return cleaned_ticket


# -----------------------------
# Main Pipeline
# -----------------------------

def main():

    with open(INPUT_FILE, "r") as f:
        tickets = json.load(f)

    processed = []

    for ticket in tickets:
        cleaned = process_ticket(ticket)
        processed.append(cleaned)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(processed, f, indent=2)

    print(f"Processed {len(processed)} tickets.")
    print(f"Saved cleaned dataset to 2_cleaned_tickets.json")


if __name__ == "__main__":
    main()
