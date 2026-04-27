# GenAI Interview Preparation — Comprehensive Q&A

---

## Table of Contents

- [GenAI Interview Preparation — Comprehensive Q\&A](#genai-interview-preparation--comprehensive-qa)
  - [Table of Contents](#table-of-contents)
  - [1. RAG (Retrieval-Augmented Generation)](#1-rag-retrieval-augmented-generation)
    - [Q1: What is RAG and why is it needed?](#q1-what-is-rag-and-why-is-it-needed)
    - [Q2: Walk me through a production RAG pipeline end-to-end.](#q2-walk-me-through-a-production-rag-pipeline-end-to-end)
    - [Q3: What are the different chunking strategies and their tradeoffs?](#q3-what-are-the-different-chunking-strategies-and-their-tradeoffs)
    - [Q4: What is Hybrid Search and why is it better than pure vector search?](#q4-what-is-hybrid-search-and-why-is-it-better-than-pure-vector-search)
    - [Q5: What is a Reranker and why use one?](#q5-what-is-a-reranker-and-why-use-one)
    - [Q6: What are common RAG failure modes and how do you fix them?](#q6-what-are-common-rag-failure-modes-and-how-do-you-fix-them)
    - [Q7: What is the "Lost in the Middle" problem?](#q7-what-is-the-lost-in-the-middle-problem)
    - [Q8: Explain Advanced RAG patterns.](#q8-explain-advanced-rag-patterns)
    - [Q9: How do you evaluate RAG systems?](#q9-how-do-you-evaluate-rag-systems)
    - [Q10: How do you handle multi-modal RAG (images, tables, charts)?](#q10-how-do-you-handle-multi-modal-rag-images-tables-charts)
  - [2. Vector Databases \& Embeddings](#2-vector-databases--embeddings)
    - [Q11: How do vector databases work internally?](#q11-how-do-vector-databases-work-internally)
    - [Q12: Compare vector database options.](#q12-compare-vector-database-options)
    - [Q13: What are embedding models and how do you choose one?](#q13-what-are-embedding-models-and-how-do-you-choose-one)
    - [Q14: What is Matryoshka Representation Learning (MRL)?](#q14-what-is-matryoshka-representation-learning-mrl)
    - [Q15: What is the difference between cosine similarity, dot product, and Euclidean distance?](#q15-what-is-the-difference-between-cosine-similarity-dot-product-and-euclidean-distance)
    - [Q16: How do you handle vector database scaling challenges?](#q16-how-do-you-handle-vector-database-scaling-challenges)
  - [3. Agentic AI \& Workflows](#3-agentic-ai--workflows)
    - [Q17: What is an AI Agent? How is it different from a chain?](#q17-what-is-an-ai-agent-how-is-it-different-from-a-chain)
    - [Q18: Explain the ReAct pattern.](#q18-explain-the-react-pattern)
    - [Q19: What is LangGraph and how does it differ from LangChain?](#q19-what-is-langgraph-and-how-does-it-differ-from-langchain)
    - [Q20: Explain multi-agent architectures.](#q20-explain-multi-agent-architectures)
    - [Q21: What is MCP (Model Context Protocol)?](#q21-what-is-mcp-model-context-protocol)
    - [Q22: How do you handle tool calling / function calling?](#q22-how-do-you-handle-tool-calling--function-calling)
    - [Q23: How do you prevent agents from going into infinite loops?](#q23-how-do-you-prevent-agents-from-going-into-infinite-loops)
    - [Q24: What is Human-in-the-Loop (HITL) in agentic systems?](#q24-what-is-human-in-the-loop-hitl-in-agentic-systems)
  - [4. LLM Fundamentals \& Prompt Engineering](#4-llm-fundamentals--prompt-engineering)
    - [Q25: Explain temperature, top-p, and other generation parameters.](#q25-explain-temperature-top-p-and-other-generation-parameters)
    - [Q26: What is Context Engineering?](#q26-what-is-context-engineering)
    - [Q27: What are common prompt engineering techniques?](#q27-what-are-common-prompt-engineering-techniques)
    - [Q28: How do you handle long conversations that exceed context windows?](#q28-how-do-you-handle-long-conversations-that-exceed-context-windows)
  - [5. Azure OpenAI \& Azure AI Search](#5-azure-openai--azure-ai-search)
    - [Q29: What are the advantages of Azure OpenAI over OpenAI directly?](#q29-what-are-the-advantages-of-azure-openai-over-openai-directly)
    - [Q30: Explain Azure AI Search architecture for RAG.](#q30-explain-azure-ai-search-architecture-for-rag)
    - [Q31: How does Azure AI Search handle vector compression?](#q31-how-does-azure-ai-search-handle-vector-compression)
    - [Q32: What is PTU vs. Pay-as-you-go in Azure OpenAI?](#q32-what-is-ptu-vs-pay-as-you-go-in-azure-openai)
  - [6. LLM Evaluation \& Guardrails](#6-llm-evaluation--guardrails)
    - [Q33: How do you evaluate LLM outputs in production?](#q33-how-do-you-evaluate-llm-outputs-in-production)
    - [Q34: What are guardrails and how do you implement them?](#q34-what-are-guardrails-and-how-do-you-implement-them)
    - [Q35: What is prompt injection and how do you defend against it?](#q35-what-is-prompt-injection-and-how-do-you-defend-against-it)
  - [7. Fine-Tuning vs. RAG vs. Prompt Engineering](#7-fine-tuning-vs-rag-vs-prompt-engineering)
    - [Q36: When should you fine-tune vs. use RAG vs. prompt engineering?](#q36-when-should-you-fine-tune-vs-use-rag-vs-prompt-engineering)
    - [Q37: What are the different fine-tuning approaches?](#q37-what-are-the-different-fine-tuning-approaches)
  - [8. Production Best Practices](#8-production-best-practices)
    - [Q38: How do you design a production GenAI system?](#q38-how-do-you-design-a-production-genai-system)
    - [Q39: How do you handle LLM reliability and fallback?](#q39-how-do-you-handle-llm-reliability-and-fallback)
    - [Q40: What observability do you need for GenAI systems?](#q40-what-observability-do-you-need-for-genai-systems)
    - [Q41: How do you optimize cost in GenAI applications?](#q41-how-do-you-optimize-cost-in-genai-applications)
    - [Q42: How do you handle multi-tenancy in GenAI systems?](#q42-how-do-you-handle-multi-tenancy-in-genai-systems)
  - [9. Advanced Topics](#9-advanced-topics)
    - [Q43: What is Context Caching / Prompt Caching?](#q43-what-is-context-caching--prompt-caching)
    - [Q44: What is Structured Output and why is it important?](#q44-what-is-structured-output-and-why-is-it-important)
    - [Q45: What is Semantic Caching?](#q45-what-is-semantic-caching)
    - [Q46: Explain the difference between Durable Functions and regular Azure Functions for AI workflows.](#q46-explain-the-difference-between-durable-functions-and-regular-azure-functions-for-ai-workflows)
    - [Q47: What is the difference between OpenAI Assistants API and custom agent frameworks?](#q47-what-is-the-difference-between-openai-assistants-api-and-custom-agent-frameworks)
    - [Q48: What are Mixture of Experts (MoE) models and why do they matter?](#q48-what-are-mixture-of-experts-moe-models-and-why-do-they-matter)
    - [Q49: What is the difference between Retrieval, Tool Use, and Code Execution in agents?](#q49-what-is-the-difference-between-retrieval-tool-use-and-code-execution-in-agents)
    - [Q50: How does your OrganAIze project work? (Be ready to explain your own project deeply)](#q50-how-does-your-organaize-project-work-be-ready-to-explain-your-own-project-deeply)
  - [10. Scenario-Based Questions](#10-scenario-based-questions)
    - [Q51: Design a RAG system for a large enterprise with 10M documents.](#q51-design-a-rag-system-for-a-large-enterprise-with-10m-documents)
    - [Q52: Your RAG system is returning irrelevant results. How do you debug?](#q52-your-rag-system-is-returning-irrelevant-results-how-do-you-debug)
    - [Q53: A user reports the AI agent performed an unintended action. How do you investigate?](#q53-a-user-reports-the-ai-agent-performed-an-unintended-action-how-do-you-investigate)
    - [Q54: How would you migrate a monolithic LLM application to an agentic architecture?](#q54-how-would-you-migrate-a-monolithic-llm-application-to-an-agentic-architecture)
  - [11. Quick-Fire Concepts](#11-quick-fire-concepts)
  - [12. Behavioral / Experience Questions (Based on Your Resume)](#12-behavioral--experience-questions-based-on-your-resume)
    - [Q55: Tell me about a time you improved a system using AI.](#q55-tell-me-about-a-time-you-improved-a-system-using-ai)
    - [Q56: How did you handle the AWS Lambda to Azure Functions migration?](#q56-how-did-you-handle-the-aws-lambda-to-azure-functions-migration)
    - [Q57: Describe your experience with multi-tenant systems.](#q57-describe-your-experience-with-multi-tenant-systems)

---

## 1. RAG (Retrieval-Augmented Generation)

### Q1: What is RAG and why is it needed?
**A:** RAG combines a retrieval system (fetching relevant documents from external knowledge) with a generative LLM. Instead of relying solely on the model's parametric knowledge (training data), RAG grounds responses in real, up-to-date, domain-specific data.

**Why needed:**
- LLMs have a knowledge cutoff date
- LLMs hallucinate when they lack information
- Fine-tuning is expensive and doesn't scale for frequently changing data
- RAG provides attributable, verifiable answers with source citations

### Q2: Walk me through a production RAG pipeline end-to-end.
**A:**
1. **Data Ingestion** — Collect documents (PDFs, DBs, APIs, web)
2. **Chunking** — Split documents into semantically meaningful chunks (recursive character, semantic, sentence-based)
3. **Embedding** — Convert chunks to vector representations using embedding models (e.g., `text-embedding-ada-002`, `text-embedding-3-large`)
4. **Indexing** — Store embeddings in a vector database (Azure AI Search, Pinecone, Weaviate, Qdrant)
5. **Query Processing** — User query → embed → similarity search (cosine, dot product) → retrieve top-k chunks
6. **Prompt Assembly** — Inject retrieved context into system/user prompt
7. **Generation** — LLM generates grounded response
8. **Post-processing** — Citation extraction, hallucination checks, guardrails

### Q3: What are the different chunking strategies and their tradeoffs?

| Strategy | Pros | Cons | Best For |
|----------|------|------|----------|
| **Fixed-size (token/char)** | Simple, predictable | Breaks mid-sentence, loses context | Uniform structured docs |
| **Recursive character** | Respects hierarchy (paragraphs → sentences) | May still break semantic units | General purpose (LangChain default) |
| **Sentence-based** | Preserves meaning boundaries | Short chunks, less context | FAQ, dialogue |
| **Semantic chunking** | Groups semantically similar content | Slower, needs embedding model | Complex docs with topic shifts |
| **Document-based** | Preserves full document context | Large chunks, token waste | Small documents, emails |
| **Agentic chunking** | LLM decides boundaries | Expensive, slow | High-value knowledge bases |

**Tradeoff:** Smaller chunks = better precision but lose context. Larger chunks = more context but may dilute relevance. Typical sweet spot: 256-512 tokens with 10-20% overlap.

### Q4: What is Hybrid Search and why is it better than pure vector search?
**A:** Hybrid search combines:
- **Vector/Semantic search** — captures meaning, handles synonyms and paraphrasing
- **Keyword/BM25 search** — exact match, handles specific terms, IDs, codes

**Why hybrid wins:**
- Pure vector search misses exact terms (e.g., error codes, product IDs)
- Pure keyword search misses semantic similarity
- Hybrid + **Reciprocal Rank Fusion (RRF)** merges both ranked lists
  - **How RRF works:** Each search method (vector and keyword) returns its own ranked list of results. RRF combines them by assigning each document a score based on its **rank position** (not raw score) in each list using the formula: `RRF_score = Σ 1/(k + rank_i)` where `k` is a constant (typically 60) and `rank_i` is the document's position in the i-th list. Documents appearing in multiple lists get boosted scores. This is **score-agnostic** — it doesn't care whether one system uses BM25 scores and the other uses cosine similarity, making it ideal for merging heterogeneous search results.
  - **Why not just average raw scores?** Vector search returns cosine similarity (0-1) while BM25 returns unbounded scores — they're on completely different scales. Normalizing them is fragile. RRF sidesteps this by only using rank positions.
  - **Example:** If "Doc A" is rank 1 in vector search and rank 5 in keyword search: `RRF = 1/(60+1) + 1/(60+5) = 0.0164 + 0.0154 = 0.0318`. A doc appearing in only one list gets a lower combined score.

**Azure AI Search** supports this natively with `search_type="hybrid"` + `semantic_reranker`.

### Q5: What is a Reranker and why use one?
**A:** A reranker is a cross-encoder model that takes (query, document) pairs and scores relevance more accurately than bi-encoder similarity.

**Flow:** Query → Retrieve top-50 via vector search → Rerank to top-5 → Send to LLM

**How it works — Bi-encoder vs Cross-encoder:**

| Aspect | Bi-encoder (Embedding Model) | Cross-encoder (Reranker) |
|--------|------------------------------|--------------------------|
| **Input** | Query and document encoded **separately** | Query and document encoded **together** as a single pair |
| **Output** | Two independent vectors → cosine similarity | Single relevance score (0-1) |
| **Attention** | No cross-attention between query & doc | Full cross-attention — every query token attends to every doc token |
| **Speed** | Fast (precompute doc embeddings once) | Slow (must run model for each query-doc pair) |
| **Accuracy** | Good | Significantly better |

**Step-by-step how a cross-encoder reranker works:**
1. **Concatenate** query and document into one input: `[CLS] query text [SEP] document text [SEP]`
2. **Pass through transformer** — all layers have full attention between query and document tokens, so the model can capture fine-grained interactions (e.g., negation, context-dependent meaning)
3. **Classification head** on the `[CLS]` token outputs a single relevance score
4. **Sort** all candidate documents by this score, take top-k

**Why cross-encoders are more accurate:**
- Bi-encoders compress an entire document into a single fixed vector — lossy. They can't model token-level interactions between query and document.
- Cross-encoders see both together, so they can reason about whether "Python" in the query matches "Python programming language" vs "Monty Python" in the doc based on full context.

**Why not just use cross-encoders for everything?**
- For 10M documents, a cross-encoder would need 10M forward passes per query — impossibly slow.
- So we use bi-encoders for **fast recall** (narrow 10M → 50 candidates) and cross-encoders for **precise reranking** (narrow 50 → 5).
- This **two-stage retrieval** pattern is the industry standard.

**Tradeoff:** Adds latency (100-300ms) but significantly improves answer quality. Worth it in production.

**Examples:** Cohere Rerank, Azure AI Search Semantic Ranker, BGE Reranker, Jina Reranker

### Q6: What are common RAG failure modes and how do you fix them?

| Failure | Cause | Fix |
|---------|-------|-----|
| **Irrelevant retrieval** | Poor chunking or embeddings | Better chunking, hybrid search, reranking |
| **Missing context** | Top-k too small, relevant doc not indexed | Increase k, improve ingestion coverage |
| **Hallucination despite context** | LLM ignores context or confabulates | Stronger system prompt, lower temperature, chain-of-thought |
| **Lost in the middle** | LLM ignores middle of long context | Put critical info at start/end, reduce context window |
| **Stale data** | Index not refreshed | Incremental indexing, CDC (Change Data Capture) |
| **Wrong granularity** | Chunks too big/small | Tune chunk size, add parent-child retrieval |

### Q7: What is the "Lost in the Middle" problem?
**A:** Research shows LLMs pay most attention to information at the **beginning** and **end** of the context window, and tend to ignore information in the **middle**. 

**Mitigation:**
- Place most relevant chunks first
- Use reranking to sort by relevance
- Reduce total context (fewer, better chunks)
- Use map-reduce or iterative refinement patterns

### Q8: Explain Advanced RAG patterns.

**1. Parent-Child / Hierarchical Retrieval:**
- Index small chunks (child) for precise retrieval
- Return the parent chunk (larger context) to the LLM
- Best of both worlds: precise search + rich context

**2. Multi-Query RAG:**
- LLM generates multiple reformulations of the user query
- Retrieve for each variant → merge and deduplicate results
- Handles ambiguous or complex queries

**3. HyDE (Hypothetical Document Embedding):**
- LLM generates a hypothetical answer
- Embed the hypothetical answer instead of the query
- Better embedding alignment with actual documents

**4. Self-RAG / Corrective RAG (CRAG):**
- LLM evaluates retrieved docs for relevance
- If irrelevant → re-retrieve or fall back to web search
- Self-reflective retrieval loop

**5. Contextual Compression:**
- After retrieval, compress/extract only relevant parts from each chunk
- Reduces token usage and noise

**6. Graph RAG:**
- Build a knowledge graph from documents
- Traverse graph relationships for multi-hop reasoning
- Better for "how does X relate to Y" questions

### Q9: How do you evaluate RAG systems?

**Metrics:**
| Metric | What it measures |
|--------|-----------------|
| **Context Relevance** | Are retrieved docs relevant to the query? |
| **Faithfulness/Groundedness** | Is the answer supported by the context? |
| **Answer Relevance** | Does the answer address the question? |
| **Context Precision** | Ratio of relevant docs in top-k |
| **Context Recall** | Were all needed docs retrieved? |
| **Latency** | End-to-end response time |
| **Token Efficiency** | Tokens used vs. answer quality |

**Tools:** RAGAS, DeepEval, Azure AI Evaluation SDK, LangSmith, custom LLM-as-judge

### Q10: How do you handle multi-modal RAG (images, tables, charts)?
**A:**
- **Tables:** Extract to markdown/structured format before chunking; use table-aware parsers (Azure Document Intelligence, Unstructured.io)
- **Images:** Use multi-modal embeddings (CLIP) or describe images via GPT-4o before indexing
- **Charts:** Convert to data tables + text descriptions
- **PDFs:** Use layout-aware extraction to preserve structure

---

## 2. Vector Databases & Embeddings

### Q11: How do vector databases work internally?
**A:** Vector DBs store high-dimensional vectors and enable efficient Approximate Nearest Neighbor (ANN) search.

**Key indexing algorithms:**

| Algorithm | How it works | Tradeoff |
|-----------|-------------|----------|
| **HNSW** (Hierarchical Navigable Small World) | Graph-based, multi-layer proximity graph | High recall, high memory, fast query |
| **IVF** (Inverted File Index) | Clusters vectors, searches nearest clusters | Lower memory, requires training, tunable |
| **PQ** (Product Quantization) | Compresses vectors into sub-codes | Very low memory, some accuracy loss |
| **ScaNN** | Anisotropic quantization | Google's approach, good accuracy-speed balance |
| **Flat/Brute Force** | Exact search, no index | Perfect recall, doesn't scale |

**Production choice:** HNSW is the most common default (Pinecone, Weaviate, Azure AI Search, pgvector all use it).

### Q12: Compare vector database options.

| Database | Type | Strengths | Weaknesses |
|----------|------|-----------|------------|
| **Azure AI Search** | Managed service | Hybrid search, semantic ranker, enterprise-grade, RBAC | Azure-only, cost at scale |
| **Pinecone** | Managed | Simple API, serverless option, fast | Vendor lock-in, limited filtering |
| **Weaviate** | Open-source | Multi-modal, GraphQL, modules | Operational overhead self-hosted |
| **Qdrant** | Open-source | Rust-based, fast, rich filtering | Smaller ecosystem |
| **ChromaDB** | Open-source | Simple, good for prototyping | Not production-grade at scale |
| **pgvector** | Postgres extension | Familiar SQL, joins with relational data | Slower ANN, limited scale |
| **FAISS** | Library (not DB) | Very fast, GPU support | No persistence, no API |

### Q13: What are embedding models and how do you choose one?

**Key dimensions:**
- **Dimensionality:** 384 (MiniLM) → 1536 (ada-002) → 3072 (text-embedding-3-large)
- **Context window:** How much text can be embedded at once
- **Multilingual support**
- **Cost and latency**

| Model | Dimensions | Best For |
|-------|-----------|----------|
| `text-embedding-3-large` | 3072 (reducible) | Highest quality, supports Matryoshka |
| `text-embedding-3-small` | 1536 | Cost-effective general purpose |
| `text-embedding-ada-002` | 1536 | Legacy, still widely used |
| Cohere embed-v3 | 1024 | Multilingual, compression |
| BGE / E5 | 768-1024 | Open-source, fine-tunable |
| all-MiniLM-L6-v2 | 384 | Fast, lightweight, local |

### Q14: What is Matryoshka Representation Learning (MRL)?
**A:** MRL trains embeddings so that **prefixes of the vector are also meaningful**. You can truncate a 3072-dim vector to 256 dims and still get reasonable similarity scores.

**Benefit:** Reduce storage by 90%+ with modest quality loss. `text-embedding-3-large` supports this natively via the `dimensions` parameter.

**Tradeoff:** Some accuracy loss at lower dimensions, but storage and speed gains are significant.

### Q15: What is the difference between cosine similarity, dot product, and Euclidean distance?

| Metric | Formula | When to use |
|--------|---------|-------------|
| **Cosine Similarity** | cos(θ) between vectors | Normalized vectors, most common for text |
| **Dot Product** | a·b | When magnitude matters (e.g., popularity) |
| **Euclidean (L2)** | √Σ(ai-bi)² | When absolute position matters |

**In practice:** Cosine similarity is standard for text embeddings. If vectors are normalized, cosine similarity = dot product.

### Q16: How do you handle vector database scaling challenges?

- **Sharding:** Distribute vectors across nodes by metadata (tenant, date)
- **Quantization:** PQ/SQ to reduce memory (8x-16x compression)
- **Tiered storage:** Hot vectors in memory, cold on disk
- **Filtering optimization:** Pre-filter (filter then search) vs. post-filter (search then filter)
- **Index tuning:** HNSW ef_construction, M parameters

**Pre-filter vs Post-filter tradeoff:**
- Pre-filter: Faster, but may miss relevant vectors outside filter
- Post-filter: Better recall, but searches more vectors (slower)

---

## 3. Agentic AI & Workflows

### Q17: What is an AI Agent? How is it different from a chain?
**A:**
- **Chain:** Fixed sequence of steps (prompt → LLM → tool → output). Deterministic flow.
- **Agent:** LLM decides **which tools to use, in what order, and when to stop**. Dynamic, non-deterministic flow.

**Agent = LLM + Tools + Memory + Planning/Reasoning Loop**

The key difference is **autonomy**: agents have a reasoning loop where the LLM observes, thinks, acts, and iterates.

### Q18: Explain the ReAct pattern.
**A:** **Re**asoning + **Act**ing. The LLM alternates between:
1. **Thought** — Reason about what to do next
2. **Action** — Call a tool/function
3. **Observation** — Process tool result
4. **Repeat** until the task is complete

```
Thought: I need to find the user's order status
Action: query_orders_db(user_id="123")
Observation: Order #456 shipped on Jan 5
Thought: I have the answer
Action: respond("Your order #456 was shipped on January 5th")
```

**Tradeoff:** More flexible than chains, but harder to control, more expensive (multiple LLM calls), and can get stuck in loops.

### Q19: What is LangGraph and how does it differ from LangChain?

| Aspect | LangChain | LangGraph |
|--------|-----------|-----------|
| **Paradigm** | Sequential chains, LCEL | Stateful graph (nodes + edges) |
| **Control flow** | Linear or branching | Cycles, conditional edges, parallel |
| **State** | Passed through chain | Explicit state object, checkpointing |
| **Best for** | Simple pipelines | Complex multi-step agents, multi-agent |
| **Human-in-the-loop** | Limited | First-class support (interrupt, approve) |
| **Persistence** | External | Built-in checkpointing |

**LangGraph key concepts:**
- **State:** Shared data structure across nodes
- **Nodes:** Functions that process state
- **Edges:** Transitions (conditional or fixed)
- **Checkpointing:** Save/restore state at any node
- **Human-in-the-loop:** `interrupt()` to pause for user input

### Q20: Explain multi-agent architectures.

**Patterns:**

**1. Supervisor/Orchestrator:**
- One agent routes tasks to specialist agents
- Supervisor decides who to call and synthesizes results
- Your OrganAIze project uses this pattern

**2. Hierarchical:**
- Layers of supervisors, each managing sub-agents
- Good for complex organizations of tasks

**3. Peer-to-peer / Swarm:**
- Agents communicate directly, no central controller
- Each agent decides when to hand off
- OpenAI Swarm pattern

**4. Pipeline:**
- Agents process sequentially, each adding to shared state
- Good for multi-stage processing (research → draft → review → edit)

**5. Debate/Critic:**
- Multiple agents argue/critique to improve output quality
- Generator + Critic pattern

**Tradeoffs:**
| Pattern | Pros | Cons |
|---------|------|------|
| Supervisor | Clear control, predictable | Bottleneck, single point of failure |
| Hierarchical | Scales complexity | Over-engineering for simple tasks |
| Peer-to-peer | Flexible, emergent behavior | Hard to debug, unpredictable |
| Pipeline | Simple, traceable | No backtracking, rigid |

### Q21: What is MCP (Model Context Protocol)?
**A:** MCP is an **open protocol** (by Anthropic) that standardizes how LLMs connect to external tools, data sources, and services. Think of it as **"USB-C for AI"** — a universal interface.

**Components:**
- **MCP Server:** Exposes tools/resources via a standard protocol
- **MCP Client:** The AI application that connects to servers
- **Tools:** Functions the LLM can call
- **Resources:** Data the LLM can read
- **Prompts:** Predefined prompt templates

**Why it matters:**
- Before MCP: Every tool integration was custom (different APIs, auth, formats)
- After MCP: Universal protocol, any client can connect to any server
- Ecosystem: 1000s of MCP servers for GitHub, databases, Slack, etc.

**Tradeoff vs Function Calling:**
| Aspect | Function Calling | MCP |
|--------|-----------------|-----|
| Standard | Provider-specific (OpenAI, Anthropic) | Open protocol |
| Discovery | Hardcoded in prompt | Dynamic tool discovery |
| Ecosystem | Build your own | Community servers |
| Complexity | Simpler for few tools | Better for many integrations |

### Q22: How do you handle tool calling / function calling?
**A:**
1. Define tool schemas (name, description, parameters with types)
2. Send to LLM with user message
3. LLM returns a tool call (function name + arguments)
4. Execute the function locally
5. Send result back to LLM
6. LLM generates final response

**Best practices:**
- Clear, descriptive tool names and parameter descriptions
- Limit tools to 10-20 per call (too many confuses the LLM)
- Validate tool arguments before execution (never trust LLM output)
- Handle tool errors gracefully (return error message, let LLM retry)
- Use `tool_choice="required"` when you must force a tool call

### Q23: How do you prevent agents from going into infinite loops?
**A:**
- **Max iterations:** Hard cap on reasoning loops (e.g., 10 steps)
- **Token/cost budget:** Track cumulative tokens, stop when exceeded
- **Timeout:** Wall-clock time limit
- **Loop detection:** Track (action, observation) pairs, detect repeats
- **Structured output:** Force specific response format to constrain behavior
- **Human-in-the-loop:** Require approval for sensitive actions

### Q24: What is Human-in-the-Loop (HITL) in agentic systems?
**A:** Inserting human checkpoints where the agent pauses for approval before executing critical actions.

**Implementation in LangGraph:**
```python
# Using interrupt()
def sensitive_node(state):
    action = plan_action(state)
    response = interrupt({"action": action, "reason": "Requires approval"})
    if response["approved"]:
        return execute(action)
```

**When to use HITL:**
- Financial transactions
- Data deletion/modification
- External communications (sending emails)
- Actions with side effects that can't be undone

---

## 4. LLM Fundamentals & Prompt Engineering

### Q25: Explain temperature, top-p, and other generation parameters.

| Parameter | What it does | Low value | High value |
|-----------|-------------|-----------|------------|
| **Temperature** | Controls randomness | Deterministic, focused | Creative, diverse |
| **Top-p (nucleus)** | Cumulative probability cutoff | Fewer token choices | More token choices |
| **Top-k** | Hard limit on token candidates | Conservative | Diverse |
| **Frequency penalty** | Penalize repeated tokens | Allow repetition | Reduce repetition |
| **Presence penalty** | Penalize tokens that appeared at all | Stay on topic | Explore new topics |
| **Max tokens** | Output length limit | Short responses | Long responses |

**Best practice:** For factual/RAG tasks: temperature=0-0.3. For creative tasks: temperature=0.7-1.0. Don't combine temperature and top-p aggressively.

### Q26: What is Context Engineering?
**A:** The practice of **designing and optimizing the entire context** that goes into an LLM call — not just the prompt, but the system message, retrieved documents, conversation history, tool results, and structured data.

**Components:**
1. **System prompt** — Role, rules, format instructions
2. **Retrieved context** — RAG results, relevant data
3. **Conversation history** — Previous turns (summarized or windowed)
4. **Tool results** — Output from function calls
5. **Examples** — Few-shot demonstrations
6. **Metadata** — User info, session context

**Key principles:**
- Put most important information at the start and end (Lost in the Middle)
- Be specific and structured (use XML tags, JSON, markdown headers)
- Minimize noise — only include relevant context
- Use delimiters to separate sections clearly

### Q27: What are common prompt engineering techniques?

| Technique | Description | Best For |
|-----------|-------------|----------|
| **Zero-shot** | No examples, just instructions | Simple tasks |
| **Few-shot** | Include examples in prompt | Pattern matching, formatting |
| **Chain-of-Thought (CoT)** | "Think step by step" | Reasoning, math |
| **Self-consistency** | Multiple CoT paths, majority vote | Complex reasoning |
| **Tree-of-Thought** | Branch and evaluate multiple reasoning paths | Planning, puzzles |
| **ReAct** | Reasoning + Acting with tools | Agentic tasks |
| **Structured output** | Force JSON/schema output | Data extraction, APIs |
| **Role prompting** | "You are an expert..." | Domain-specific tasks |

### Q28: How do you handle long conversations that exceed context windows?
**A:**
1. **Sliding window:** Keep last N messages
2. **Summarization:** Periodically summarize older messages
3. **Hybrid:** Keep recent messages + rolling summary of older ones
4. **Retrieval:** Embed conversation history, retrieve relevant parts
5. **Hierarchical memory:** Short-term (recent) + long-term (summaries) + episodic (key events)

**Tradeoff:** Window = simple but loses info. Summarization = preserves more but adds latency/cost. Retrieval = most flexible but complex.

---

## 5. Azure OpenAI & Azure AI Search

### Q29: What are the advantages of Azure OpenAI over OpenAI directly?

| Feature | Azure OpenAI | OpenAI Direct |
|---------|-------------|---------------|
| **Data privacy** | Data stays in your Azure region, not used for training | Data may be used (opt-out available) |
| **Compliance** | SOC2, HIPAA, ISO, FedRAMP | Limited compliance |
| **Networking** | Private endpoints, VNET | Public only |
| **RBAC** | Azure AD integration | API key only |
| **Content filtering** | Built-in, configurable | Basic moderation |
| **SLA** | Enterprise SLA | Best effort |
| **PTU** | Provisioned throughput (reserved capacity) | Not available |
| **Rate limits** | Per-deployment, adjustable | Per-organization |

### Q30: Explain Azure AI Search architecture for RAG.
**A:**
- **Index:** Schema defining fields, types, and behaviors (searchable, filterable, facetable)
- **Indexer:** Automated data ingestion from Azure data sources (Blob, SQL, Cosmos DB)
- **Skillset:** AI enrichment pipeline (OCR, entity extraction, embedding generation)
- **Vectorizer:** Built-in embedding generation at query time
- **Semantic Ranker:** L2 reranking using Microsoft's transformer model
- **Scoring profiles:** Custom relevance tuning

**Best practices:**
- Use hybrid search (vector + keyword) with semantic ranker
- Enable vector compression (scalar/binary quantization) for cost savings
- Use narrow data types and `stored: false` for fields not needed in results
- Implement security trimming with `security_filter` for multi-tenant

### Q31: How does Azure AI Search handle vector compression?
**A:**
- **Scalar Quantization:** float32 → int8 (4x compression, ~minimal quality loss)
- **Binary Quantization:** float32 → 1-bit (32x compression, needs oversampling + reranking)
- **Matryoshka truncation:** Reduce dimensions of MRL-compatible embeddings
- **`stored: false`:** Don't store original vectors if only searching (not retrieving)

**Combined:** Scalar quantization + stored:false can achieve 8x+ memory reduction.

### Q32: What is PTU vs. Pay-as-you-go in Azure OpenAI?

| Aspect | PTU (Provisioned) | Pay-as-you-go |
|--------|-------------------|---------------|
| **Billing** | Fixed hourly rate | Per 1K tokens |
| **Throughput** | Guaranteed, reserved | Best effort, shared |
| **Latency** | Consistent, lower | Variable |
| **Best for** | Steady, high-volume workloads | Bursty, unpredictable usage |
| **Cost** | Expensive if underutilized | Expensive at high volume |

---

## 6. LLM Evaluation & Guardrails

### Q33: How do you evaluate LLM outputs in production?
**A:**

**Automated metrics:**
- **Groundedness:** Is the response supported by provided context?
- **Relevance:** Does the response answer the question?
- **Coherence:** Is the response well-structured and logical?
- **Fluency:** Is the language natural and grammatically correct?
- **Similarity:** Semantic similarity to reference answer (if available)

**LLM-as-Judge:** Use a stronger model (GPT-4o) to evaluate a weaker model's output on rubrics.

**Human evaluation:** Gold standard but expensive. Use for calibrating automated metrics.

**A/B testing:** Compare system versions on real traffic.

**Tradeoff:** Automated = scalable but imperfect. Human = accurate but expensive. LLM-as-Judge = good middle ground but can have biases.

### Q34: What are guardrails and how do you implement them?
**A:** Safety mechanisms to ensure LLM outputs are safe, on-topic, and accurate.

**Types:**
1. **Input guardrails:** PII detection, prompt injection detection, topic classification
2. **Output guardrails:** Content filtering, factuality checking, format validation
3. **Structural guardrails:** Max token limits, rate limiting, cost caps

**Implementation approaches:**
- Azure Content Safety API
- NeMo Guardrails (NVIDIA)
- Guardrails AI framework
- Custom classifiers (fine-tuned small models)
- Regex/rule-based for format validation
- Constitutional AI principles in system prompt

### Q35: What is prompt injection and how do you defend against it?
**A:** An attack where malicious input tries to override the system prompt or manipulate the LLM.

**Types:**
- **Direct:** "Ignore previous instructions and..."
- **Indirect:** Malicious content embedded in retrieved documents

**Defenses:**
1. Input sanitization and validation
2. Separate system/user message roles properly
3. Use delimiters and XML tags for context boundaries
4. Prompt injection detection classifiers
5. Output validation (does response match expected format?)
6. Principle of least privilege for tools (agents can't execute destructive actions without approval)
7. Azure Content Safety prompt shields

---

## 7. Fine-Tuning vs. RAG vs. Prompt Engineering

### Q36: When should you fine-tune vs. use RAG vs. prompt engineering?

| Approach | Best For | Cost | Latency | Data Freshness |
|----------|---------|------|---------|----------------|
| **Prompt Engineering** | Style, format, simple tasks | Lowest | Lowest | Real-time (via context) |
| **RAG** | Knowledge-intensive, changing data | Medium | Medium | Near real-time |
| **Fine-tuning** | Specific style/tone, consistent format, domain jargon | High (training) | Lowest (no retrieval) | Static (retraining needed) |
| **RAG + Fine-tuning** | Best quality for domain-specific + fresh data | Highest | Medium | Near real-time |

**Decision framework:**
1. Try prompt engineering first (cheapest, fastest)
2. If knowledge-intensive → add RAG
3. If style/format consistency is critical → fine-tune
4. If both → fine-tune the model AND add RAG

### Q37: What are the different fine-tuning approaches?

| Method | What it does | Parameters trained | Cost |
|--------|-------------|-------------------|------|
| **Full fine-tuning** | Update all weights | All (billions) | Very high |
| **LoRA** | Low-rank adapter matrices | 0.1-1% of params | Low |
| **QLoRA** | LoRA + quantized base model | Same as LoRA | Very low |
| **Prefix tuning** | Learnable prefix tokens | < 0.1% | Very low |
| **RLHF** | Reinforcement learning from human feedback | Reward model + policy | Very high |
| **DPO** | Direct preference optimization (no reward model) | Full or LoRA | Medium |

**LoRA tradeoff:** Much cheaper and faster than full fine-tuning, slight quality gap for very specialized domains. Usually the best default choice.

---

## 8. Production Best Practices

### Q38: How do you design a production GenAI system?

**Architecture layers:**
1. **API Gateway** — Rate limiting, auth, load balancing (Azure APIM)
2. **Orchestration** — LangGraph/LangChain/Semantic Kernel for workflow
3. **LLM Layer** — Azure OpenAI with fallback models
4. **Retrieval Layer** — Azure AI Search with hybrid search
5. **Memory/State** — Redis/Cosmos DB for conversation state
6. **Evaluation** — Continuous monitoring of quality metrics
7. **Observability** — Tracing (LangSmith, Application Insights), logging
8. **Guardrails** — Input/output safety, content filtering

### Q39: How do you handle LLM reliability and fallback?
**A:**
- **Retry with exponential backoff** for transient failures (429, 500)
- **Model fallback:** GPT-4o → GPT-4o-mini → GPT-3.5-turbo
- **Region fallback:** East US → West US → Europe
- **Circuit breaker pattern:** Stop calling failed service, fallback to cached/degraded response
- **Timeout management:** Set appropriate timeouts, stream for UX
- **Queue-based load leveling:** Buffer requests during spikes

### Q40: What observability do you need for GenAI systems?
**A:**

**Tracing:** Every LLM call should log:
- Input tokens, output tokens, total cost
- Model used, temperature, parameters
- Latency (TTFT — Time to First Token, total)
- Retrieved documents and scores
- Tool calls and results
- Success/failure

**Metrics:**
- P50/P95/P99 latency
- Token usage and cost per request
- Error rates (LLM errors, tool errors, guardrail triggers)
- Quality scores (groundedness, relevance) on sample
- User satisfaction (thumbs up/down, explicit feedback)

**Tools:** LangSmith, Azure Application Insights, Weights & Biases, Phoenix (Arize)

### Q41: How do you optimize cost in GenAI applications?
**A:**
1. **Model selection:** Use cheapest model that meets quality bar (GPT-4o-mini for simple tasks)
2. **Caching:** Semantic cache for similar queries (Azure Redis + embeddings)
3. **Prompt optimization:** Shorter prompts, fewer examples
4. **Token management:** Limit max_tokens, truncate context
5. **Batching:** Batch API for non-real-time workloads (50% cheaper)
6. **Vector compression:** Reduce embedding dimensions and storage
7. **Streaming:** Don't wait for full response; stream to user
8. **PTU:** Reserved capacity for predictable workloads
9. **Request routing:** Route simple queries to smaller models

### Q42: How do you handle multi-tenancy in GenAI systems?
**A:**
- **Data isolation:** Separate indexes/collections per tenant or security filtering
- **Model isolation:** Separate deployments or shared with tenant-aware prompts
- **Rate limiting:** Per-tenant quotas and throttling
- **Cost tracking:** Per-tenant token and cost accounting
- **Prompt isolation:** Tenant-specific system prompts, prevent cross-tenant data leakage
- **RBAC:** Azure AD-based access control

---

## 9. Advanced Topics

### Q43: What is Context Caching / Prompt Caching?
**A:** Reusing the KV-cache of previously processed prompt prefixes to avoid redundant computation.

- **Anthropic:** Automatic prefix caching (cache_control breakpoints)
- **OpenAI:** Automatic for same prompt prefix
- **Benefit:** Up to 90% cost reduction and 80% latency reduction for repeated system prompts
- **Tradeoff:** Only works for identical prefixes; dynamic content at the beginning invalidates cache

**Best practice:** Put static content (system prompt, few-shot examples) at the beginning; dynamic content (user query, retrieved docs) at the end.

### Q44: What is Structured Output and why is it important?
**A:** Forcing LLM to output valid JSON conforming to a specific schema (JSON Schema/Pydantic).

**Methods:**
- `response_format: { type: "json_schema", json_schema: {...} }` (OpenAI)
- Pydantic models with LangChain's `with_structured_output()`
- Grammar-constrained decoding (Outlines, LMQL)

**Why important:**
- Reliable downstream parsing (no regex hacking)
- Type safety for tool arguments
- Consistent data extraction
- API contract enforcement

### Q45: What is Semantic Caching?
**A:** Instead of exact-match caching, use embedding similarity to find cache hits for semantically similar queries.

**Flow:**
1. Embed user query
2. Search cache (vector similarity)
3. If similarity > threshold → return cached response
4. Else → call LLM → cache result

**Tradeoff:** Risk of returning stale/wrong answers for queries that are similar but meaningfully different. Set similarity threshold carefully (0.95+).

### Q46: Explain the difference between Durable Functions and regular Azure Functions for AI workflows.
**A:** (Relevant to your resume — release notes automation)

| Aspect | Regular Functions | Durable Functions |
|--------|------------------|-------------------|
| **Execution** | Stateless, single invocation | Stateful, multi-step orchestration |
| **Timeout** | 5-10 min (consumption) | Days/weeks |
| **Patterns** | Request-response | Fan-out/fan-in, chaining, human interaction |
| **State** | External (DB, queue) | Built-in (Azure Storage) |
| **Best for AI** | Simple LLM calls | Multi-step agent workflows, long-running |

**Patterns used in AI workflows:**
- **Function chaining:** Document → Extract → Embed → Index
- **Fan-out/fan-in:** Process 100 documents in parallel, aggregate
- **Human interaction:** Wait for approval before publishing
- **Monitor:** Poll for completion of async AI operations

### Q47: What is the difference between OpenAI Assistants API and custom agent frameworks?

| Aspect | Assistants API | Custom (LangGraph/LangChain) |
|--------|---------------|------------------------------|
| **Setup** | Quick, managed | More code, more control |
| **Tools** | Code interpreter, file search, function calling | Anything you build |
| **State** | Managed threads | Self-managed |
| **Flexibility** | Limited to OpenAI's patterns | Full control |
| **Multi-agent** | Not supported | Full support |
| **Cost control** | Less transparent | Full visibility |
| **Vendor lock** | OpenAI only | Model-agnostic |

### Q48: What are Mixture of Experts (MoE) models and why do they matter?
**A:** MoE models (like GPT-4, Mixtral) route each token to a subset of "expert" sub-networks, not the full model.

**Benefits:**
- Much larger total parameters with similar compute cost
- Faster inference (only fraction of parameters active)
- Specialization per expert

**Tradeoff:** Higher memory (all experts in memory), routing overhead, harder to fine-tune.

### Q49: What is the difference between Retrieval, Tool Use, and Code Execution in agents?
**A:**
- **Retrieval:** Fetching relevant information from a knowledge base (RAG)
- **Tool Use:** Calling external APIs or functions (search, calculate, database query)
- **Code Execution:** Running generated code in a sandbox (data analysis, computation)

Each adds capability but also risk:
| Capability | Risk | Mitigation |
|-----------|------|------------|
| Retrieval | Irrelevant or poisoned docs | Reranking, source validation |
| Tool Use | Wrong API calls, data exposure | Schema validation, RBAC, approval |
| Code Execution | Arbitrary code execution | Sandboxing, no network, timeout |

### Q50: How does your OrganAIze project work? (Be ready to explain your own project deeply)
**A:** (From your resume) Self-organizing multi-agent framework using LangGraph and LiteLLM:

**Key architecture decisions to discuss:**
- **Dynamic agent spawning:** Supervisor analyzes task, spawns specialist agents on-demand
- **LiteLLM:** Unified API to call any LLM provider (cost optimization, model routing)
- **Parallel execution:** Independent sub-tasks execute concurrently
- **Budget controls:** Token tracking per agent, cumulative cost limits
- **Result synthesis:** Supervisor aggregates and synthesizes specialist outputs

**Be ready to discuss:**
- Why LangGraph over LangChain agents?
- How do you handle failures in spawned agents?
- How do you prevent cost runaway?
- How do you ensure deterministic behavior for testing?
- What's the latency profile? How do you optimize it?

---

## 10. Scenario-Based Questions

### Q51: Design a RAG system for a large enterprise with 10M documents.
**Think about:**
- Incremental indexing (not re-index everything)
- Tiered retrieval (metadata filter → vector search → rerank)
- Multi-index strategy (by department, document type)
- Security trimming (users see only authorized docs)
- Caching layer for common queries
- Async ingestion pipeline with monitoring
- Quality evaluation loop

### Q52: Your RAG system is returning irrelevant results. How do you debug?
**Steps:**
1. Check retrieved documents — are they relevant? (Retrieval problem)
2. If docs are relevant but answer is wrong — prompt/LLM problem
3. If docs are irrelevant — embedding quality? chunking? query?
4. Try the query directly in the vector DB — inspect scores
5. Compare vector search vs. keyword search results
6. Check for data quality issues (duplicate, stale, malformed chunks)
7. Test with reranking enabled/disabled
8. Log and compare across multiple queries to find patterns

### Q53: A user reports the AI agent performed an unintended action. How do you investigate?
**Steps:**
1. Pull the full trace — every LLM call, tool call, and state transition
2. Check the reasoning chain — why did the LLM choose that tool?
3. Check tool input validation — were arguments correct?
4. Check if the system prompt or context was manipulated (prompt injection)
5. Verify guardrails — did they fire? Were they bypassed?
6. Review the state at each checkpoint (LangGraph checkpoints)
7. Root cause: LLM error, tool error, missing guardrail, or data issue?
8. Fix: Add guardrail, fix prompt, add HITL for that action type

### Q54: How would you migrate a monolithic LLM application to an agentic architecture?
**Steps:**
1. Identify distinct capabilities (search, summarize, analyze, act)
2. Extract each as a tool with clear schema
3. Start with a single ReAct agent using existing tools
4. Add evaluation to measure quality vs. monolithic baseline
5. If complexity grows, split into specialist agents with supervisor
6. Add HITL for critical actions
7. Implement observability and cost tracking
8. Gradual rollout with A/B testing

---

## 11. Quick-Fire Concepts

| Concept | One-liner |
|---------|-----------|
| **Tokenization** | Breaking text into subword units (BPE, SentencePiece) |
| **Attention** | Mechanism allowing each token to weigh relevance of all other tokens |
| **Transformer** | Architecture using self-attention + feedforward layers |
| **KV Cache** | Cached key-value pairs from previous tokens to avoid recomputation |
| **TTFT** | Time to First Token — key UX latency metric |
| **Streaming** | Send tokens as generated, don't wait for complete response |
| **Grounding** | Connecting LLM responses to verifiable external data |
| **Hallucination** | LLM generating plausible but factually incorrect content |
| **Embedding** | Dense vector representation of text capturing semantic meaning |
| **Fine-tuning** | Additional training on domain-specific data |
| **RLHF** | Training with human preference feedback |
| **Distillation** | Training small model to mimic large model |
| **Quantization** | Reducing model precision (FP16→INT8→INT4) for speed/memory |
| **LoRA** | Low-rank adaptation — efficient fine-tuning |
| **Constitutional AI** | Self-critique and revision based on principles |
| **Chain-of-Thought** | Explicit reasoning steps before answering |
| **Few-shot** | Including examples in the prompt |
| **Zero-shot** | No examples, just instructions |
| **Token limit** | Maximum context window size (input + output) |
| **System prompt** | Instructions defining LLM behavior and constraints |

---

## 12. Behavioral / Experience Questions (Based on Your Resume)

### Q55: Tell me about a time you improved a system using AI.
**Answer framework (STAR):**
- **S:** Manual release notes taking 14+ hours per sprint across 20+ stakeholders
- **T:** Automate using Azure OpenAI
- **A:** Built Durable Functions pipeline: collect ADO work items → summarize with GPT → format → review → publish via Angular extension
- **R:** 80% reduction in effort, published as IP

### Q56: How did you handle the AWS Lambda to Azure Functions migration?
**Key points:**
- ~20 functions migrated
- Mapping Lambda triggers → Azure triggers (API Gateway→HTTP, SQS→Service Bus, S3→Blob)
- Handling cold start differences
- Authentication model changes (IAM → Azure AD/Managed Identity)
- Testing strategy for parity

### Q57: Describe your experience with multi-tenant systems.
**Key points:**
- Factory pattern for tenant-specific database routing
- Configurable connection pooling per tenant
- Data isolation at the database level
- Performance optimization per tenant's scale

---

*Prepared for GenAI interview — covers RAG, Vector DBs, Agentic AI, Azure OpenAI, LangGraph, MCP, production best practices, evaluation, security, and your specific experience.*
