# GenAI Interview Preparation — Advanced & Deep-Dive Topics

*Covers topics beyond resume-specific questions: Transformer internals, tokenization, training, inference optimization, reasoning models, responsible AI, LLMOps, security, serving, and more.*

---

## Table of Contents

1. [Transformer Architecture Deep Dive](#1-transformer-architecture-deep-dive)
   - Q1: Transformer architecture end-to-end
   - Q2: Self-Attention step-by-step
   - Q3: Multi-Head Attention
   - Q4: Positional Encoding (RoPE, ALiBi)
   - Q5: KV Cache
   - Q6: Feed-Forward Network (FFN)
2. [Tokenization Deep Dive](#2-tokenization-deep-dive)
   - Q7: How does BPE tokenization work?
   - Q8: Why does tokenization matter for LLM performance?
   - Q9: BPE vs WordPiece vs SentencePiece
3. [LLM Training Pipeline](#3-llm-training-pipeline)
   - Q10: Stages of training an LLM
   - Q11: How does RLHF work in detail?
   - Q12: What is DPO and why is it replacing RLHF?
4. [Inference Optimization](#4-inference-optimization)
   - Q13: Main inference optimization techniques
   - Q14: Speculative Decoding
   - Q15: Flash Attention
   - Q16: Continuous Batching
   - Q17: Model quantization in detail
5. [Reasoning Models & Advanced Generation](#5-reasoning-models--advanced-generation)
   - Q18: Reasoning Models (o1, o3, DeepSeek-R1)
   - Q19: Chain-of-Thought vs Reasoning Models
   - Q20: Test-Time Compute Scaling
6. [LLM Serving & Deployment](#6-llm-serving--deployment)
   - Q21: Compare LLM serving frameworks
   - Q22: vLLM and PagedAttention
   - Q23: Self-hosted vs managed LLM serving
7. [Responsible AI & Safety](#7-responsible-ai--safety)
   - Q24: Key Responsible AI principles
   - Q25: Types of bias in LLMs
   - Q26: Red Teaming for LLMs
   - Q27: Constitutional AI (CAI)
8. [LLMOps & Production Lifecycle](#8-llmops--production-lifecycle)
   - Q28: LLMOps vs MLOps
   - Q29: CI/CD for GenAI applications
   - Q30: Versioning prompts in production
   - Q31: Data Flywheel for GenAI
9. [Knowledge Graphs + LLMs](#9-knowledge-graphs--llms)
   - Q32: How do Knowledge Graphs enhance LLMs?
   - Q33: Graph RAG (Microsoft)
10. [Multimodal Models](#10-multimodal-models)
    - Q34: Vision-Language Models (VLMs)
    - Q35: CLIP
11. [Long-Context Models](#11-long-context-models)
    - Q36: Handling 1M+ token context windows
    - Q37: Long context vs RAG
12. [Semantic Kernel vs LangChain/LangGraph](#12-semantic-kernel-vs-langchainlanggraph)
    - Q38: Semantic Kernel vs LangChain/LangGraph comparison
13. [Agent Frameworks Comparison](#13-agent-frameworks-comparison)
    - Q39: Modern agent frameworks comparison
    - Q40: A2A (Agent-to-Agent) protocol
14. [Embedding Fine-Tuning](#14-embedding-fine-tuning)
    - Q41: When and how to fine-tune embedding models
15. [Hallucination Detection & Mitigation](#15-hallucination-detection--mitigation)
    - Q42: Systematically reducing hallucinations
16. [Advanced Caching Strategies](#16-advanced-caching-strategies)
    - Q43: Caching strategies for GenAI systems
17. [Model Selection & Routing](#17-model-selection--routing)
    - Q44: Building an intelligent model router
    - Q45: Benchmarking and comparing LLM models
18. [Security Deep Dive](#18-security-deep-dive)
    - Q46: LLM security threat model
    - Q47: Defense-in-depth for GenAI
19. [Real-World System Design Questions](#19-real-world-system-design-questions)
    - Q48: Customer support AI agent design
    - Q49: Document intelligence for law firm
    - Q50: Real-time fraud detection with LLMs
20. [Emerging Topics & Trends](#20-emerging-topics--trends)
    - Q51: Agentic RAG
    - Q52: Tool-Augmented Generation (TAG)
    - Q53: Compound AI systems
    - Q54: Distillation
    - Q55: Synthetic Data Generation

---

## 1. Transformer Architecture Deep Dive

### Q1: Explain the Transformer architecture end-to-end.
**A:** The Transformer (2017, "Attention Is All You Need") replaced RNNs/LSTMs with a purely attention-based architecture.

**Components (Encoder-Decoder, original):**
```
Input → Tokenization → Token Embeddings + Positional Encoding
  → [Encoder: (Self-Attention → Add&Norm → FFN → Add&Norm) × N layers]
  → [Decoder: (Masked Self-Attention → Cross-Attention → FFN) × N layers]
  → Linear → Softmax → Output Token
```

**Modern LLMs (GPT, LLaMA) are decoder-only** — they drop the encoder and use only masked self-attention (can only attend to previous tokens).

**BERT-style models are encoder-only** — bidirectional attention (used for embeddings, classification, reranking).

### Q2: How does Self-Attention work step-by-step?

**Core idea:** For each token, compute how much it should "attend to" every other token.

**Steps:**
1. Each token embedding is projected into three vectors:
   - **Q (Query):** "What am I looking for?"
   - **K (Key):** "What do I contain?"
   - **V (Value):** "What information do I provide?"

2. Compute attention scores:
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right) V$$

3. Step-by-step for the sentence "The cat sat":
   ```
   Q_"sat" · K_"The" = 0.1   (low attention)
   Q_"sat" · K_"cat" = 0.8   (high attention — "who sat?")
   Q_"sat" · K_"sat" = 0.3   (moderate self-attention)
   → softmax → [0.08, 0.72, 0.20]
   → weighted sum of V vectors
   ```

4. **Why divide by √d_k?** Without it, dot products grow large for high dimensions, pushing softmax into regions with tiny gradients (vanishing gradients). Scaling keeps values in a reasonable range.

### Q3: What is Multi-Head Attention?
**A:** Instead of one attention computation, run **multiple attention heads in parallel**, each with different learned Q, K, V projections.

```
Head 1: Learns syntactic relationships ("subject-verb")
Head 2: Learns semantic relationships ("cat-animal")  
Head 3: Learns positional relationships ("nearby words")
...
Head 8-96: Various other patterns
```

Each head captures **different types of relationships**. Outputs are concatenated and projected:
$$\text{MultiHead}(Q,K,V) = \text{Concat}(\text{head}_1, ..., \text{head}_h) W^O$$

**GPT-4 has ~96 attention heads per layer.**

### Q4: What is Positional Encoding and why is it needed?
**A:** Transformers process all tokens in parallel — unlike RNNs, they have **no inherent notion of order**. Positional encoding injects position information.

| Method | How | Used by |
|--------|-----|---------|
| **Sinusoidal (original)** | Fixed sin/cos functions of position | Original Transformer |
| **Learned embeddings** | Trainable position vectors | GPT-2, BERT |
| **RoPE (Rotary)** | Rotates Q/K vectors by position angle | LLaMA, GPT-NeoX, most modern LLMs |
| **ALiBi** | Adds linear bias to attention scores based on distance | BLOOM, MPT |

**RoPE advantage:** Encodes **relative** position (distance between tokens matters, not absolute position), enabling better length generalization.

### Q5: What is the KV Cache and why does it matter?
**A:** During autoregressive generation, the model generates one token at a time. Without KV cache, it would recompute attention for ALL previous tokens at every step.

**KV Cache:** Store the K and V vectors of all previously generated tokens. At each step, only compute Q for the new token and attend to cached K, V.

```
Step 1: Process "The"       → cache K₁, V₁
Step 2: Process "cat"       → cache K₂, V₂; attend to K₁K₂, V₁V₂
Step 3: Process "sat"       → cache K₃, V₃; attend to K₁K₂K₃, V₁V₂V₃
...without cache, step 1000 would recompute all 999 previous K,V
```

**Impact:**
- Without cache: O(n²) per token → O(n³) total for n tokens
- With cache: O(n) per token → O(n²) total
- **Tradeoff:** Uses significant GPU memory (proportional to sequence length × layers × dimensions)

**KV cache size example:** For a 70B model with 128K context, KV cache alone can be **40+ GB**.

### Q6: What is the Feed-Forward Network (FFN) in Transformers?
**A:** After attention, each token passes through a **position-wise FFN** — the same 2-layer MLP applied independently to each token:

$$\text{FFN}(x) = \text{GELU}(xW_1 + b_1)W_2 + b_2$$

- Attention captures **relationships between tokens**
- FFN acts as a **knowledge store** — research suggests factual knowledge is primarily stored in FFN weights
- FFN is typically **4x the hidden dimension** (e.g., hidden=4096 → FFN intermediate=16384)
- FFN parameters make up **~2/3 of total model parameters**

---

## 2. Tokenization Deep Dive

### Q7: How does BPE (Byte Pair Encoding) tokenization work?
**A:** BPE is the most common tokenization algorithm (used by GPT, LLaMA).

**Training process:**
1. Start with character-level vocabulary: `{a, b, c, ..., z, space, ...}`
2. Count all adjacent character pairs in training data
3. Merge the most frequent pair into a new token
4. Repeat until vocabulary reaches desired size (e.g., 50K-100K tokens)

**Example:**
```
Corpus: "low lower lowest"

Step 0: l o w _ l o w e r _ l o w e s t
Most frequent pair: (l, o) → merge to "lo"

Step 1: lo w _ lo w e r _ lo w e s t
Most frequent pair: (lo, w) → merge to "low"

Step 2: low _ low e r _ low e s t
Most frequent pair: (low, e) → merge to "lowe"

...continues until vocab size reached
```

**At inference:** Tokenizer greedily applies learned merges:
- "lower" → ["low", "er"]
- "unhappiness" → ["un", "happiness"] or ["un", "happ", "iness"]

### Q8: Why does tokenization matter for LLM performance?

| Issue | Impact | Example |
|-------|--------|---------|
| **Multilingual** | Non-English text gets more tokens → more expensive, worse quality | "こんにちは" = 3-5 tokens vs "hello" = 1 token |
| **Code** | Whitespace/indentation wastes tokens | Python indentation = wasted tokens |
| **Numbers** | Each digit may be a separate token | "123456" = 6 tokens, bad for arithmetic |
| **Rare words** | Split into subwords, losing meaning | "Akashchekka" → ["Ak", "ash", "che", "kka"] |
| **Context window** | Inefficient tokenization → fewer words fit | Same text, different token counts across models |

**Token counts vary by model:**
- GPT-4: ~100K vocabulary
- LLaMA 3: ~128K vocabulary (better multilingual)
- Gemini: ~256K vocabulary

### Q9: What is the difference between BPE, WordPiece, and SentencePiece?

| Algorithm | Used by | Key difference |
|-----------|---------|---------------|
| **BPE** | GPT, LLaMA | Merges most frequent pairs, byte-level |
| **WordPiece** | BERT | Merges pairs that maximize likelihood (probabilistic) |
| **SentencePiece** | T5, LLaMA | Language-agnostic, treats input as raw bytes, no pre-tokenization |
| **Tiktoken** | OpenAI GPT-4 | Optimized BPE implementation, very fast |

---

## 3. LLM Training Pipeline

### Q10: What are the stages of training an LLM?

```
Stage 1: Pre-training (Self-supervised)
  └─ Predict next token on massive text corpus (trillions of tokens)
  └─ Learns language, facts, reasoning patterns
  └─ Cost: $1M-$100M+ in compute
  └─ Output: Base model (completes text, no instruction following)

Stage 2: Supervised Fine-Tuning (SFT) / Instruction Tuning
  └─ Train on (instruction, response) pairs
  └─ Learns to follow instructions, be helpful
  └─ 10K-1M examples
  └─ Output: Instruction-tuned model (helpful but may be unsafe)

Stage 3: Alignment (RLHF / DPO)
  └─ Align with human preferences (helpful, harmless, honest)
  └─ Human annotators rank responses
  └─ Output: Aligned model (ChatGPT, Claude)

Stage 4: Post-training specialization
  └─ Domain fine-tuning, tool use training, safety fine-tuning
```

### Q11: How does RLHF work in detail?

**Step 1: Train a Reward Model (RM)**
- Show human annotators pairs of model responses
- Humans rank: Response A > Response B
- Train a model to predict human preferences → outputs a scalar reward score
- Dataset: ~100K ranked pairs

**Step 2: Optimize Policy with PPO (Proximal Policy Optimization)**
- Generate response with the LLM (policy model)
- Score with reward model
- Update LLM weights to maximize reward
- Add KL divergence penalty to prevent straying too far from the SFT model (prevents reward hacking)

```
SFT Model → Generate Response → Reward Model scores it → PPO updates weights
                                                          ↑
                                    KL penalty (don't diverge too much from SFT)
```

**Problems with RLHF:**
- Expensive (train 3 models: SFT, Reward, Policy)
- Reward hacking (model exploits RM weaknesses)
- Complex, unstable training

### Q12: What is DPO and why is it replacing RLHF?
**A:** **Direct Preference Optimization** — trains directly on preference pairs without needing a separate reward model.

**Key insight:** The reward model can be derived implicitly from the policy itself. So instead of:
```
RLHF: Train Reward Model → Use RL to optimize → Complex, 3 models
DPO:  Directly optimize on preference pairs → Simple, 1 model
```

**DPO loss:** Increases probability of preferred response, decreases probability of rejected response:
$$L_{DPO} = -\log \sigma\left(\beta \log \frac{\pi_\theta(y_w|x)}{\pi_{ref}(y_w|x)} - \beta \log \frac{\pi_\theta(y_l|x)}{\pi_{ref}(y_l|x)}\right)$$

Where $y_w$ = preferred response, $y_l$ = rejected response.

**Tradeoffs:**
| Aspect | RLHF | DPO |
|--------|------|-----|
| Complexity | 3 models, RL training | 1 model, supervised-style |
| Stability | Unstable, hyperparameter-sensitive | Stable, easier to train |
| Quality | Slightly better at scale | Comparable, sometimes better |
| Cost | Very high | Much lower |
| Adoption | GPT-4 (initially) | LLaMA 3, Gemma, most open models |

---

## 4. Inference Optimization

### Q13: What are the main inference optimization techniques?

| Technique | What it does | Speedup | Quality Impact |
|-----------|-------------|---------|----------------|
| **Quantization** | Reduce precision (FP16→INT8→INT4) | 2-4x | Slight degradation |
| **KV Cache** | Cache previous token K/V matrices | Essential | None |
| **Continuous Batching** | Dynamically batch requests | 2-10x throughput | None |
| **Speculative Decoding** | Draft model proposes, main model verifies | 2-3x | None (lossless) |
| **Flash Attention** | Memory-efficient attention computation | 2-4x | None |
| **PagedAttention (vLLM)** | OS-style paging for KV cache | 2-4x throughput | None |
| **Tensor Parallelism** | Split model across GPUs | Linear scaling | None |

### Q14: What is Speculative Decoding?
**A:** Use a small, fast **draft model** to generate several candidate tokens, then have the large **target model** verify them all in one forward pass.

**How it works:**
1. Draft model (e.g., GPT-2) generates 5 candidate tokens quickly
2. Target model (e.g., GPT-4) processes all 5 in a single forward pass (parallel verification)
3. Accept tokens that match, reject from first mismatch
4. Resample the rejected position using the target model's distribution

```
Draft model generates:  "The cat sat on the"  (5 tokens, fast)
Target model verifies:  "The cat sat on a"    (accepts 4, rejects "the"→"a")
Result: Generated 4 tokens in ~1 forward pass instead of 4
```

**Why it works:** Verification is parallelizable (one forward pass for multiple tokens), but generation is sequential. Most tokens from the draft model are correct for "easy" predictions.

**Tradeoff:** Need a good draft model. If it's too different from the target, acceptance rate drops and there's no speedup.

### Q15: What is Flash Attention?
**A:** An **IO-aware** exact attention algorithm that avoids materializing the full N×N attention matrix in GPU HBM (high bandwidth memory).

**Problem:** Standard attention computes the full attention matrix (N×N for sequence length N), which for 128K tokens = 128K × 128K × 2 bytes = **32 GB** — exceeds GPU memory.

**Flash Attention solution:** 
- Tile the computation — process blocks of Q, K, V at a time
- Compute attention in SRAM (fast, small) instead of HBM (slow, large)
- Never materializes the full N×N matrix
- Uses online softmax trick to compute exact attention incrementally

**Result:** 2-4x faster, uses much less memory, **mathematically identical** output.

### Q16: What is Continuous Batching (Dynamic Batching)?
**A:** In static batching, all requests in a batch must wait for the slowest to finish. In continuous batching (used by vLLM, TGI):

- Requests can **join and leave the batch dynamically**
- When one request finishes generating, a new request immediately takes its slot
- No GPU idle time waiting for the longest sequence

**Impact:** 2-10x throughput improvement over static batching.

### Q17: Explain model quantization in detail.

**What:** Reducing the numerical precision of model weights:

| Precision | Bits per param | Memory for 70B model | Quality |
|-----------|---------------|----------------------|---------|
| FP32 | 32 | 280 GB | Baseline |
| FP16/BF16 | 16 | 140 GB | ~Identical |
| INT8 | 8 | 70 GB | Minimal loss |
| INT4 (GPTQ/AWQ) | 4 | 35 GB | Slight loss |
| GGUF Q4_K_M | 4-5 mixed | ~40 GB | Good balance |

**Methods:**
- **Post-Training Quantization (PTQ):** Quantize after training (GPTQ, AWQ, GGUF) — fast, no retraining
- **Quantization-Aware Training (QAT):** Simulate quantization during training — better quality, expensive

**AWQ (Activation-Aware Weight Quantization):** Not all weights equally important. AWQ identifies salient weight channels (by analyzing activations) and keeps them at higher precision.

---

## 5. Reasoning Models & Advanced Generation

### Q18: What are Reasoning Models (o1, o3, DeepSeek-R1)?
**A:** Models that perform **extended internal reasoning** ("thinking") before producing an answer.

**How they differ from standard models:**
| Aspect | Standard (GPT-4o) | Reasoning (o1/o3) |
|--------|-------------------|-------------------|
| **Process** | Direct answer generation | Think step-by-step internally, then answer |
| **Thinking tokens** | None | Hundreds to thousands of hidden reasoning tokens |
| **Latency** | Lower | Higher (thinking takes time) |
| **Cost** | Lower | Higher (thinking tokens billed) |
| **Accuracy on hard tasks** | Good | Significantly better (math, code, logic) |
| **Simple tasks** | Efficient | Overkill and expensive |

**When to use reasoning models:**
- Complex multi-step math/logic problems
- Code generation with intricate requirements
- Scientific reasoning
- NOT for: simple Q&A, summarization, classification (wasteful)

### Q19: What is Chain-of-Thought vs. Reasoning Models?
**A:**
- **CoT prompting:** You tell the model "think step by step" — it reasons in the output, visible to you
- **Reasoning models:** The model reasons internally in **hidden thinking tokens** — trained via RL to reason, not just prompted

**CoT is prompting; reasoning models are architecturally/training-wise different.**

### Q20: What is Test-Time Compute Scaling?
**A:** Instead of making models bigger (training compute), give them **more compute at inference** (thinking time).

**Insight:** A smaller model thinking longer can outperform a larger model answering immediately.

```
GPT-4o (fast, direct)  →  Accuracy: 80% on hard math
o3-mini (thinking 30s)  →  Accuracy: 95% on hard math
```

**Methods:**
- More thinking tokens
- Multiple samples + majority voting (self-consistency)
- Beam search over reasoning paths
- Iterative refinement

---

## 6. LLM Serving & Deployment

### Q21: Compare LLM serving frameworks.

| Framework | Language | Key Feature | Best For |
|-----------|---------|-------------|----------|
| **vLLM** | Python | PagedAttention, continuous batching | Highest throughput |
| **TGI (Text Generation Inference)** | Rust | HuggingFace integration, production-ready | HF models in production |
| **Ollama** | Go | Simple local deployment | Dev/testing, local models |
| **TensorRT-LLM** | C++/Python | NVIDIA GPU optimization | Maximum single-GPU perf |
| **llama.cpp** | C++ | CPU inference, GGUF format | Edge/CPU deployment |
| **Azure OpenAI** | Managed | Enterprise features, compliance | Enterprise production |

### Q22: What is vLLM and why is it popular?
**A:** An open-source LLM serving engine known for **PagedAttention**.

**PagedAttention:** Inspired by OS virtual memory paging:
- KV cache is divided into fixed-size **blocks (pages)**
- Blocks are allocated on-demand, not contiguously
- Avoids memory fragmentation and waste
- Enables efficient memory sharing across requests (e.g., shared system prompt)

**Result:** 2-4x higher throughput than naive serving, near-zero memory waste.

### Q23: How do you choose between self-hosted vs. managed LLM serving?

| Factor | Self-hosted (vLLM/TGI) | Managed (Azure OpenAI) |
|--------|----------------------|------------------------|
| **Control** | Full (model choice, config) | Limited to available models |
| **Cost at scale** | Lower (own GPUs) | Higher (per-token pricing) |
| **Ops burden** | High (GPU management, scaling) | Zero |
| **Compliance** | You manage | Built-in (HIPAA, SOC2) |
| **Latency** | Predictable (dedicated GPUs) | Variable (shared infra) |
| **Time to production** | Weeks | Hours |
| **Open models** | Any model | Only offered models |
| **Fine-tuned models** | Deploy anywhere | Limited fine-tune options |

---

## 7. Responsible AI & Safety

### Q24: What are the key Responsible AI principles?
**A:**

| Principle | What it means | Implementation |
|-----------|--------------|----------------|
| **Fairness** | No bias against protected groups | Bias testing across demographics, balanced training data |
| **Transparency** | Users know they're interacting with AI | Disclosure, explainable outputs |
| **Accountability** | Clear ownership of AI decisions | Logging, audit trails, human oversight |
| **Reliability** | Consistent, predictable behavior | Testing, guardrails, fallbacks |
| **Privacy** | Protect user data | Data minimization, no PII in logs, anonymization |
| **Inclusiveness** | Work for all users | Multilingual, accessibility, diverse testing |

### Q25: What types of bias exist in LLMs?
**A:**
- **Training data bias:** Model reflects biases in internet text
- **Selection bias:** Training data over-represents certain demographics/languages
- **Confirmation bias:** Model reinforces common stereotypes
- **Recency bias:** Model favors patterns seen more frequently in training
- **Sycophancy:** Model agrees with user even when they're wrong

**Mitigation:**
- Balanced training data and RLHF with diverse annotators
- Red teaming to discover biases
- Output filtering for sensitive topics
- Regular bias audits with tools like Fairlearn

### Q26: What is Red Teaming for LLMs?
**A:** Adversarial testing where a team systematically tries to make the model produce harmful, incorrect, or policy-violating outputs.

**Categories tested:**
- Jailbreaking attempts (bypass safety)
- Prompt injection (override instructions)
- Harmful content generation
- PII extraction
- Bias elicitation
- Factual accuracy under pressure
- Edge cases in tool use

**Best practice:** Red team before every major deployment. Use both human red teamers and automated tools (Garak, PyRIT by Microsoft).

### Q27: What is Constitutional AI (CAI)?
**A:** Anthropic's approach to alignment without human feedback for every example:

1. **Generate** response to potentially harmful query
2. **Self-critique** using a set of principles (constitution): "Does this response cause harm?"
3. **Revise** response based on critique
4. **Train** on the revised (better) responses using DPO

**The "constitution" is a set of explicit rules:**
- "Choose the response that is least harmful"
- "Choose the response that is most helpful while being safe"
- "Avoid responses that are deceptive"

**Advantage over RLHF:** Less human annotation needed — the model self-improves guided by principles.

---

## 8. LLMOps & Production Lifecycle

### Q28: What is LLMOps and how does it differ from MLOps?

| Aspect | Traditional MLOps | LLMOps |
|--------|------------------|--------|
| **Model** | Train your own | Mostly use pre-trained, fine-tune |
| **Data** | Training datasets | Prompts, retrieval data, evaluation sets |
| **Versioning** | Model weights | Prompts, retrieval configs, guardrails |
| **Evaluation** | Accuracy, F1, AUC | Groundedness, relevance, safety (subjective) |
| **Cost driver** | Training compute | Inference tokens |
| **Monitoring** | Drift detection | Quality degradation, hallucination rate |
| **CI/CD** | Retrain → deploy | Prompt update → evaluate → deploy |

### Q29: How do you set up CI/CD for GenAI applications?
**A:**

```
1. Prompt/Config Change (Git PR)
     ↓
2. Automated Evaluation Suite
   - Run test queries against staging
   - Compute metrics (groundedness, relevance, safety)
   - Compare against baseline (regression detection)
     ↓
3. Human Review (for significant changes)
   - Sample outputs reviewed by domain experts
     ↓
4. Staged Rollout
   - Canary deployment (5% traffic)
   - Monitor quality metrics
   - Gradually increase to 100%
     ↓
5. Production Monitoring
   - Continuous quality sampling
   - Cost tracking
   - Alert on quality drops
```

### Q30: How do you version prompts in production?
**A:**
- Store prompts in **version control** (Git), not hardcoded
- Each prompt has a version ID, template variables, and metadata
- Use **prompt registries** (LangSmith Hub, custom DB)
- A/B test prompt versions on live traffic
- Rollback capability to previous versions
- Track which prompt version produced which outputs (traceability)

### Q31: What is the Data Flywheel for GenAI?
**A:** A self-reinforcing loop where production data continuously improves the system:

```
Deploy → Users interact → Collect feedback (thumbs up/down)
  → Identify failure cases → Improve (better prompts, more data, fine-tune)
    → Redeploy → Better results → More users → More feedback → ...
```

**Concrete steps:**
1. Log all queries, retrieved docs, responses, and user feedback
2. Identify patterns in negative feedback
3. Add failing examples to evaluation suite
4. Fix: improve chunking, add data, update prompts, fine-tune
5. Measure improvement, deploy
6. New failure patterns emerge → repeat

---

## 9. Knowledge Graphs + LLMs

### Q32: How do Knowledge Graphs enhance LLMs?
**A:**

| Approach | What | Benefit |
|----------|------|---------|
| **Graph RAG** | Build KG from docs, retrieve subgraphs | Multi-hop reasoning, relationship queries |
| **KG-grounded generation** | LLM references KG for facts | Reduced hallucination |
| **KG construction via LLM** | LLM extracts entities/relations | Automated KG building |
| **Hybrid retrieval** | Vector search + graph traversal | Better for connected information |

**When to use KG over plain RAG:**
- "How does drug A interact with drug B which is prescribed for condition C?" (multi-hop)
- Entities with complex relationships (org charts, supply chains, medical ontologies)
- When you need **explainable** retrieval paths

**Tradeoff:** KG construction is expensive and requires maintenance. Plain RAG is simpler for most use cases.

### Q33: What is Graph RAG (Microsoft)?
**A:** Microsoft's approach that combines:
1. **Build:** LLM extracts entities and relationships from documents → knowledge graph
2. **Community detection:** Identify clusters of related entities
3. **Summarize:** LLM generates summaries for each community
4. **Query:** 
   - **Local search:** Traditional retrieval for specific questions
   - **Global search:** Query community summaries for high-level questions ("What are the main themes?")

**Advantage:** Handles **global/thematic queries** that traditional RAG completely fails at (e.g., "Summarize all risks across 1000 documents").

---

## 10. Multimodal Models

### Q34: How do Vision-Language Models (VLMs) work?
**A:** Models like GPT-4o, Gemini, Claude 3.5 that process both text and images.

**Architecture:**
```
Image → Vision Encoder (ViT) → Image tokens/embeddings
                                       ↓
Text  → Text Tokenizer → Text tokens → [LLM Decoder] → Output text
```

1. **Vision encoder** (typically ViT — Vision Transformer) processes the image into a sequence of patch embeddings
2. A **projection layer** maps image embeddings into the LLM's token embedding space
3. Image tokens are **interleaved with text tokens** in the LLM's context
4. LLM generates text conditioned on both image and text context

### Q35: What is CLIP and why is it important?
**A:** **Contrastive Language-Image Pre-training** (OpenAI) — learns a shared embedding space for text and images.

**Training:** Given (image, caption) pairs:
- Encode image → image embedding
- Encode caption → text embedding
- Train so matching pairs are close, non-matching pairs are far (contrastive loss)

**Uses:**
- Image search with text queries
- Zero-shot image classification
- Multimodal RAG (embed images and text in same space)
- Foundation for building VLMs

---

## 11. Long-Context Models

### Q36: How do models handle 1M+ token context windows?
**A:**

| Technique | How | Used by |
|-----------|-----|---------|
| **RoPE scaling** | Extend rotary position embeddings to longer sequences | LLaMA, most open models |
| **ALiBi** | Linear attention bias, naturally extrapolates | MPT, BLOOM |
| **Ring Attention** | Distribute attention computation across devices | Research |
| **Sparse Attention** | Attend only to local + strided + global tokens | Longformer, BigBird |
| **Sliding Window + Global** | Local window attention + selected global tokens | Mistral |

**The real challenges with long context:**
1. **KV cache memory:** 1M tokens × layers × dimensions = hundreds of GB
2. **Attention complexity:** O(n²) even with optimizations
3. **"Needle in a haystack" problem:** Can the model actually use information from anywhere in the context?
4. **Cost:** More input tokens = higher cost

**Tradeoff:** Having a 1M context window doesn't mean you should fill it. Retrieval (RAG) is still more effective for most tasks — retrieve the relevant 5 chunks instead of dumping 1M tokens and hoping the model finds the needle.

### Q37: When should you use long context vs. RAG?

| Scenario | Long Context | RAG |
|----------|-------------|-----|
| Few documents, need full context | ✅ | Overkill |
| Thousands of documents | Too expensive | ✅ |
| Need exact citation/traceability | Harder | ✅ (know which chunk) |
| Cross-document reasoning | ✅ (all visible at once) | Harder |
| Cost-sensitive | ❌ ($$ per token) | ✅ |
| Latency-sensitive | Slower (process all tokens) | Faster |
| Dynamic/changing corpus | Index updates needed either way | ✅ (incremental) |

---

## 12. Semantic Kernel vs LangChain/LangGraph

### Q38: Compare Semantic Kernel with LangChain/LangGraph.

| Aspect | Semantic Kernel | LangChain/LangGraph |
|--------|----------------|---------------------|
| **By** | Microsoft | LangChain Inc |
| **Languages** | C#, Python, Java | Python, JS |
| **Paradigm** | Plugins + Planners + Kernel | Chains + Agents + Graph |
| **Azure integration** | First-class | Good, but not native |
| **Enterprise readiness** | Built for enterprise .NET | Community-driven |
| **Multi-agent** | Agent framework (preview) | LangGraph (mature) |
| **State management** | Kernel memory, filters | LangGraph checkpointing |
| **Best for** | .NET shops, Azure-heavy orgs | Python-first, flexibility |

**When to choose Semantic Kernel:** Your org is .NET-heavy, deeply on Azure, wants Microsoft support.
**When to choose LangGraph:** Python-first, need complex multi-agent workflows, want framework flexibility.

---

## 13. Agent Frameworks Comparison

### Q39: Compare modern agent frameworks.

| Framework | By | Key Concept | Best For |
|-----------|-----|-------------|----------|
| **LangGraph** | LangChain | State graph with cycles | Complex stateful agents |
| **CrewAI** | Open-source | Role-based agents with tasks | Team-of-agents simulation |
| **AutoGen** | Microsoft | Conversational agents | Multi-agent chat |
| **Semantic Kernel** | Microsoft | Plugins + planners | Enterprise .NET |
| **OpenAI Swarm** | OpenAI | Lightweight handoff-based | Simple agent routing |
| **Haystack** | deepset | Pipeline-based | RAG-focused workflows |

### Q40: What is the A2A (Agent-to-Agent) protocol?
**A:** Google's protocol for agents built by different vendors/frameworks to communicate and collaborate.

**MCP vs A2A:**
| Aspect | MCP | A2A |
|--------|-----|-----|
| **Purpose** | Agent ↔ Tools/Data | Agent ↔ Agent |
| **By** | Anthropic | Google |
| **Scope** | Tool discovery and invocation | Task delegation between agents |
| **Analogy** | USB-C (connect peripherals) | HTTP (services talk to each other) |

**A2A key concepts:**
- **Agent Card:** JSON descriptor of agent capabilities (like an API spec)
- **Task:** Unit of work with lifecycle (pending → running → completed)
- **Message:** Communication between agents
- **Artifact:** Output from task execution

**They're complementary:** MCP connects agents to tools. A2A connects agents to each other.

---

## 14. Embedding Fine-Tuning

### Q41: When and how do you fine-tune embedding models?
**A:** When off-the-shelf embeddings don't capture domain-specific similarity well.

**When to fine-tune:**
- Domain-specific jargon (medical, legal, finance)
- When "similar" means something domain-specific (legal precedent similarity ≠ semantic similarity)
- Retrieval quality is bottleneck despite good chunking

**How:**
1. Create training triplets: (query, positive_doc, negative_doc)
2. Contrastive learning: push positive pairs closer, negative pairs apart
3. Typically fine-tune with LoRA on a base embedding model (BGE, E5)

**Data needed:** 1K-10K high-quality triplets for noticeable improvement.

**Tradeoff:** Improved retrieval for your domain, but need labeled data and the embedding model must be re-run on all documents (re-index everything).

---

## 15. Hallucination Detection & Mitigation

### Q42: How do you systematically reduce hallucinations?

**Detection approaches:**
| Method | How | Precision |
|--------|-----|-----------|
| **Self-consistency** | Generate multiple answers, check agreement | Medium |
| **Retrieval verification** | Check if claims exist in retrieved docs | High |
| **NLI-based** | Use Natural Language Inference model to check entailment | High |
| **LLM-as-judge** | Another LLM checks factuality | Medium-High |
| **Confidence calibration** | Low token probabilities → likely hallucination | Medium |

**Mitigation strategies (layered):**
1. **Better retrieval** — more relevant context reduces need to hallucinate
2. **Explicit grounding instructions** — "Only answer based on the provided context. Say 'I don't know' if the context doesn't contain the answer"
3. **Lower temperature** — reduce randomness (0-0.3 for factual)
4. **Chain-of-thought** — reasoning reduces confabulation
5. **Citation forcing** — require inline citations for every claim
6. **Structured output** — constrain output format
7. **Post-hoc verification** — NLI or LLM check on generated response
8. **Confidence scores** — expose uncertainty to users

---

## 16. Advanced Caching Strategies

### Q43: Compare caching strategies for GenAI systems.

| Strategy | Cache key | Hit rate | Risk |
|----------|----------|----------|------|
| **Exact match** | Hash of full prompt | Low | None (exact) |
| **Semantic cache** | Embedding similarity > threshold | Medium | Similar but different queries |
| **Prompt prefix cache** | Shared system prompt prefix | High (for same system prompt) | None (provider-managed) |
| **Tool result cache** | Tool name + args hash | High (deterministic tools) | Stale data |
| **Retrieval cache** | Query → cached retrieved docs | Medium | Stale index |

**Multi-tier caching architecture:**
```
User Query
  ↓
Tier 1: Exact match cache (Redis) → HIT: return instantly
  ↓ MISS
Tier 2: Semantic cache (vector similarity) → HIT: return if similarity > 0.97
  ↓ MISS  
Tier 3: Retrieval cache (same query → same docs) → HIT: skip retrieval
  ↓ MISS
Tier 4: Full pipeline (retrieve → rerank → LLM)
  → Cache result at all tiers
```

---

## 17. Model Selection & Routing

### Q44: How do you build an intelligent model router?
**A:** Route queries to the cheapest model that meets quality requirements.

**Approaches:**
1. **Rule-based:** Simple queries → GPT-4o-mini, complex → GPT-4o
2. **Classifier-based:** Train a small classifier on query complexity → route
3. **LLM-based:** Cheap model classifies difficulty, routes to appropriate model
4. **Cascading:** Try cheap model first, if confidence low → escalate to expensive model

**Example routing logic:**
```
Query → Complexity classifier
  ├── Simple (FAQ, greeting) → GPT-4o-mini ($0.15/1M tokens)
  ├── Medium (summarization, extraction) → GPT-4o ($2.50/1M tokens)
  └── Complex (reasoning, multi-step) → o1 ($15/1M tokens)
```

**Cost impact:** 70% of queries are simple → 70% cost reduction by routing.

### Q45: How do you benchmark and compare LLM models?

**Common benchmarks:**
| Benchmark | Tests | Limitation |
|-----------|-------|------------|
| **MMLU** | Multi-task knowledge (57 subjects) | Memorization, not reasoning |
| **HumanEval** | Code generation | Simple functions only |
| **GSM8K** | Grade school math | Not representative of hard math |
| **MATH** | Competition math | Narrow domain |
| **MT-Bench** | Multi-turn conversation quality | Subjective |
| **Arena Elo** | Human preference ranking | Expensive, slow |

**Best practice:** Don't rely on public benchmarks. Build your **own evaluation set** with real queries from your domain, scored on your quality criteria.

---

## 18. Security Deep Dive

### Q46: What is a comprehensive LLM security threat model?

| Threat | Description | Mitigation |
|--------|-------------|------------|
| **Prompt injection (direct)** | User input overrides system prompt | Input classification, role separation |
| **Prompt injection (indirect)** | Malicious content in retrieved docs | Content scanning, source trust |
| **Jailbreaking** | Bypass safety training | Multi-layer guardrails, red teaming |
| **Data extraction** | Extract training data or system prompt | Output filtering, prompt hiding |
| **PII leakage** | Model exposes personal info from context | PII detection/redaction on input/output |
| **Denial of wallet** | Attacker sends expensive queries to run up costs | Rate limiting, cost caps, query validation |
| **Model theft** | Extracting model via repeated queries | Rate limiting, API key management |
| **Supply chain** | Compromised model weights or packages | Verify model checksums, audit dependencies |
| **Tool abuse** | Agent executes malicious tool calls | Input validation, sandboxing, HITL |

### Q47: How do you implement defense-in-depth for GenAI?
**A:** Multiple layers, each catching what the previous missed:

```
Layer 1: Network — API Gateway, WAF, DDoS protection
Layer 2: Authentication — Azure AD, API keys, RBAC
Layer 3: Input — Rate limiting, input validation, prompt injection detection
Layer 4: Retrieval — Source trust, content scanning, access control (security trimming)
Layer 5: LLM — System prompt hardening, content filtering
Layer 6: Output — PII scanning, format validation, hallucination check
Layer 7: Monitoring — Anomaly detection, audit logs, alerts
```

---

## 19. Real-World System Design Questions

### Q48: Design a customer support AI agent for an e-commerce company.
**Think through:**

**Functional requirements:**
- Answer product questions (RAG over product catalog)
- Check order status (tool: order API)
- Process returns/refunds (tool: returns API + HITL for refunds > $100)
- Escalate to human when needed

**Architecture:**
```
User → API Gateway → Intent Classifier
  ├── FAQ/Product question → RAG pipeline
  ├── Order inquiry → Order tool + response generation
  ├── Return/Refund → Agent workflow with HITL
  └── Complex/Emotional → Escalate to human
```

**Key decisions:**
- Model: GPT-4o-mini for FAQ, GPT-4o for complex
- Memory: Conversation history in Redis (24hr TTL)
- Guardrails: No price promises, no competitor mentions, PII redaction
- Evaluation: CSAT score, resolution rate, escalation rate
- Fallback: "Let me connect you with a human agent"

### Q49: Design a document intelligence system for a law firm.
**Think through:**
- **Ingestion:** PDF/DOCX with complex layouts → Azure Document Intelligence
- **Chunking:** Hierarchical (preserve section/subsection structure)
- **Search:** Hybrid search with legal citation awareness
- **Security:** Document-level access control (which attorney can see which case)
- **Citation:** Every answer must cite specific document + section
- **Audit:** Complete trace of every query and answer (legal compliance)

### Q50: Design a real-time fraud detection system using LLMs.
**Think through:**
- **Latency requirement:** < 500ms per decision
- Can't use expensive LLM for every transaction
- **Architecture:**
  1. Rule engine catches obvious fraud (fast, < 10ms)
  2. ML model scores risk (medium, < 100ms)
  3. Only suspicious cases (top 5%) go to LLM for reasoning
  4. LLM provides explainable fraud rationale
- **Cost control:** Only 5% of transactions hit the LLM
- **HITL:** Flagged cases queued for human review

---

## 20. Emerging Topics & Trends

### Q51: What is Agentic RAG?
**A:** Instead of a fixed RAG pipeline, an **agent decides** the retrieval strategy dynamically:

- Should I search? Which index? What query?
- Are the results good enough? Should I refine?
- Do I need a web search instead?
- Should I combine multiple sources?

**Example flow:**
```
User: "Compare our Q3 earnings with competitors"

Agent thinks:
  1. Search internal docs for Q3 earnings → found
  2. Need competitor data → not in internal index
  3. Search web for competitor earnings → found
  4. Synthesize comparison
```

### Q52: What is Tool-Augmented Generation (TAG)?
**A:** Going beyond RAG — instead of just retrieving documents, the model can call **computational tools** (calculators, code interpreters, APIs, databases) to generate accurate answers.

**RAG:** "Look up and quote"
**TAG:** "Look up, compute, query, and synthesize"

### Q53: What are compound AI systems?
**A:** Systems that combine multiple AI components (LLMs, retrievers, classifiers, code executors) into a pipeline, rather than relying on a single monolithic model.

**Why:** No single model excels at everything. A compound system routes each sub-task to the best component.

**Example:** Query → Classifier (small model) → Router → [RAG | Calculator | Code Interpreter | Web Search] → LLM Synthesizer → Guardrails → Response

### Q54: What is Distillation and when is it useful?
**A:** Training a **small "student" model** to mimic a **large "teacher" model**.

**How:**
1. Run teacher (GPT-4o) on your data → collect outputs
2. Fine-tune student (GPT-4o-mini or open model) on teacher's outputs
3. Student learns teacher's behavior for your specific task

**When useful:**
- You've validated quality with an expensive model
- Need to reduce cost/latency for production
- Want a smaller model for edge deployment

**Tradeoff:** Student is cheaper and faster but only works well on the specific task it was distilled for — less general than the teacher.

### Q55: What is Synthetic Data Generation and when do you use it?
**A:** Using LLMs to generate training/evaluation data.

**Use cases:**
- Generate Q&A pairs for RAG evaluation: LLM reads document → generates questions that the document answers
- Augment fine-tuning data when real data is scarce
- Generate adversarial examples for red teaming
- Create diverse test cases for guardrail testing

**Risks:**
- Model collapse (training on model-generated data degrades quality)
- Bias amplification
- Quality varies — must filter/validate

**Best practice:** Always mix synthetic with real data. Use synthetic for scale, real for quality calibration.

---

*This document covers deep technical topics beyond resume-specific questions — transformer internals, tokenization, training pipelines, inference optimization, reasoning models, responsible AI, LLMOps, security, system design, and emerging trends.*
