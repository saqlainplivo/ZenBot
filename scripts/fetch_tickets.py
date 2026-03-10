import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN")
EMAIL = os.getenv("ZENDESK_EMAIL")
TOKEN = os.getenv("ZENDESK_API_TOKEN")
MAX_TICKETS = 5000

auth = (f"{EMAIL}/token", TOKEN)
base_url = f"https://{SUBDOMAIN}.zendesk.com/api/v2"


OUTPUT_FILE = "1_zendesk_conversations.json"


def get_comments(ticket_id, retries=3):
    url = f"{base_url}/tickets/{ticket_id}/comments.json"
    for attempt in range(retries):
        try:
            r = requests.get(url, auth=auth)
            r.raise_for_status()
            return r.json()["comments"]
        except requests.exceptions.RequestException as e:
            print(f"    Attempt {attempt + 1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return None


def save_dataset(dataset):
    with open(OUTPUT_FILE, "w") as f:
        json.dump(dataset, f, indent=2)


def fetch_all_tickets():
    """Paginate through the tickets endpoint until MAX_TICKETS or no more pages."""
    all_tickets = []
    url = f"{base_url}/tickets.json?per_page=100"

    while url and len(all_tickets) < MAX_TICKETS:
        print(f"Fetching page... ({len(all_tickets)} tickets so far)")
        r = requests.get(url, auth=auth)
        r.raise_for_status()
        data = r.json()

        all_tickets.extend(data["tickets"])
        url = data.get("next_page")

        # respect rate limits
        time.sleep(0.5)

    return all_tickets[:MAX_TICKETS]


def main():
    # Step 1 — Fetch tickets with pagination
    print("Fetching tickets...")
    all_tickets = fetch_all_tickets()
    print(f"Got {len(all_tickets)} tickets\n")

    # Step 2 & 3 — Fetch conversations and build dataset
    dataset = []
    skipped = []

    for i, ticket in enumerate(all_tickets, 1):
        ticket_id = ticket["id"]
        print(f"  [{i}/{len(all_tickets)}] Ticket #{ticket_id}: {ticket['subject']}")

        comments = get_comments(ticket_id)

        if comments is None:
            print(f"    SKIPPED ticket #{ticket_id} after retries")
            skipped.append(ticket_id)
            continue

        convo = []
        for c in comments:
            if not c["public"]:
                continue
            convo.append({
                "author_id": c["author_id"],
                "message": c["body"],
                "timestamp": c["created_at"],
            })

        dataset.append({
            "ticket_id": ticket_id,
            "subject": ticket["subject"],
            "tags": ticket["tags"],
            "status": ticket["status"],
            "conversation": convo,
        })

        # save incrementally every 50 tickets
        if len(dataset) % 50 == 0:
            save_dataset(dataset)
            print(f"    [checkpoint] saved {len(dataset)} tickets")

        # respect rate limits on comments endpoint
        time.sleep(0.25)

    # final save
    save_dataset(dataset)

    print(f"\nDone. Saved {len(dataset)} tickets to {OUTPUT_FILE}")
    if skipped:
        print(f"Skipped {len(skipped)} tickets: {skipped}")


if __name__ == "__main__":
    main()
