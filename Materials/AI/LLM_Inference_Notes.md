## What is Inference?

Inference is the process of using a **trained model** to generate
predictions. During inference, the model's weights are **frozen**---no
learning or parameter updates occur.

A useful analogy:

-   A **class** defines behavior but must be instantiated before use.
-   A trained **LLM** is a collection of learned parameters stored on
    disk.
-   Loading those parameters into CPU/GPU memory "brings the model to
    life" so it can answer prompts repeatedly until unloaded.

------------------------------------------------------------------------

## High-Level Inference Pipeline

``` text
User Prompt
    ↓
Tokenizer
    ↓
Token IDs
    ↓
Embeddings + Positional Encoding
    ↓
Transformer Layers
    ↓
Logits
    ↓
Softmax + Sampling
    ↓
Next Token
    ↓
Append Token
    ↓
Repeat until EOS
```

### Main Steps

1.  **Tokenization** -- Convert text into token IDs.
2.  **Embedding Lookup** -- Map each token ID to a dense vector.
3.  **Positional Encoding** -- Add positional information so the model
    understands order.
4.  **Transformer Layers** -- Process tokens using self-attention and
    feed-forward networks.
5.  **Logits** -- Produce scores for every token in the vocabulary.
6.  **Sampling** -- Select the next token using methods such as Greedy,
    Temperature, Top-K, or Top-P.
7.  **Repeat** until an end-of-sequence token or another stopping
    condition.

------------------------------------------------------------------------

## Prefill vs Decode

### Prefill

The entire prompt is processed in one forward pass.

-   Computes Keys (K) and Values (V) for all prompt tokens.
-   Builds the KV cache.
-   Highly parallelizable on GPUs.

### Decode

The model generates one token at a time.

-   Uses the existing KV cache.
-   Computes only the new token.
-   Sequential by nature and therefore slower.

------------------------------------------------------------------------

# KV Cache

## Why is it needed?

Without a KV cache, every generated token would require recomputing
attention for **all previous tokens**.

Example:

    Prompt:
    The capital of France is

    Generated:
    Paris

Without caching, the model would process:

    The capital of France is Paris

from scratch before generating the next token.

Repeating this for every token is expensive.

------------------------------------------------------------------------

## The Idea

During the prefill phase, the model computes:

-   Query (Q)
-   Key (K)
-   Value (V)

for every token.

The Keys and Values of previous tokens never change, so instead of
recomputing them, they are stored.

This stored information is called the **KV Cache**.

When generating the next token:

-   Previous K and V are reused.
-   Only the new token's Q, K, and V are computed.

This significantly speeds up autoregressive generation.

------------------------------------------------------------------------

## Why cache only K and V?

Attention is computed as:

    Attention(Q, K, V)

For every newly generated token:

-   The **Query** is new because the token needs to decide what to
    attend to.
-   The previous **Keys** and **Values** remain unchanged.

Therefore only K and V are cached.

------------------------------------------------------------------------

## Where is the KV Cache stored?

Typically in **GPU memory (VRAM)** alongside the loaded model.

    GPU Memory

    +------------------------------+
    | Model Weights                |
    +------------------------------+
    | KV Cache                     |
    +------------------------------+
    | Temporary Buffers            |
    +------------------------------+

Important distinction:

-   **Model weights** are loaded once and shared across requests.
-   **KV cache** is created per request, grows as tokens are generated,
    and is freed when the request ends.

------------------------------------------------------------------------

## Is the KV Cache Durable?

No.

The KV cache is an in-memory optimization.

If the inference process or server restarts:

-   The cache is lost.
-   It is rebuilt by reprocessing the prompt during the next prefill
    phase.

The conversation history may still exist elsewhere, but the cache itself
does not.

------------------------------------------------------------------------

## Can KV Cache be Persisted?

Yes, although it is not the common approach.

Possible approaches:

### Persistent KV Cache

Serialize the KV cache to storage and reload it later.

Useful for:

-   Long-running agent workflows
-   Very long prompts
-   Session resumption

### Prefix Caching

Store the KV cache for frequently reused prompt prefixes.

Example:

    You are a helpful assistant...

Instead of recomputing that prefix for every request, reuse the existing
cache.

This is widely used in production systems.

### Prompt Cache

Cache KV entries using a prompt hash.

If another request has the exact same prefix, reuse the previously
computed KV cache.

------------------------------------------------------------------------

# Inference Optimizations

## 1. KV Cache

Reuses Keys and Values from previous tokens to avoid recomputing
attention.

------------------------------------------------------------------------

## 2. Quantization

Store model weights using lower precision.

Examples:

-   FP16
-   BF16
-   INT8
-   INT4

Benefits:

-   Smaller models
-   Lower memory usage
-   Faster inference

Trade-off:

-   Slight reduction in accuracy depending on the method.

------------------------------------------------------------------------

## 3. Continuous Batching

Dynamically batch multiple incoming requests together.

Benefits:

-   Better GPU utilization
-   Higher throughput
-   Lower cost

------------------------------------------------------------------------

## 4. Prefix Caching

Reuse the KV cache for common prompt prefixes instead of rebuilding it
every time.

------------------------------------------------------------------------

## 5. Speculative Decoding

A smaller model predicts several tokens.

The larger model verifies them.

If correct, multiple tokens are accepted together, reducing latency.

------------------------------------------------------------------------

## 6. FlashAttention

An optimized attention algorithm that reduces memory movement while
producing the same output.

Benefits:

-   Faster attention
-   Lower memory usage

------------------------------------------------------------------------

## 7. PagedAttention

Efficiently manages KV cache memory by storing it in pages instead of
one large contiguous block.

Benefits:

-   Better memory utilization
-   Supports many concurrent users

------------------------------------------------------------------------

## 8. Tensor Parallelism

Split a model across multiple GPUs by dividing model weights.

Useful when a single GPU cannot fit the entire model.

------------------------------------------------------------------------

## 9. Pipeline Parallelism

Split transformer layers across multiple GPUs.

Each GPU executes a different section of the model.

------------------------------------------------------------------------

# Key Takeaways

-   A trained LLM is a collection of learned parameters.
-   Loading the weights into memory enables inference.
-   Inference consists of tokenization, embeddings, transformer
    computation, sampling, and iterative decoding.
-   Prefill processes the entire prompt and builds the KV cache.
-   Decode generates one token at a time using the KV cache.
-   KV cache stores Keys and Values of previous tokens to avoid
    recomputation.
-   KV cache resides in GPU memory, is request-specific, and is not
    durable.
-   Common optimizations include KV cache, quantization, continuous
    batching, prefix caching, speculative decoding, FlashAttention,
    PagedAttention, and model parallelism.
