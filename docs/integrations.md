# ZenBot × Dobby PAI — Hybrid Intelligence Architecture

## Background

ZenBot is a RAG-based chatbot trained on historical Zendesk support tickets. It answers questions by searching 4,377 indexed chunks and generating GPT-4o responses with citations back to real tickets.

Dobby PAI is an agentic chatbot (running on EKS/ECS) with live system access — queryable via Slack and an internal web UI. It can look up specific calls, logs, messages, and take actions in real time.

The goal is to combine both into a single interface where the right engine handles the right query, but neither system's strengths are ever lost — specifically, ZenBot's citation/accountability layer should persist even when Dobby is answering.

---

## Core Design Principle

> Dobby answers *what*. ZenBot proves *why* with citations. They are complementary, not competing.

| Capability | ZenBot | Dobby PAI |
|---|---|---|
| Historical ticket patterns | ✅ | ✅ |
| Citation to real tickets | ✅ | ❌ |
| Live call / log lookup | ❌ | ✅ |
| Specific message/ID queries | ❌ | ✅ |
| Agentic actions | ❌ | ✅ |
| Accountability layer | ✅ | ❌ |

---

## Architecture

```
                        ┌─────────────────────┐
     User Query ──────► │  Intent Classifier   │
                        │  (GPT-4o-mini, fast) │
                        └──────────┬──────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
             "Generic/How-to"            "Specific/Live"
             (patterns, concepts,        (call ID, log,
              best practices)             message, user)
                    │                             │
                    ▼                             ▼
          ┌──────────────────┐        ┌──────────────────┐
          │  ZenBot RAG      │        │   Dobby PAI      │
          │  (primary)       │        │   (primary)      │
          └────────┬─────────┘        └────────┬─────────┘
                   │                            │
                   └──────────┬─────────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │  Citation Enricher    │  ← Always runs ZenBot
                  │  (parallel async)     │    vector search regardless
                  └───────────┬───────────┘    of which path was taken
                              │
                              ▼
                  ┌───────────────────────┐
                  │  Response Synthesizer │
                  │  · Primary answer     │
                  │  · Supporting tickets │
                  │  · Source label       │
                  └───────────┬───────────┘
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
               ZenBot UI            Slack Bot
```

---

## Query Routing Logic

### Path A — Generic Query
**Triggers when:** question is conceptual, pattern-based, or a "how to"

Examples:
- *"What are common DTMF issues?"*
- *"How do we handle SMS delivery failures?"*
- *"What's the usual fix for WebRTC audio drops?"*

**Execution:**
1. ZenBot RAG runs as primary (vector search → GPT-4o)
2. Citation Enricher is already part of RAG — no extra call needed
3. Dobby PAI is not called (saves latency)

**Output:** Structured answer + ticket citations

---

### Path B — Specific / Live Query
**Triggers when:** question references a specific entity — call ID, phone number, log trace, message SID, user account, timestamp range

Examples:
- *"Why did call ID 4829 drop?"*
- *"Check the logs for +14155552671 from yesterday"*
- *"What happened with message SID SM123abc?"*

**Execution:**
1. Dobby PAI runs as primary (live lookup + agentic response)
2. Citation Enricher runs **in parallel** — ZenBot searches for similar historical incidents
3. Response Synthesizer merges both into: Dobby's live answer + "We've seen similar patterns in tickets #X, #Y"

**Output:** Live specific answer + historical context citations

---

## Why Not Simple Routing?

Simple routing (send to one OR the other) loses the citation layer whenever Dobby answers. The Citation Enricher solves this — it's a vector search that takes ~200ms and runs in parallel, so it costs almost nothing and ensures accountability is always present.

| Approach | Generic ✓ | Specific ✓ | Always Cited |
|---|---|---|---|
| Route to ZenBot only | ✅ | ❌ | ✅ |
| Route to Dobby only | ❌ | ✅ | ❌ |
| Simple A/B routing | ✅ | ✅ | ❌ |
| **This architecture** | ✅ | ✅ | ✅ |

---

## Components to Build

### 1. Intent Classifier
- **What:** Fast LLM call (GPT-4o-mini) that reads the query and returns `generic` or `specific`
- **Implementation:** Two-stage — rules first (regex for UUIDs, phone numbers, SIDs, numeric IDs), then LLM for ambiguous cases
- **Latency target:** <300ms (runs before anything else)
- **File:** `backend/classifier.py`

### 2. Dobby PAI Connector
- **What:** HTTP client that sends the query to Dobby's API and normalizes the response into ZenBot's format
- **Needs:** Dobby's endpoint URL, auth method (API key / JWT / internal only), request/response schema
- **File:** `backend/dobby_connector.py`

### 3. Citation Enricher
- **What:** Standalone async call to ZenBot's existing `search_qdrant()` — already implemented, just needs to be extracted to run independently
- **Runs:** In parallel with whichever primary engine is called
- **File:** Already in `backend/app.py` — refactor into `backend/retriever.py`

### 4. Response Synthesizer
- **What:** Short LLM prompt that merges the primary answer + citation context into one coherent response, with a source label ("Answered via ZenBot" / "Answered via Dobby + historical context")
- **File:** `backend/synthesizer.py`

### 5. Unified Orchestrator
- **What:** The new `/chat` endpoint that wires classifier → primary engine → citation enricher → synthesizer
- **Replaces:** The current `/query` endpoint (or sits alongside it)
- **File:** `backend/orchestrator.py`

---

## API Shape (Proposed)

### Request
```json
POST /chat
{
  "question": "Why did call ID 4829 drop?",
  "filters": {},
  "conversation_id": "optional-for-context"
}
```

### Response
```json
{
  "answer": "Call 4829 dropped due to...",
  "source": "dobby",
  "citations": [
    {
      "ticket_id": "36286",
      "subject": "DTMF API Not Consistent",
      "score": 0.82,
      "relevance": "Similar mid-call drop pattern"
    }
  ],
  "intent": "specific",
  "metadata": {
    "classifier_ms": 210,
    "primary_engine_ms": 1840,
    "citation_ms": 190,
    "total_ms": 2240
  }
}
```

---

## What We Need From Dobby

Before implementation can begin on the Dobby connector, we need:

- [ ] **Endpoint URL** — the base API URL for Dobby PAI
- [ ] **Auth mechanism** — API key, JWT, OAuth, or VPN-only
- [ ] **Request format** — how to send a query (body schema, headers)
- [ ] **Response format** — how the answer comes back (text, JSON, streaming?)
- [ ] **Slack integration** — does Slack currently hit Dobby directly, or through a middleware? If middleware, that's where the orchestrator should live instead of ZenBot

---

## Implementation Phases

### Phase 1 — Foundation
- [ ] Refactor `search_qdrant()` into standalone `retriever.py`
- [ ] Build `classifier.py` with rule-based detection + LLM fallback
- [ ] Write tests for classifier with real query samples

### Phase 2 — Dobby Integration
- [ ] Build `dobby_connector.py` once API details are confirmed
- [ ] Map Dobby's response schema to ZenBot's `Chunk` format
- [ ] Add timeout + fallback (if Dobby is down, fall back to ZenBot RAG)

### Phase 3 — Orchestration
- [ ] Build `orchestrator.py` with parallel async execution
- [ ] Build `synthesizer.py` for response merging
- [ ] Add `/chat` endpoint alongside existing `/query`

### Phase 4 — Interface
- [ ] Update ZenBot UI to show source label (ZenBot / Dobby / Hybrid)
- [ ] Add Slack bot connector if queries need to route through ZenBot
- [ ] Add confidence/intent display in UI

---

## Open Questions

1. Should Slack queries route through ZenBot's orchestrator, or does Dobby's Slack integration stay separate?
2. If Dobby is down, should we always fall back to ZenBot RAG or surface an error?
3. Should conversation history be maintained across turns (context window for multi-turn queries)?
4. Is there a latency SLA for responses in Slack vs the web UI?
