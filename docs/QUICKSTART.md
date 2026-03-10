# ZenBot Quick Start Guide 🚀

## ✅ System Status: ALL COMPONENTS RUNNING

Your ZenBot RAG chatbot is **fully operational** with all three interfaces ready to use!

---

## 🌐 Access Your Interfaces

### 1. Streamlit Web UI (Recommended for UAT)
```
🔗 http://localhost:8501
```
**Features:**
- Chat-style interface
- Real-time retrieval visualization
- Metadata filters (product, region, priority)
- Performance metrics dashboard
- Citation tracking

### 2. FastAPI Interactive Docs (For Developers)
```
🔗 http://localhost:8000/docs
```
**Try the endpoints:**
- GET `/stats` - Database statistics
- POST `/query` - Full RAG query
- POST `/search` - Raw semantic search

### 3. CLI Query Script (For Debugging)
```bash
python3 7_query_chatbot_gpt.py
```

---

## 🎯 Test It Now

### Option 1: Web UI (Easiest)

1. Open http://localhost:8501
2. Type a question in the chat box:
   - "What are common DTMF issues?"
   - "Why are SMS messages failing?"
   - "How do I fix voice call quality?"
3. Try filters in the sidebar:
   - Product: call
   - Region: emea
   - Priority: p1

### Option 2: API Call (curl)

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are DTMF issues?",
    "top_k": 5
  }' | python3 -m json.tool
```

### Option 3: CLI Script

```bash
python3 7_query_chatbot_gpt.py

💬 You: What are common DTMF issues?
💬 You: filter product=call
💬 You: exit
```

---

## 📊 Current Database Stats

- **Total chunks**: 4,377 indexed
- **Vector dimensions**: 3,072 (text-embedding-3-large)
- **Distance metric**: Cosine similarity
- **Database location**: `./qdrant_local_db/`

---

## ⚡ Performance Expectations

- **Embedding**: ~275ms
- **Search**: ~34ms
- **LLM Generation**: ~4,700ms
- **Total**: ~5 seconds per query

*Retrieval scores 0.5+ indicate good matches*

---

## 🛑 Stop Services

If you need to stop the services:

```bash
# Find and kill API server
lsof -i :8000
kill <PID>

# Find and kill Streamlit
lsof -i :8501
kill <PID>
```

Or restart with:
```bash
./start_zenbot.sh
```

---

## 📚 Documentation

- **Complete README**: `README_COMPLETE.md` - Full system documentation
- **API Reference**: http://localhost:8000/docs - Interactive API docs
- **Test Scripts**: `test_*.py` - Validation and debugging tools

---

## 🎓 Demo Flow for Stakeholders

**5-Minute Demo Script:**

1. **Open Streamlit UI** (http://localhost:8501)
   - "This is ZenBot, our AI support assistant that searches 4,377 historical tickets"

2. **Ask a question**: "What are common DTMF issues?"
   - "Notice how it retrieves relevant tickets and synthesizes an answer"
   - "All responses include citations to actual ticket IDs"

3. **Show filters**: Select "product: call" + "region: emea"
   - "We can narrow results by metadata to focus on specific issues"

4. **Expand metrics**: Click "📊 Query Metrics"
   - "Retrieval happens in 34ms, answer generation in ~5 seconds"
   - "Top score of 0.6+ means high relevance"

5. **Show chunks**: Click "🔍 View Retrieved Chunks"
   - "These are the actual ticket excerpts used to generate the answer"
   - "Green scores (0.7+) are excellent matches"

6. **Ask follow-up**: "How do I troubleshoot this issue?"
   - "Chat history is preserved for context"

---

## 🐛 Troubleshooting

### Issue: "API Not Available" in Streamlit

**Fix:**
```bash
# Check if API is running
curl http://localhost:8000/

# If not, start it:
python3 8_api_server.py &
```

### Issue: "Port already in use"

**Fix:**
```bash
# Kill existing process
lsof -i :8000
kill -9 <PID>

# Or use a different port
uvicorn 8_api_server:app --port 8001
```

### Issue: Poor search results (scores <0.5)

**Expected behavior:**
- If the question isn't in the knowledge base, scores will be low
- Try rephrasing the question
- Use filters to narrow scope

**Debug:**
```bash
python3 test_single_query.py  # Test raw search
```

---

## 🎯 Next Steps

### For UAT Testing
1. Gather support team for live demo
2. Prepare list of real questions from daily workflow
3. Test with filters (product, region, priority)
4. Collect feedback on:
   - Answer accuracy
   - Response time (is 5s acceptable?)
   - Missing features
   - Filter options needed

### After UAT Sign-Off
1. Build React frontend for production
2. Deploy to staging environment
3. Add authentication & rate limiting
4. Migrate Qdrant to server mode
5. Set up monitoring & logging

---

## 🏆 What You've Accomplished

✅ **Step 1: CLI Query Script** - Debugging interface ready
✅ **Step 2: FastAPI Backend** - REST API with full docs
✅ **Step 3: Streamlit UI** - Polished demo for UAT
✅ **Validated**: All endpoints tested and working
✅ **Database**: 4,377 chunks indexed and searchable
✅ **Performance**: <5s response time with citations

**Total build time**: ~2 hours from raw data to production-ready demo

---

## 💡 Pro Tips

**For Best Results:**
- Use specific questions: "Why are DTMF tones failing in EMEA?" vs "Tell me about DTMF"
- Combine filters: product=call + priority=p1 for focused results
- Check retrieval scores: 0.7+ is excellent, 0.5+ is good
- Review retrieved chunks to verify relevance
- Use citations to trace back to source tickets

**Performance Optimization:**
- Switch to `gpt-4o-mini` for 3x faster responses
- Reduce `top_k` to 3 for smaller context (faster, cheaper)
- Cache common questions (future enhancement)

---

**🎉 You're ready to demo! Open http://localhost:8501 and start asking questions.**
