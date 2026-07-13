# GenAI High-Level Design (HLD) — System Design Interview Questions

*Machine-learning system design for mid-to-senior GenAI / Applied AI Engineer roles. Each question walks through the **full request flow step-by-step** — what happens at each stage, how data transforms, and why each decision is made — so you can explain the system like you built it, not just name the boxes.*

---

## How to Approach a GenAI System Design Interview

Interviewers grade you on **structure and tradeoff reasoning**, not on naming the trendiest tool.

1. **Clarify requirements** — functional, non-functional (latency, scale, cost, quality), constraints (privacy, on-prem vs cloud).
2. **Define scale & SLAs** — QPS, users, corpus size, p95 latency, freshness, budget per query.
3. **Draw the high-level architecture** — ingestion path, serving path, data stores, model layer.
4. **Walk the request flow end-to-end** — this is where you win or lose. Trace one request through every hop, naming the data at each step.
5. **Deep-dive the core component** — usually retrieval, the agent loop, or the serving stack.
6. **Address quality & evaluation** — how you measure and improve output quality.
7. **Cover cross-cutting concerns** — cost, guardrails, observability, security, multi-tenancy.
8. **State tradeoffs** — every choice has a cost; call it out explicitly.

**Estimation anchors** (know these cold):
- Embedding: ~1536 dims × 4 bytes ≈ 6 KB per vector (float32); ~1.5 KB with int8 quantization.
- 10M chunks × 6 KB ≈ 60 GB raw vectors; with HNSW graph overhead ~1.5–2× → ~100 GB.
- LLM cost: rough order — GPT-4o-class ~$2.50–$10 per 1M tokens; mini-class ~$0.15–$0.60 per 1M tokens.
- Latency budget: embedding ~10–30 ms, vector search ~10–50 ms, rerank ~50–200 ms, LLM TTFT ~300–800 ms, generation ~30–100 tokens/sec.

---

## Table of Contents

1. [Design an Enterprise RAG Platform (10M+ documents)](#1-design-an-enterprise-rag-platform-10m-documents)
2. [Design a Customer Support AI Agent](#2-design-a-customer-support-ai-agent)
3. [Design a Multi-Tenant LLM Gateway / API Platform](#3-design-a-multi-tenant-llm-gateway--api-platform)
4. [Design a Real-Time AI Coding Assistant](#4-design-a-real-time-ai-coding-assistant)
5. [Design an LLM Inference Serving Platform](#5-design-an-llm-inference-serving-platform)
6. [Design a Semantic Search Engine](#6-design-a-semantic-search-engine)
7. [Design a Document Intelligence / Contract Analysis System](#7-design-a-document-intelligence--contract-analysis-system)
8. [Design a Multi-Agent Research / Workflow System](#8-design-a-multi-agent-research--workflow-system)
9. [Design an LLM Evaluation & Observability Platform](#9-design-an-llm-evaluation--observability-platform)
10. [Design a Content Moderation / Guardrails System](#10-design-a-content-moderation--guardrails-system)
11. [Design a Conversational Memory / Long-Term Memory System](#11-design-a-conversational-memory--long-term-memory-system)
12. [Design a Text-to-SQL / Natural Language BI System](#12-design-a-text-to-sql--natural-language-bi-system)
13. [Design a Fine-Tuning / Model Customization Pipeline](#13-design-a-fine-tuning--model-customization-pipeline)
14. [Design a Recommendation System with LLMs](#14-design-a-recommendation-system-with-llms)
15. [Cross-Cutting Concerns Cheat Sheet](#15-cross-cutting-concerns-cheat-sheet)

---

## 1. Design an Enterprise RAG Platform (10M+ documents)

> *The single most common GenAI HLD question. Master this and you can adapt it to most others.*

**Clarifying questions to ask:**
- What document types (PDF, HTML, Office, Confluence, tickets)? How often do they change?
- Read-heavy Q&A or also summarization/extraction? Single-turn or conversational?
- Freshness — must new docs be searchable in seconds or is hourly OK?
- Access control — per-user/per-group document permissions?
- Scale — corpus size, QPS, concurrent users, latency SLA, budget per query?

**Assumed requirements:** 10M docs, ~50M chunks, 100 QPS peak, p95 < 3s, per-document ACLs, hourly freshness.

**High-level architecture:**

```
INGESTION (async, batch + streaming)
Source connectors → Parser/OCR → Chunker → Embedder → Vector DB + Metadata store
                                              ↓
                                    (ACL tags, doc metadata)

SERVING (online)
User query → Auth → Query rewrite → Hybrid retrieval (vector + BM25)
           → ACL filter → Rerank → Context assembly → LLM → Guardrails → Response
                                                              ↓
                                                    Trace / eval logging
```

### Deep dive — Ingestion flow (how a document becomes retrievable)

Walk the interviewer through the life of one document:

1. **Trigger.** A connector detects a new/changed file (webhook from SharePoint, S3 event, or a scheduled crawl). It drops a message `{doc_id, source_uri, version, acl_tags}` onto an ingestion queue. Using a queue decouples spiky uploads from the (slow, GPU-bound) embedding stage and gives you retries + a dead-letter queue.
2. **Fetch + parse.** A worker pulls the message, downloads the raw bytes, and runs a **layout-aware parser** (e.g., Document Intelligence / Unstructured). Output is normalized text plus structure — headings, tables, page numbers. Scanned PDFs go through OCR. *Why it matters:* naive `pdf.extract_text()` destroys tables and reading order, which silently wrecks retrieval quality downstream.
3. **Chunk.** The normalized text is split into 300–500 token chunks with ~10–15% overlap, respecting structure (don't split mid-table or mid-section). Each chunk carries metadata: `{doc_id, chunk_id, section_path, page, acl_tags, source_uri, doc_version}`. *Why:* chunks are the unit of retrieval; too large dilutes relevance and wastes context tokens, too small loses the surrounding meaning.
4. **Embed.** Chunks are batched (e.g., 64 at a time) and sent to an embedding model, returning a vector per chunk (~1536 float32 = 6 KB). The **embedding model version is stored in metadata** so you know what to re-embed when you upgrade models.
5. **Index.** Vectors + metadata are upserted into the vector store (HNSW index) and, in parallel, the raw text is indexed into a BM25/inverted index for keyword search. The two indexes share the same `chunk_id`.
6. **Update/delete handling.** For a changed doc, you must delete old chunks (by `doc_id`) before inserting new ones, otherwise stale content lingers. This is why `doc_id → chunk_ids` mapping lives in the metadata store.
7. **Freshness.** With a queue + workers, end-to-end lag is typically seconds-to-minutes; "hourly freshness" is comfortably met. If you need seconds, prioritize a hot lane for high-priority sources.

### Deep dive — Query flow (how a question becomes an answer)

Trace one user query, naming the data at each hop:

1. **Auth & context.** Request arrives with `user_id`; you resolve the user's `acl_groups`. These become a **retrieval filter** so the user can never even retrieve a chunk they aren't allowed to see (security enforced at retrieval, not after generation).
2. **Query understanding / rewrite.** The raw query ("what's our refund window?") is often expanded or rewritten. For conversational RAG you also do **history-aware rewriting**: "and for electronics?" → "what is the refund window for electronics?" using the chat history. A small/cheap model does this. *Why:* the follow-up alone is un-retrievable; rewriting makes it self-contained.
3. **Embed the query.** The rewritten query is embedded with the *same model version* used for the corpus. Mismatched embedding models = garbage similarity.
4. **Hybrid retrieval (parallel).**
   - *Dense:* ANN search over the HNSW index returns top-K (say 50) chunks by cosine similarity — captures semantic matches ("refund" ≈ "money back").
   - *Sparse:* BM25 returns top-K by keyword overlap — captures exact terms, product codes, and rare tokens dense misses.
   - Both searches apply the **ACL filter** from step 1.
5. **Fusion.** The two ranked lists are merged with **Reciprocal Rank Fusion (RRF)** — a chunk ranked high in either list floats up. This gives a single candidate list of ~50 that's better than either method alone.
6. **Rerank.** A **cross-encoder** scores each (query, chunk) pair jointly and re-sorts, keeping the top 5. Unlike the bi-encoder embeddings (query and chunk encoded separately), the cross-encoder reads them together, so it's far more precise — it fixes cases where the vector was "close" but not actually relevant.
7. **Context assembly.** The top 5 chunks are formatted into the prompt with their citations, placed carefully (best chunks at the start and end to beat "lost in the middle"). A system prompt instructs: *"Answer only from the context; if the answer isn't present, say you don't know; cite sources."*
8. **Generation.** The assembled prompt goes to the LLM. Small model handles most; a router escalates complex/ambiguous queries to a frontier model. Tokens stream back for low TTFT.
9. **Output guardrails.** The response is checked for PII leakage, groundedness (does every claim trace to a retrieved chunk?), and policy. Citations are attached.
10. **Logging.** The full trace (rewrite → retrieved chunk_ids → rerank scores → prompt → output → tokens/cost/latency) is logged for evaluation and debugging.

**Key design decisions:**

| Component | Choice | Why |
|---|---|---|
| Ingestion | Event-driven queue + batch backfill | Decouple; handle spikes; reprocess on model change |
| Chunking | Structure-aware, 300–500 tokens, 10–15% overlap | Balance recall vs context noise |
| Embeddings | Dedicated model, versioned | Re-embed on model change; version in metadata |
| Vector store | HNSW (Azure AI Search / pgvector / Pinecone) | ANN for scale; hybrid support |
| Retrieval | Hybrid dense + BM25, RRF fusion | Dense misses exact terms; sparse misses semantics |
| Reranker | Cross-encoder top-50 → top-5 | Precision; fixes "lost in the middle" |
| Access control | ACL filter at query time | Never retrieve unauthorized docs |
| LLM | Small default, escalate to large | Cost/latency control |

**Scaling:**
- **Vector index:** shard by tenant or hash; replicas for read throughput. 50M × 6 KB ≈ 300 GB → shard across nodes.
- **Ingestion:** parallel workers, backpressure via queue depth, dead-letter queue for poison messages.
- **Caching:** semantic cache (by query-embedding similarity) for repeated questions; exact prompt cache.
- **Re-embedding:** model upgrade = re-embed whole corpus → blue/green index swap to avoid downtime.

**Quality & evaluation:** retrieval (recall@k, MRR, nDCG on a golden set); generation (faithfulness, answer relevance, citation accuracy via LLM-as-judge). Offline eval gates in CI; online A/B with 👍/👎.

**Common failure modes → fixes:**
- Irrelevant chunks → better chunking + reranker + hybrid.
- Hallucination → "answer only from context," require citations, lower temperature.
- Missing recent docs → check ingestion lag.
- Lost in the middle → rerank; place best chunks at edges; shrink context.

**Tradeoffs:** more retrieved context improves recall but raises cost, latency, and dilutes attention. Reranking adds latency but sharply improves precision. Managed vector DB ships faster; self-hosted (pgvector/Milvus) is cheaper at scale but more ops.

---

## 2. Design a Customer Support AI Agent

**Clarifying questions:** channels (chat/email/voice)? Actions allowed (refunds, order changes)? Human handoff? Languages? Compliance (PCI, PII)?

**Functional requirements:** answer product/policy questions (RAG), take actions via tools (order status, returns, refunds), escalate to a human, maintain conversation context.

**Architecture:**

```
User → Channel adapter → Session/Memory (Redis, TTL)
     → Orchestrator (agent loop)
         ├── Intent router
         ├── RAG tool (KB retrieval)
         ├── Action tools (order/return/refund APIs) — with HITL gate
         └── Escalation → human queue
     → Guardrails (PII redaction, policy) → Response → Trace + CSAT
```

### Deep dive — Conversation flow (one support session, turn by turn)

1. **Message in.** User sends "Where's my order? It's late." The channel adapter normalizes it and loads **session state** from Redis (last N turns + a rolling summary, keyed by `conversation_id`, 24h TTL). Context is now: history + new message.
2. **Guardrail (input).** Scan for PII and prompt injection. Redact/mask a card number if present before it ever reaches the model or logs.
3. **Intent routing.** A cheap classifier (or small LLM) labels the intent: `order_status`. This routing is the cost lever — most turns never touch the expensive model. Ambiguous or emotional messages route to the frontier model.
4. **Agent decides on a tool.** The orchestrator gives the LLM the message + available tool schemas. The model emits a **tool call**: `get_order_status(user_id, order_id?)`. If `order_id` is missing, the agent asks a clarifying question instead — no guessing.
5. **Tool execution.** The orchestrator (not the model) calls the real Order API with the user's scoped credentials (least privilege). The API returns structured JSON: `{status: "in_transit", eta: "2 days", carrier: ...}`.
6. **Grounded response generation.** The tool result is fed back into the model, which writes a natural, empathetic reply grounded in the actual data — no invented ETAs.
7. **High-risk action → HITL gate.** Suppose the user then demands a $200 refund. The agent proposes `issue_refund(order_id, 200)`, but a policy rule ("refunds > $100 require approval") **pauses** the workflow and routes it to a human agent's queue with full context. The human approves/denies; only then does the tool actually fire. Refund tools use **idempotency keys** so a retry never double-refunds.
8. **Escalation path.** If confidence is low, the user is frustrated across turns, or the intent is out of scope, the agent hands off to a human with a summary of what it already tried — no "start over."
9. **Output guardrails.** Before sending: check for prohibited content (no price promises, no competitor mentions), PII leaks, and policy. 
10. **Persist + measure.** Update session memory (append turn, refresh summary), log the trace, and capture CSAT signals for evaluation.

**Key decisions:** cheap-classifier routing; model tiering (mini for FAQ, frontier for complex); short-term memory in Redis + long-term user profile in a DB; HITL gate for money/destructive actions; guardrails; idempotent, least-privilege tools.

**Reliability:** fallback chain (primary model → secondary provider → canned "connect to human"); circuit breaker on tool failures; timeouts + retries with backoff.

**Metrics:** deflection rate, resolution rate, escalation rate, CSAT, cost/conversation, tool success rate.

**Tradeoffs:** more autonomy = higher deflection but more risk; HITL adds safety at the cost of latency and human load. Aggressive caching cuts cost but can serve stale policy answers.

---

## 3. Design a Multi-Tenant LLM Gateway / API Platform

> *An internal platform that lets many teams call LLMs safely, cheaply, and observably (an in-house LiteLLM/Portkey).*

**Requirements:** unified API across providers, per-tenant quotas & budgets, key management, caching, routing/fallback, logging, guardrails, PII handling.

**Architecture:**

```
Clients → API Gateway (authN/Z, rate limit)
        → LLM Gateway
            ├── Router (model selection, load balance, fallback)
            ├── Budget/quota enforcer (per tenant/project)
            ├── Semantic + exact cache
            ├── Guardrail middleware (in/out)
            ├── PII redaction
            └── Provider adapters (OpenAI, Azure, Anthropic, self-hosted)
        → Usage metering → Billing + Observability
```

### Deep dive — Request flow (one completion through the gateway)

1. **Auth.** Client sends a **virtual key** (per tenant/project), not the real provider key. The gateway resolves `tenant_id`, scopes, and allowed models. Real provider keys live in a vault and are never exposed to tenants.
2. **Rate limit & budget check.** A token-bucket limiter checks both **RPM and TPM** (tokens matter more than requests for LLMs). In parallel, the budget enforcer checks the tenant's remaining spend; if the cap is hit, it returns `429` immediately — before spending money.
3. **Normalize.** The request (which may be in any provider's format) is normalized to a canonical OpenAI-compatible schema so downstream logic is provider-agnostic.
4. **Cache lookup.** 
   - *Exact cache:* hash of (model, normalized prompt, params). Hit → return instantly, near-zero cost.
   - *Semantic cache:* embed the prompt, ANN-search prior prompts; if similarity > threshold, return the cached answer. This is where real savings come from on repetitive traffic — but the threshold must be tuned to avoid serving "almost right" answers.
5. **Input guardrails + PII.** Redact PII, run injection detection. Optionally the gateway can enforce org-wide policies centrally so every team inherits them.
6. **Routing.** The router picks a provider/deployment by policy: cost-based, latency-based, capability-based, or weighted round-robin across regions. It load-balances across multiple deployments to dodge per-deployment rate limits.
7. **Call + fallback.** The provider adapter translates to the provider's API and calls it, streaming tokens back. On `429`/`5xx`/timeout, the router **fails over** to the next provider in the chain transparently — the client sees one stable API.
8. **Output guardrails + meter.** Output is checked; then usage (prompt/completion tokens, latency, cost) is emitted **asynchronously** onto a metering queue so it never blocks the response path.
9. **Aggregate.** A consumer aggregates usage into billing/chargeback and observability dashboards, with per-request cost attribution by `tenant_id`.

**Key decisions:** provider-agnostic schema; token-bucket on RPM+TPM; vault-backed keys with scoped virtual keys; exact + semantic cache; async metering; multi-tenant isolation via `tenant_id` on every record + per-tenant quotas (noisy-neighbor protection).

**Scaling:** stateless gateway → horizontal scale behind an LB; Redis for cache + limiter counters; async metering via queue.

**Tradeoffs:** the gateway adds a hop and a potential SPOF (mitigate with HA + client-side local fallback). Semantic caching saves cost but risks near-miss answers — tune the threshold.

---

## 4. Design a Real-Time AI Coding Assistant

> *Copilot-style inline completions + chat.*

**Requirements:** low-latency inline completions (p95 TTFT < 300–500 ms), repo-aware context, chat mode, privacy (no code leakage), very high QPS.

**Architecture:**

```
Editor → Debounce/trigger → Context builder (open file, cursor, related files, symbols)
       → Prompt assembler (fill-in-the-middle) → Completion model (fast, small)
       → Post-filter (dedupe, license/secret scan) → Suggestion

Chat mode → Retrieval over repo (embeddings + symbol index) → Larger model → Answer
```

### Deep dive — Inline completion flow (from keystroke to ghost text)

1. **Trigger + debounce.** As the user types, the editor debounces (e.g., waits ~30–50 ms of no typing) so you don't fire a request per keystroke. A new keystroke **cancels the in-flight request** — no point completing stale context.
2. **Context building (the hard part).** Within a tight token budget you must pick the *most relevant* context: the code before the cursor (prefix) and after (suffix), plus snippets from related files. Relevance signals: recently edited files, imports/symbols referenced near the cursor, and a lightweight **repo embedding index** to pull semantically related code. This assembly quality is what makes suggestions feel "smart."
3. **Prompt assembly with FIM.** Completions aren't just "continue this text" — you need **fill-in-the-middle**: the model sees `<prefix> <cursor> <suffix>` and completes the hole. Sending only the prefix produces worse completions because the code after the cursor constrains the answer.
4. **Prefix caching.** The repo/context prefix is stable across keystrokes, so the serving layer reuses the **KV cache** for it and only processes the new tokens — big latency win.
5. **Fast model + streaming.** A small, low-latency model generates; tokens stream so the first characters appear almost immediately (TTFT is what users feel).
6. **Post-filter.** Before showing the suggestion: dedupe against what's already typed, scan for **secrets/API keys** and disallowed licensed code, and drop low-confidence completions.
7. **Feedback.** Acceptance/rejection is logged as the core quality signal (acceptance rate) and feeds model/context improvements.

**Chat mode flow** is essentially repo-scoped RAG: the question triggers retrieval over the repo (embeddings + a symbol/definition index), the relevant files/symbols are assembled into context, and a **larger** model reasons and answers — latency budget is looser than inline.

**Key decisions:** two model tiers (tiny for inline, large for chat); context assembly via recency + proximity + embeddings; FIM prompting; prefix/KV caching; on-prem/VPC deployment + secret scanning for privacy; completion caching keyed on (context hash, cursor).

**Scaling:** inline completions are extreme QPS → continuous batching + KV-cache reuse on the serving layer; autoscale GPU pool by queue depth.

**Tradeoffs:** bigger context = better suggestions but slower/pricier; aggressive triggering helps UX but wastes compute on discarded suggestions.

---

## 5. Design an LLM Inference Serving Platform

> *The infra-heavy version — serving open-weight models at scale.*

**Requirements:** serve open models (Llama-class), high throughput, low p95, streaming, autoscaling, multi-model.

**Architecture:**

```
Client → API/LB → Scheduler/Router
       → Inference workers (vLLM/TGI/TensorRT-LLM)
           ├── Continuous batching
           ├── PagedAttention (KV cache mgmt)
           ├── Tensor/pipeline parallelism (multi-GPU)
           └── Quantized weights (INT8/FP8/AWQ/GPTQ)
       → Stream tokens (SSE)
GPU autoscaler ← queue depth / GPU utilization
```

### Deep dive — Inference flow (from request to streamed tokens)

1. **Admission.** Request hits the router with prompt + sampling params. The router picks a worker hosting the right model (by GPU availability and, ideally, by which worker already has this prompt's prefix cached).
2. **Prefill phase.** The worker runs the full prompt through the model in one parallel pass to build the **KV cache** (the attention keys/values for every prompt token). This is compute-bound and produces the first token. TTFT ≈ prefill time.
3. **Continuous (in-flight) batching.** Instead of waiting to assemble a fixed batch, the scheduler lets **new requests join the running batch every step** and finished ones leave. GPUs stay saturated even with wildly different sequence lengths — the single biggest throughput win over naive static batching.
4. **Decode phase.** Tokens are generated one at a time; each step reads the growing KV cache. This is memory-bandwidth-bound. **PagedAttention** stores the KV cache in fixed-size pages (like OS virtual memory) so there's no fragmentation and memory is used efficiently — this is what lets vLLM pack many concurrent sequences.
5. **Prefix sharing.** If many requests share a system prompt, their KV-cache pages for that prefix are **shared**, computed once — great for high-fanout apps.
6. **Big-model parallelism.** If the model doesn't fit on one GPU, **tensor parallelism** splits each layer's matrices across GPUs (they sync every layer); **pipeline parallelism** puts different layers on different GPUs. Quantization (INT8/FP8/AWQ) shrinks weights so more fits and throughput rises with minor quality loss.
7. **Speculative decoding (optional).** A small draft model proposes several tokens; the big model verifies them in one pass. When the draft is right (often), you get 2–3× speedup for free.
8. **Stream out.** Tokens stream back over SSE as they're produced.
9. **Autoscaling.** The GPU pool scales on **queue wait time + GPU utilization**, not just CPU. A warm pool absorbs spikes because cold-starting a large model (load weights into VRAM) takes minutes.

**Tradeoffs:** throughput vs latency (bigger batches raise throughput but hurt p50); quantization saves cost but can dent quality; self-hosting is cheaper at high steady volume but demands serious MLOps — managed endpoints win for spiky/low volume.

---

## 6. Design a Semantic Search Engine

**Requirements:** search a large corpus, sub-100 ms latency, high relevance, typo tolerance, filters/facets, freshness.

**Architecture:**

```
INDEXING: Docs → Chunk → Embed + tokenize → Vector index (HNSW) + Inverted index (BM25) + Metadata
QUERY: Query → (spell correct, expand) → parallel [vector search, BM25]
       → RRF fusion → filter/facet → rerank (cross-encoder) → results
```

### Deep dive — Query flow (from typed query to ranked results)

1. **Query preprocessing.** Normalize, spell-correct ("iphon" → "iphone"), and optionally expand with synonyms. For semantic intent, also embed the corrected query.
2. **Parallel retrieval.** Fire dense (ANN over HNSW) and sparse (BM25) simultaneously.
   - **HNSW** navigates a multi-layer proximity graph: start at a sparse top layer, greedily hop toward the query vector, descend layers, and return the nearest neighbors — sub-linear, high recall, but RAM-hungry.
   - **BM25** scores by term frequency/inverse document frequency — nails exact tokens, product IDs, and rare words the embedding blurs.
3. **Filtering strategy.** If the user applied facets (brand, price), you choose **pre-filter** (restrict the ANN search to matching vectors — precise but can hurt recall/latency if the filter is very selective) vs **post-filter** (retrieve more, then drop non-matches — simpler, but you may retrieve too few after filtering). Senior answer: pick based on filter selectivity.
4. **Fusion.** Merge the two ranked lists with RRF into one candidate set (~top 100).
5. **Rerank.** A cross-encoder rescoring the top candidates jointly with the query gives the final precise ordering; optionally blend business signals (popularity, recency, margin) via learning-to-rank.
6. **Assemble results.** Attach highlights/snippets and facet counts; return.
7. **Freshness path.** New/updated docs flow through a lightweight near-real-time write path (append to both indexes) separate from periodic bulk reindexing, so search stays current without full rebuilds.

**Scaling:** shard by doc range/hash; replicas for QPS; hot (recent) vs cold tiers.

**Tradeoffs:** HNSW is fast but RAM-hungry and slow to rebuild; IVF-PQ compresses memory but loses precision. Pre- vs post-filtering trades recall against latency.

---

## 7. Design a Document Intelligence / Contract Analysis System

**Requirements:** ingest complex PDFs/DOCX (tables, signatures, layouts), extract structured fields, answer questions, cite sources, strict ACLs and audit.

**Architecture:**

```
Upload → Layout parser/OCR → Structure-aware chunking (sections/clauses)
       → Embed + entity extraction → Vector store + structured DB (fields)
Query → Retrieve (hybrid, ACL-filtered) → LLM extract/answer with mandatory citations
       → Human review for low-confidence → Audit log
```

### Deep dive — Extraction & query flow (contract in, cited answer out)

1. **Ingest + parse.** A contract PDF is run through layout-aware OCR that preserves reading order, tables, and the section/clause hierarchy. Output: structured text with `page` and `section_path` for every block.
2. **Hierarchical chunking.** Split along the natural hierarchy (Article → Section → Clause), keeping the path in metadata. This is what enables precise citations later ("Section 7.2, page 4").
3. **Dual write.** 
   - *Unstructured path:* embed each clause → vector store for semantic Q&A.
   - *Structured path:* an extraction LLM emits **JSON-schema output** for known fields (parties, effective date, liability cap, renewal terms) with a **confidence score** per field → structured DB.
4. **Confidence gating.** Fields below a confidence threshold are routed to a **human reviewer** queue. Their corrections become labeled data — a flywheel that improves extraction over time.
5. **Query.** A lawyer asks "What's the liability cap?" The query is embedded and retrieved with an **ACL filter** (they may only see cases they're assigned to — enforced at retrieval).
6. **Grounded answer with mandatory citations.** The LLM answers strictly from retrieved clauses and must cite `doc + page + clause`. In legal/finance, an uncited answer is unusable, so the guardrail rejects responses lacking citations.
7. **Audit.** Every query, retrieved clauses, and answer is written to an immutable audit log for compliance.

**Tradeoffs:** high accuracy needs expensive parsing + human review; you trade throughput/cost for correctness — the right call in legal/finance.

---

## 8. Design a Multi-Agent Research / Workflow System

> *Orchestrating specialized agents (planner, researcher, writer, critic).*

**Requirements:** decompose complex tasks, coordinate agents, use tools, converge reliably, control cost/loops.

**Architecture (orchestrator–worker):**

```
User goal → Orchestrator/Planner (decomposes into subtasks)
          → dispatch to Worker agents (parallel where possible)
              ├── Researcher (web/RAG search)
              ├── Analyst (code execution / data)
              └── Writer (synthesis)
          → Critic/Verifier (checks output) → loop or finalize
          → Shared memory/state (blackboard) + trace
```

### Deep dive — Orchestration flow (goal to verified deliverable)

1. **Plan.** The orchestrator receives "Write a competitive analysis of X." A planner LLM decomposes it into an explicit task graph: `[research competitors] → [gather our data] → [synthesize] → [critique]`. Modeling this as a **state machine/graph (LangGraph-style)** — nodes = steps, edges = transitions, with checkpoints — beats a free-form "keep prompting until done" loop for reliability and debuggability.
2. **Dispatch (fan-out).** Independent subtasks run in **parallel**: the researcher agent does web/RAG search on each competitor while the analyst pulls internal metrics. Each worker gets a narrow prompt + only the tools it needs.
3. **Tool use per worker.** The researcher issues search queries, reads results, and writes findings to **shared state (a blackboard)** keyed by subtask. Workers communicate through this shared state, not by cramming everything into one context window.
4. **Join + synthesize.** Once dependencies complete, the writer agent reads the blackboard and drafts the analysis.
5. **Critique loop.** A **critic/verifier** agent checks the draft against the goal and evidence. If it finds gaps ("missing pricing comparison"), it emits a revision request and the graph loops back to the relevant node — but under a **max-steps + budget cap** with repetition detection so it can't loop forever.
6. **HITL checkpoints.** For high-stakes outputs, the graph pauses for human approval at defined nodes.
7. **Durability.** Because these workflows are long-running, state is **checkpointed** after each node so a crash/restart resumes instead of restarting (durable execution).
8. **Finalize + trace.** On critic approval, return the deliverable; the full multi-agent trace is logged for cost analysis and debugging.

**Failure handling:** per-agent timeouts, retries, and graceful degradation (return partial results with caveats).

**Tradeoffs:** more agents = more capability but more cost, latency, and coordination failure modes. Explicit graphs reduce flexibility but massively improve reliability and debuggability. Avoid fully autonomous swarms in production.

---

## 9. Design an LLM Evaluation & Observability Platform

**Requirements:** trace every LLM call, measure quality offline + online, catch regressions, monitor cost/latency/drift.

**Architecture:**

```
App (instrumented) → Trace collector (spans: prompt, retrieval, tools, response, tokens, cost)
                    → Trace store (OLAP) + Dashboards
Offline eval: Golden datasets → run pipeline → LLM-as-judge + metrics → CI gate
Online: user feedback (👍/👎), implicit signals → aggregate → alerts on regression/drift
```

### Deep dive — Two flows: tracing (online) and evaluation (offline)

**Online tracing flow:**
1. The app is instrumented so each LLM interaction emits a **trace** with nested spans: `query_rewrite → retrieval (with chunk_ids + scores) → rerank → prompt → LLM (tokens, cost, latency) → tools → guardrails`. Think OpenTelemetry for LLM chains.
2. Traces stream to a collector and land in an OLAP store powering dashboards (cost/latency/volume by tenant, model, route).
3. **Online quality:** users leave 👍/👎 and implicit signals (edits, copies, follow-ups). A **sample** of production traffic is auto-scored by an LLM judge. Drift detectors watch input/output distributions and fire alerts on regressions.

**Offline evaluation flow (the CI gate):**
1. Maintain **versioned golden datasets** (inputs + reference answers / rubrics), including hard cases mined from production failures.
2. On every prompt/model/config change, run the whole pipeline over the golden set.
3. Score with metrics — faithfulness, answer relevance, correctness, safety — using **LLM-as-judge with a rubric**, calibrated against human labels (LLM judges are noisy/biased, so you spot-check).
4. **Gate the deploy:** if scores drop below threshold vs the current baseline, block the release. Optionally **replay real production traces** against the new version to catch regressions before rollout.
5. Passing changes go to an **online A/B test** to confirm the offline win holds with real users.

**Tradeoffs:** LLM-as-judge scales but is noisy — calibrate with humans. Full tracing has storage cost — sample high-volume traffic.

---

## 10. Design a Content Moderation / Guardrails System

**Requirements:** block unsafe input/output (toxicity, PII, prompt injection, jailbreaks, policy violations) with low latency and low false positives.

**Architecture:**

```
Input → Input guardrails (PII, injection, topic/policy classifier)
      → LLM
      → Output guardrails (toxicity, PII leak, groundedness, policy) → allow / block / rewrite
      → Log violations for audit + tuning
```

### Deep dive — Guardrail flow (layered defense on both sides of the model)

---

## 16. Design a Semantic Cache for LLM Responses

> *A cost + latency lever that sits in front of the model. Instead of matching queries by exact string, it matches by **meaning** — so "What's your refund policy?" and "How do I get my money back?" hit the same cached answer.*

**Why it matters:** LLM calls are the most expensive and slowest hop in the stack. In production, a large fraction of traffic is semantically repetitive (FAQs, popular prompts). A cache hit turns a ~800 ms, $0.01 LLM call into a ~20 ms, near-free vector lookup. This is the single highest-ROI optimization for read-heavy GenAI apps.

**Clarifying questions to ask:**
- What's the hit-rate potential — FAQ-style traffic (high) or long-tail unique prompts (low)?
- How stale can an answer be? (Pricing/inventory = seconds; general knowledge = days.)
- Is the answer a pure function of the prompt, or does it depend on **per-user context / RAG documents / tools**? (Determines the cache key.)
- What's the cost of a **wrong** cache hit (returning a semantically-close but incorrect answer)? This sets your similarity threshold.
- Multi-tenant? Then cache must be namespaced per tenant to avoid cross-tenant leakage.

**Assumed requirements:** 1000 QPS, target ≥40% hit rate, p95 < 50 ms on hits, per-tenant isolation, configurable TTL, tunable similarity threshold.

**High-level architecture:**

```
Query → Embed query → Vector similarity search (cache index)
      │
      ├── HIT  (top-1 score ≥ threshold) → validate (TTL, ACL, tenant) → return cached answer
      │
      └── MISS (no candidate ≥ threshold) → LLM → store {embedding, answer, metadata}
                                                 → return answer

Eviction: TTL expiry + LRU/LFU on capacity
Invalidation: on source-data change, purge affected entries
```

### Deep dive — Request flow (how a query becomes a hit or a miss)

1. **Normalize.** Lowercase, trim, strip volatile tokens (timestamps, IDs). This raises the hit rate before you even embed.
2. **Embed the query.** Run the incoming prompt through the same embedding model used to index the cache (e.g. 1536-dim vector). The embedding **is** the cache key — semantics, not the raw string.
3. **Similarity search.** Query the vector index (ANN, e.g. HNSW) for the top-1 (or top-k) nearest cached entries by cosine similarity.
4. **Threshold decision.** If `top1_score ≥ threshold` (e.g. cosine ≥ 0.92) → **candidate hit**; else → **miss**. The threshold is the core knob: too low → wrong answers served; too high → low hit rate. Tune it against a labeled set of paraphrase pairs.
5. **Validate the hit.** A candidate isn't served blindly. Check:
   - **TTL** — is the entry still fresh?
   - **Tenant / ACL** — does this entry belong to the requesting tenant and is the user allowed to see it?
   - **Context match** — if the answer depended on user context or RAG doc versions, confirm those still match (store a context hash in metadata).
   Passing all → return cached answer, record a hit.
6. **On miss.** Call the LLM, get the answer, then **write back**: store `{query_embedding, response, tenant_id, context_hash, created_at, ttl, hit_count}`. Return the fresh answer.
7. **Async hit-quality sampling.** A small % of hits are re-scored (LLM-as-judge or by actually calling the model and comparing) to detect the threshold drifting into "wrong answer" territory.

### Data structures — what powers each operation

| Concern | Structure | Why |
|---|---|---|
| **Semantic lookup** | **Vector index (HNSW / IVF-PQ ANN)** in a vector DB (Redis-VSS, Milvus, pgvector, FAISS) | O(log n)-ish approximate nearest-neighbor by cosine; the heart of "match by meaning". |
| **Entry storage / metadata** | **Hash map** `cache_id → {response, tenant, context_hash, created_at, ttl, freq}` (Redis hash / KV) | O(1) fetch of the full record once ANN returns the id. |
| **TTL expiry** | **Min-heap / priority queue** keyed by `expire_at`, or the store's native TTL | Efficiently evict the soonest-to-expire; native TTL avoids a background sweeper. |
| **Capacity eviction (LRU)** | **Doubly-linked list + hash map** (classic O(1) LRU) | Evict least-recently-used when at capacity; move-to-front on hit. |
| **Capacity eviction (LFU)** | **Frequency buckets / min-heap on `hit_count`** | Keep the *popular* FAQ answers, drop one-off long-tail queries. |
| **Invalidation by source** | **Inverted index** `doc_id → [cache_ids]` | When a source doc changes, purge exactly the cache entries derived from it. |
| **Exact-match fast path** | **Hash of normalized prompt → cache_id** | Skip the embedding + ANN cost entirely when the prompt is byte-identical. |

A production cache is a **two-layer lookup**: an exact-match hash map (cheap, catches identical repeats) in front of the vector index (semantic, catches paraphrases).

### Eviction & invalidation

- **TTL** — every entry expires; short for volatile domains, long for stable knowledge.
- **LRU/LFU** — bound memory; LFU is usually better here because cache value follows a power-law (a few FAQs dominate).
- **Explicit invalidation** — on a source-data or prompt-template change, purge affected entries via the inverted index. Stale cache = silently wrong answers, so invalidation correctness matters more than hit rate.

### Correctness guardrails (the dangerous part)

The risk unique to semantic caching: **a near-neighbor is not always the same question.** "How do I *cancel* my subscription?" vs "How do I *change* my subscription?" can sit above a loose threshold yet need different answers. Mitigations:
- Conservative threshold + offline calibration on paraphrase/near-miss pairs (measure hit precision, not just rate).
- Never cache answers that depend on **fast-changing or user-specific state** unless the key includes that state (context hash, user id).
- Sample hits for quality; auto-lower the threshold or purge on detected regressions.

### Scaling & multi-tenancy

- **Namespace per tenant** (separate index or a mandatory `tenant_id` filter) — prevents cross-tenant answer leakage and keeps each tenant's neighbors relevant.
- **Sharded vector index** by tenant/hash for horizontal scale; replicas for read throughput.
- **Distributed KV (Redis cluster)** for the metadata + exact-match layer.

### Tradeoffs

- **Hit rate vs correctness** — the similarity threshold trades one directly against the other; there's no free lunch. Pick based on the cost of a wrong answer.
- **Freshness vs cost savings** — aggressive TTL = fewer stale answers but a lower hit rate.
- **Extra embedding call on every request** — you pay one embedding (~10–30 ms, cheap) to potentially save one LLM call (~800 ms, expensive); net win whenever hit rate is non-trivial.
- **Memory footprint** — storing embeddings + responses costs RAM; bound it with LFU eviction and int8-quantized vectors.
- **Best fit:** FAQ/support bots, popular-prompt workloads. **Poor fit:** highly personalized, real-time, or long-tail-unique traffic where hit rates stay low.

1. **Cheap-first input checks.** Run fast, deterministic filters before spending model tokens: regex/allow-lists for obvious cases, a **PII detector** (redact card/SSN), and a **prompt-injection/jailbreak classifier**. Untrusted content (retrieved docs, tool output) is wrapped in delimiters and demoted below system instructions (**instruction hierarchy**) so it can't override rules.
2. **Parallel expensive checks.** Heavier LLM-based policy/topic classification runs **in parallel** with the cheap checks (not serially) to protect latency; only escalate to it when the cheap filters are uncertain.
3. **Decision.** Based on severity, the system chooses an action: allow, **block** (refuse), **redact** (mask PII), **rewrite** (soften), or **route to human**. Thresholds are configurable per use case.
4. **Model call.** If allowed, the (possibly sanitized) prompt goes to the LLM.
5. **Output checks.** The response passes a second gauntlet: toxicity classifier, PII/secret scanner (did it leak training or retrieved PII?), and — for RAG — a **groundedness check** verifying claims trace to retrieved context. Independent checks run in parallel.
6. **Act + log.** Enforce the output decision and log every violation with the triggering content for audit and for **tuning thresholds** over time.

**Tradeoffs:** stricter guardrails reduce risk but raise false positives (blocking valid content) and latency. Tune per use case; log everything for continuous improvement.

---

## 11. Design a Conversational Memory / Long-Term Memory System

**Requirements:** remember user facts and past conversations across sessions, retrieve relevant memories, respect context limits, allow forgetting.

**Architecture:**

```
Turn → Short-term buffer (recent messages)
     → Summarizer (rolling summary when buffer grows)
     → Memory extractor (salient facts) → Long-term store (vector + structured)
Retrieval: query → fetch relevant memories (vector search + recency) → inject into prompt
```

### Deep dive — Memory flow (write path and read path)

**Write path (after each turn):**
1. Append the new turn to the **working-memory buffer** (recent messages, in Redis).
2. When the buffer exceeds a token budget, a **rolling summarizer** compresses older turns into a running summary — full transcript is kept separately for recall, but the prompt only carries the summary + recent turns.
3. Asynchronously, a **memory extractor** pulls salient durable facts ("prefers window seats," "allergic to peanuts") and writes them to long-term stores: a **vector store** for episodic/semantic recall and a **structured KV/graph store** for stable user facts. Extraction is async so it never slows the response.
4. **Conflict resolution:** if a new fact contradicts an old one ("now prefers aisle"), dedupe and update rather than storing both.

**Read path (start of a turn):**
1. From the incoming message, retrieve candidate memories by **hybrid scoring**: semantic similarity (vector search) + recency + an importance weight.
2. Select the top few that fit the memory token budget and **inject** them into the prompt alongside the working buffer.
3. The model now answers with personalized context it "remembers" across sessions.

**Forgetting:** TTLs on low-value memories, importance decay over time, and **user-initiated deletion** (GDPR) that purges both vector and structured stores.

**Tradeoffs:** more injected memory = more personalization but higher cost and risk of context pollution/distraction. Summarization saves tokens but loses detail.

---

## 12. Design a Text-to-SQL / Natural Language BI System

**Requirements:** convert natural language to SQL over a known schema, execute safely, return accurate results, handle ambiguity.

**Architecture:**

```
Question → Schema retrieval (relevant tables/columns via embeddings)
         → LLM generates SQL (few-shot + schema + business glossary)
         → SQL validator (parse, allow-list, read-only) → Execute (row/time limits)
         → Result → LLM summarizes / chart → Answer (with the SQL shown)
```

### Deep dive — Query flow (English question to trusted answer)

1. **Schema linking.** Real warehouses have thousands of columns — too many for the prompt. Embed the question and **retrieve only the relevant tables/columns** (using column names + descriptions + a business glossary). This focused schema is the single biggest accuracy lever.
2. **Grounded generation.** The LLM gets: the pruned schema, a few **few-shot examples** of good question→SQL pairs, sample rows, and the business glossary ("revenue = net_sales − returns"). It generates candidate SQL.
3. **Static validation.** Before touching the DB: parse the SQL, enforce **read-only** (reject writes/DDL), allow-list tables the user may query, and inject **row/time limits**. Execution runs under a least-privilege, read-only role in a sandbox.
4. **Execute.** Run against the warehouse (often a replica) with a timeout.
5. **Self-correction loop.** If the DB returns an error, feed the error message back to the LLM to **repair** the query and retry (bounded attempts) — this dramatically raises success rate.
6. **Present with trust.** The LLM summarizes results and/or picks a chart, and **always shows the generated SQL** so the analyst can verify — critical for trust in BI.
7. **Ambiguity handling.** If the question is ambiguous ("top customers" — by revenue or count?), the system either asks a clarifying question or states its assumption explicitly.
8. **Cache** frequent question→SQL mappings to cut cost/latency.

**Tradeoffs:** more schema context improves accuracy but costs tokens; strict validation reduces flexibility but is essential for safety on production databases.

---

## 13. Design a Fine-Tuning / Model Customization Pipeline

**Requirements:** let teams fine-tune (LoRA/full) or distill models, manage datasets, evaluate, deploy safely.

**Architecture:**

```
Data prep (collect, clean, dedupe, format, split) → Dataset versioning
→ Training (LoRA/QLoRA/full FT) on GPU cluster → Experiment tracking
→ Evaluation (held-out + safety evals) → Registry (versioned adapters/models)
→ Canary deploy → A/B vs baseline → Promote or roll back
```

### Deep dive — Pipeline flow (raw data to promoted model)

1. **Data curation.** Collect examples, then **clean, dedupe, and decontaminate** against your eval sets (leakage inflates scores). Balance classes, standardize formatting into the training chat template. Version the dataset so runs are reproducible.
2. **Method selection.** Default to prompt/RAG; fine-tune only when you need a consistent style/format or lower latency than prompting allows. For cost, use **LoRA/QLoRA** — you freeze the base weights and train small low-rank adapter matrices (millions of params vs billions), which is cheap and fast. Full fine-tuning is rare.
3. **Distillation (optional).** Run a strong **teacher** model to generate high-quality outputs on your task, then fine-tune a cheaper **student** on those outputs — once you've validated the teacher's quality. You get near-teacher behavior at a fraction of inference cost.
4. **Train + track.** Run on a GPU cluster; log hyperparameters, loss curves, and artifacts to an experiment tracker.
5. **Evaluate — never ship on loss alone.** Run the candidate against a held-out task set **plus safety/regression evals**. Compare to the current baseline.
6. **Register.** Store the versioned adapter/model with a model card (data lineage, metrics, intended use).
7. **Canary + A/B.** Deploy to a small traffic slice, A/B against baseline on real metrics; **promote** if it wins, **roll back** if not.
8. **Efficient serving.** With **multi-LoRA serving**, many customized adapters share one base model in memory and are swapped per request — serving hundreds of fine-tunes cheaply.

**Tradeoffs:** fine-tuning bakes in knowledge (fast at inference) but is costly to update vs RAG (fresh, updatable, adds retrieval latency). Often combine both.

---

## 14. Design a Recommendation System with LLMs

**Requirements:** personalized recommendations enhanced by LLM understanding; scale to millions of items/users; low latency.

**Architecture:**

```
Offline: Items → LLM/embedding enrichment (summaries, tags, embeddings) → Item vectors
         User history → user embedding / profile
Online: Candidate generation (ANN retrieval + collaborative filtering)
        → Ranking (features + LLM reranker for top-N)
        → LLM generates explanations → Results
```

### Deep dive — Two-stage flow (millions of items to a ranked shortlist)

**Offline enrichment (batch):**
1. For every item, an LLM generates rich summaries/tags and an **embedding** capturing semantic content. These are precomputed and stored — you never run an LLM over the full catalog online.
2. Build a **user embedding/profile** from interaction history (updated incrementally as users act).

**Online serving (per request):**
1. **Candidate generation (cheap, wide).** From millions of items, narrow to a few hundred candidates fast via **ANN retrieval** (user embedding → nearest item vectors) blended with **collaborative filtering** ("users like you bought…"). No LLM here — it must be milliseconds over the whole catalog.
2. **Ranking (expensive, narrow).** Rank only the few hundred candidates using a feature-rich model; optionally apply an **LLM reranker** on the top-N to capture nuanced intent that classic features miss.
3. **Cold start.** For a brand-new item/user with no interaction history, fall back to **semantic similarity** via LLM embeddings — content match works where collaborative signals don't yet exist.
4. **Explanations.** An LLM generates human-readable "why recommended" text for the final shortlist — only for the handful shown, so cost stays bounded.
5. **Cache** aggressively; keep the online path lean via precomputation.

**Tradeoffs:** LLM enrichment improves relevance and cold-start but adds offline cost; keep the online path lean with precomputation and staged ranking. The rule: **never run an LLM over the full candidate set** — only over the top-K after cheap retrieval.

---

## 15. Cross-Cutting Concerns Cheat Sheet

Bring these up proactively in any GenAI HLD — they separate mid from senior candidates.

**Cost optimization:**
- Model tiering (route easy → mini, hard → frontier); prompt/semantic caching; batch offline work.
- Trim context (rerank, compress); cap max tokens; quantized/self-hosted models at steady high volume.
- Attribute and monitor cost per request/tenant; budget caps + alerts.

**Latency optimization:**
- Streaming (TTFT matters most); parallelize retrieval + guardrails; speculative decoding.
- Cache prompts/embeddings/results; keep models warm; smaller models where quality allows.

**Reliability:**
- Provider fallback chains, circuit breakers, timeouts + retries with backoff, graceful degradation.
- Idempotency for tool actions; dead-letter queues for async pipelines.

**Security & privacy:**
- Prompt-injection defenses, PII redaction, secrets scanning, least-privilege tool scopes.
- Data residency, encryption at rest/in transit, no training on customer data, ACL-enforced retrieval.

**Observability:**
- End-to-end tracing (tokens, cost, latency per span), quality eval (offline gates + online sampling), drift detection, alerting.

**Multi-tenancy:**
- Tenant ID on every record, per-tenant quotas (RPM + TPM), logical/physical isolation, cost attribution, noisy-neighbor protection.

**Evaluation:**
- Golden datasets, LLM-as-judge (calibrated with human labels), CI eval gates, A/B testing, feedback loops (data flywheel).

**Quality:**
- Grounding + citations for RAG, guardrails, HITL for high-stakes, continuous improvement from production traces.

---

*Practice tip: for any prompt, spend the first 2–3 minutes on requirements and scale, draw the box diagram, then **walk one request through every hop naming the data at each step** — that narrative is what earns the senior signal. Close by naming 2–3 explicit tradeoffs and how you'd evaluate success.*
