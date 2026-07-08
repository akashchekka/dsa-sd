# GenAI Concepts — Quick Revision

---

## Q: All that I need to know about LLM Inference

**What it is:** Running a **trained** model to generate output (no weight updates). LLMs are **autoregressive** — they generate **one token at a time**, feeding each output back as the next input until a stop condition.

### Core concepts
- **Token:** Subword unit (~4 chars / 0.75 word). Model predicts the next token's probability distribution.
- **Autoregressive loop:** Output token appended → fed back → predict next. Sequential by nature.
- **Two phases:** **Prefill** (process whole prompt at once) then **Decode** (emit tokens one by one).
- **KV cache:** Stored Keys/Values of past tokens so attention isn't recomputed each step.
- **Sampling:** How the next token is chosen (greedy, temperature, top-p, top-k).
- **Stop condition:** EOS token, max tokens, or stop sequence.

### The two phases (the core mental model)
| Phase | What happens | Bottleneck | GPU use |
|---|---|---|---|
| **Prefill** | Read entire prompt in one parallel pass, build KV cache, emit first token | **Compute-bound** | Fully utilized |
| **Decode** | Generate each subsequent token sequentially, one forward pass per token | **Memory-bound** | Under-utilized |

> Prefill is one big parallel matrix crunch → fast. Decode is many tiny sequential steps → slow and memory-bound. This split explains almost all inference latency behavior.

### KV cache — why decode is memory-bound
- Attention for a new token needs **Keys + Values of all previous tokens**.
- Recomputing them every step is O(n²); instead **cache** them and reuse → each step only computes the new token.
- **Cost:** KV cache grows **linearly** with sequence length × layers × heads × 2 (K and V). Often the **real limiter** on batch size and context length.

$$\text{KV cache size} \approx 2 \times L \times n_{\text{tokens}} \times d_{\text{model}} \times \text{bytes}$$

### Delivery/latency metrics (the money numbers)
| Metric | Meaning | Driven by |
|---|---|---|
| **TTFT** (Time To First Token) | Delay until first token appears | **Prefill** (prompt length) |
| **TPOT / ITL** (Time Per Output Token / Inter-Token Latency) | Gap between output tokens | **Decode** |
| **Throughput** | Total tokens/sec across all users | Batching efficiency |
| **Latency** | End-to-end per-request time | Prefill + decode |

- **Total time ≈ TTFT + (output_tokens × TPOT).**
- **Latency vs throughput trade-off:** bigger batches → higher throughput but higher per-user latency.

### Sampling / decoding controls
| Param | Effect | Low | High |
|---|---|---|---|
| **Temperature** | Randomness scaling | Deterministic, focused | Creative, diverse |
| **Top-p (nucleus)** | Keep tokens until cumulative prob = p | Fewer choices | More choices |
| **Top-k** | Keep only top-k tokens | Conservative | Diverse |
| **Greedy** | Always pick argmax | Repeatable | — |

- Factual/RAG → `temperature≈0`. Creative → `0.7–1.0`. Don't stack aggressive temperature + top-p.

### When to care / trade-offs
- **Use knowledge:** every latency, cost, and scaling question about serving LLMs comes back to prefill vs decode + KV cache.
- **Avoid over-optimizing:** for low traffic, a hosted API already applies these; optimizations matter at scale/self-hosting.

**Golden rules:** Generation is **autoregressive** (one token at a time). **Prefill = compute-bound**, **decode = memory-bound**. **KV cache** trades memory for speed and **limits batch size**. **TTFT** comes from prefill, **TPOT** from decode.

> LLM inference is an autoregressive loop split into a compute-bound prefill (process the prompt, build the KV cache, emit the first token) and a memory-bound decode (emit tokens one at a time). The KV cache makes decode fast by avoiding recomputation but grows with sequence length and becomes the main limit on batch size — which is why TTFT is a prefill problem and throughput is a batching problem.

---

## Q: How do you optimize LLM inference?

Optimize along four axes: **batching** (throughput), **memory** (fit more/bigger), **compute** (faster kernels), and **scaling** (more GPUs). Reduce redundant work and keep the GPU busy.

### 1. Batching (biggest throughput lever)
| Technique | Idea | Win |
|---|---|---|
| **Static batching** | Wait, group N requests, run together | Simple, but slow requests block the batch |
| **Continuous / in-flight batching** | Add/evict requests **every decode step** | Huge throughput; no head-of-line blocking (vLLM, TGI) |

> Continuous batching keeps the GPU saturated by never waiting for the slowest request to finish before admitting new ones.

### 2. Memory optimizations (fit more, run bigger)
| Technique | Idea | Trade-off |
|---|---|---|
| **PagedAttention** | Manage KV cache in fixed **pages** like OS virtual memory | Near-zero fragmentation → bigger batches (vLLM) |
| **Quantization** | Weights/activations FP16 → **INT8/INT4/FP8** | ~2–4× less memory, faster; small accuracy loss |
| **KV cache quantization** | Store cached K/V in lower precision | More context/batch per GPU |
| **GQA / MQA** | Share K/V heads across query heads | Smaller KV cache, faster decode |

### 3. Compute optimizations (faster per step)
| Technique | Idea | Win |
|---|---|---|
| **FlashAttention** | IO-aware fused attention kernel | Less memory + faster attention |
| **Speculative decoding** | Small **draft** model proposes k tokens, big model **verifies** in one pass | Fewer expensive steps → lower latency |
| **Prefix / prompt caching** | Reuse KV cache of a shared prompt prefix | Skip recomputing system prompt (up to ~90% savings) |
| **Kernel fusion / compilation** | Fuse ops (torch.compile, TensorRT-LLM) | Less overhead |

### 4. Scaling across GPUs
| Technique | Split by | Use |
|---|---|---|
| **Tensor parallelism** | Split each layer's matmuls across GPUs | Model too big for one GPU |
| **Pipeline parallelism** | Split layers across GPUs (stages) | Very deep models |
| **Data/replica parallelism** | Full model copies behind a balancer | More throughput/QPS |

### 5. Serving-level wins
- **Streaming** tokens → lower **perceived** latency (TTFT matters more than total).
- **Semantic caching** → return cached answer for similar queries.
- **Model right-sizing** → smallest model that passes quality; route easy queries to small models.
- **Distillation** → train a small model to mimic a big one.

### What optimizes what
| Goal | Reach for |
|---|---|
| Higher throughput | Continuous batching, PagedAttention |
| Lower memory / bigger context | Quantization, GQA/MQA, KV-cache quant |
| Lower latency (TTFT/TPOT) | Speculative decoding, prefix caching, FlashAttention, streaming |
| Serve huge models | Tensor + pipeline parallelism |
| Lower cost | Right-size model, distillation, semantic cache, batching |

**Golden rules:** **Batch continuously** to keep the GPU busy. **Quantize + PagedAttention** to fit more. **Speculative decoding + prefix caching** to cut latency. **Tensor/pipeline parallelism** to serve giant models. Remember: **decode is memory-bound**, so most latency wins come from doing **less memory movement**, not more compute.

> Inference optimization works on four axes: batching (continuous/in-flight batching to saturate the GPU), memory (quantization, PagedAttention, GQA to shrink weights and KV cache), compute (FlashAttention, speculative decoding, prefix caching to do fewer/faster steps), and scaling (tensor/pipeline parallelism for huge models). Because decode is memory-bound and KV-cache-limited, the highest-leverage wins reduce memory pressure and redundant recomputation rather than adding raw compute.

---
