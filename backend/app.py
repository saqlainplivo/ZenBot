"""
ZenBot FastAPI Server - REST API for Zendesk Ticket RAG

Exposes the query logic as a REST endpoint for UI integration.

Usage:
    pip install fastapi uvicorn
    uvicorn 8_api_server:app --reload --port 8000

Endpoints:
    GET  /               - Health check
    GET  /stats          - Database statistics
    POST /query          - Ask a question
    POST /search         - Raw semantic search (no LLM)
"""

import os
import time
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ───────────────────────────────────────────────────────────────
QDRANT_PATH = "../qdrant_local_db"
COLLECTION_NAME = "zendesk_tickets"
EMBED_MODEL = "text-embedding-3-large"
LLM_MODEL = "gpt-4o"
DEFAULT_TOP_K = 5

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant_client = QdrantClient(path=QDRANT_PATH)

# Initialize FastAPI
app = FastAPI(
    title="ZenBot API",
    description="RAG-powered Zendesk ticket assistant",
    version="1.0.0"
)

# CORS middleware (allow all origins for now — restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic Models ─────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., description="User's question", min_length=3)
    filters: Optional[Dict[str, str]] = Field(None, description="Metadata filters (e.g., {'product': 'sms'})")
    top_k: Optional[int] = Field(DEFAULT_TOP_K, ge=1, le=20, description="Number of chunks to retrieve")
    include_chunks: Optional[bool] = Field(True, description="Include retrieved chunks in response")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What are common DTMF issues?",
                "filters": {"product": "call"},
                "top_k": 5,
                "include_chunks": True
            }
        }


class SearchRequest(BaseModel):
    question: str = Field(..., description="Search query", min_length=3)
    filters: Optional[Dict[str, str]] = Field(None, description="Metadata filters")
    top_k: Optional[int] = Field(DEFAULT_TOP_K, ge=1, le=20)

    class Config:
        json_schema_extra = {
            "example": {
                "question": "DTMF not working",
                "filters": {"region": "emea"},
                "top_k": 5
            }
        }


class Chunk(BaseModel):
    score: float
    ticket_id: int
    chunk_id: str
    subject: str
    content: str
    product: Optional[str]
    issue_type: Optional[str]
    priority: Optional[str]
    region: Optional[str]
    status: Optional[str]


class QueryResponse(BaseModel):
    answer: str
    citations: List[int]
    chunks: Optional[List[Chunk]]
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    chunks: List[Chunk]
    metadata: Dict[str, Any]


class StatsResponse(BaseModel):
    collection_name: str
    total_chunks: int
    vector_dimensions: int
    distance_metric: str
    status: str


# ── Core Functions ──────────────────────────────────────────────────────────────

def embed_question(question: str) -> List[float]:
    """Embed user question using OpenAI."""
    response = openai_client.embeddings.create(
        model=EMBED_MODEL,
        input=question
    )
    return response.data[0].embedding


def search_qdrant(
    query_vector: List[float],
    top_k: int,
    filters: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """Search Qdrant for relevant chunks."""
    # Build filter
    qdrant_filter = None
    if filters:
        conditions = []
        for field, value in filters.items():
            conditions.append(
                FieldCondition(
                    key=field,
                    match=MatchValue(value=value)
                )
            )
        qdrant_filter = Filter(must=conditions)

    # Search
    results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
        query_filter=qdrant_filter,
        with_payload=True,
    ).points

    # Format
    chunks = []
    for r in results:
        chunks.append({
            "score": r.score,
            "ticket_id": r.payload.get("ticket_id"),
            "chunk_id": r.payload.get("chunk_id"),
            "subject": r.payload.get("subject"),
            "content": r.payload.get("content"),
            "product": r.payload.get("product"),
            "issue_type": r.payload.get("issue_type"),
            "priority": r.payload.get("priority"),
            "region": r.payload.get("region"),
            "status": r.payload.get("status"),
        })

    return chunks


def build_prompt(question: str, chunks: List[Dict[str, Any]]) -> tuple[str, str]:
    """Build system prompt and user message for GPT."""
    context_parts = []
    for chunk in chunks:
        context_parts.append(
            f"Ticket #{chunk['ticket_id']}: {chunk['subject']}\n"
            f"Product: {chunk['product']} | Issue: {chunk['issue_type']}\n"
            f"{chunk['content']}"
        )

    context = "\n\n".join(context_parts)

    system_prompt = """You are ZenBot, a Zendesk support assistant. Answer based ONLY on the provided ticket context.

RULES:
- Cite sources using [ticket_id] format (e.g., "According to [36286]...")
- If context doesn't answer the question, say "I don't have enough information in the ticket history."
- Be concise and actionable
- Synthesize information from multiple tickets when relevant"""

    user_message = f"""Context:\n{context}\n\nQuestion: {question}"""

    return system_prompt, user_message


def ask_gpt(system_prompt: str, user_message: str) -> str:
    """Query GPT-4o for answer."""
    response = openai_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.3,
        max_tokens=1024,
    )
    return response.choices[0].message.content


def extract_citations(answer: str) -> List[int]:
    """Extract ticket IDs from answer (format: [12345])."""
    import re
    citations = re.findall(r'\[(\d+)\]', answer)
    return sorted(set(int(c) for c in citations))


# ── Static Files ───────────────────────────────────────────────────────────────

# Mount static files
app.mount("/static", StaticFiles(directory="../static"), name="static")

# ── API Endpoints ───────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Serve the main HTML page."""
    return FileResponse("../static/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ZenBot API",
        "version": "1.0.0"
    }


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get database statistics."""
    try:
        info = qdrant_client.get_collection(COLLECTION_NAME)
        return {
            "collection_name": COLLECTION_NAME,
            "total_chunks": info.points_count,
            "vector_dimensions": info.config.params.vectors.size,
            "distance_metric": str(info.config.params.vectors.distance),
            "status": str(info.status)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Answer a question using RAG pipeline.

    Returns synthesized answer with citations and optional retrieved chunks.
    """
    start_time = time.time()

    try:
        # 1. Embed question
        embed_start = time.time()
        query_vector = embed_question(request.question)
        embed_time = time.time() - embed_start

        # 2. Search Qdrant
        search_start = time.time()
        chunks = search_qdrant(query_vector, request.top_k, request.filters)
        search_time = time.time() - search_start

        if not chunks:
            return QueryResponse(
                answer="I don't have any relevant information in the ticket history to answer that question.",
                citations=[],
                chunks=[],
                metadata={
                    "retrieval_count": 0,
                    "embed_time_ms": int(embed_time * 1000),
                    "search_time_ms": int(search_time * 1000),
                    "llm_time_ms": 0,
                    "total_time_ms": int((time.time() - start_time) * 1000)
                }
            )

        # 3. Generate answer
        llm_start = time.time()
        system_prompt, user_message = build_prompt(request.question, chunks)
        answer = ask_gpt(system_prompt, user_message)
        llm_time = time.time() - llm_start

        # 4. Extract citations
        citations = extract_citations(answer)

        return QueryResponse(
            answer=answer,
            citations=citations,
            chunks=[Chunk(**chunk) for chunk in chunks] if request.include_chunks else None,
            metadata={
                "retrieval_count": len(chunks),
                "top_score": chunks[0]["score"] if chunks else 0,
                "embed_time_ms": int(embed_time * 1000),
                "search_time_ms": int(search_time * 1000),
                "llm_time_ms": int(llm_time * 1000),
                "total_time_ms": int((time.time() - start_time) * 1000),
                "filters_applied": request.filters or {}
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Semantic search without LLM generation.

    Returns raw retrieved chunks for debugging or custom processing.
    """
    start_time = time.time()

    try:
        # 1. Embed question
        query_vector = embed_question(request.question)

        # 2. Search Qdrant
        chunks = search_qdrant(query_vector, request.top_k, request.filters)

        return SearchResponse(
            chunks=[Chunk(**chunk) for chunk in chunks],
            metadata={
                "retrieval_count": len(chunks),
                "top_score": chunks[0]["score"] if chunks else 0,
                "total_time_ms": int((time.time() - start_time) * 1000),
                "filters_applied": request.filters or {}
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# ── Startup Event ───────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Validate database connection on startup."""
    try:
        info = qdrant_client.get_collection(COLLECTION_NAME)
        print(f"✅ Connected to Qdrant: {info.points_count:,} chunks indexed")
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        raise


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
