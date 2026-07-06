# Bloom Filter

Space-efficient **probabilistic** set-membership. Answers one question fast and with tiny memory: *"Is this item **definitely not** in the set, or **possibly** in it?"*

## Run

```pwsh
cd machine-coding-py
python -m bloom_filter
```

## The subject

**Problem.** You want to check membership in a huge set (billions of URLs, keys, seen-IDs) but can't afford to store every element, and a full lookup (disk/DB/network) is expensive. A Bloom filter answers membership in **O(k)** time using a small bit array — with one catch: it can say "possibly present" when the item isn't there (a **false positive**), but it **never** says "not present" for something that is (**no false negatives**).

**Why it's a good design question.** It looks like a data-structure trick but is really about **trade-offs and math**:

- **Two knobs from two inputs.** Given expected item count `n` and target false-positive rate `p`, you derive the bit array size `m` and number of hash functions `k`.
- **The hashing trick.** You don't need `k` independent hash functions — **double hashing** (`g_i = h1 + i*h2 mod m`) derives all `k` indexes from two base hashes while preserving the error rate.
- **Know the limits.** No deletion (clearing a bit could corrupt other items), can't resize, fixed capacity. Follow-ups: **Counting Bloom filter** (deletes), **Scalable Bloom filter** (growth), **Cuckoo filter** (deletes + locality).
- **Right place to use it.** Only where a false positive triggers a cheap fallback verification — never where being wrong is catastrophic.

**Where Bloom filters live in the real world.** Cassandra / HBase / LevelDB / RocksDB (skip SSTables that definitely lack a key → avoid disk reads), CDNs and web caches ("seen this URL?"), Chrome (malicious-URL pre-check), Bitcoin SPV wallets, dedup pipelines.

**Sizing math.**

```
m = -(n * ln p) / (ln 2)^2      # bit array size
k = (m / n) * ln 2              # number of hash functions
```

**Core mental model.**

```
add(x)          -> set bits h1..hk(x) to 1
might_contain(x)-> any bit 0 ? DEFINITELY absent : POSSIBLY present
```

**Core concepts exercised.** Probabilistic data structures, bit manipulation, hashing (double hashing / Kirsch-Mitzenmacher), interface segregation (`IBloomFilter`, `IHashStrategy`), strategy pattern (pluggable hashing), capacity/error-rate math.

## What's implemented

```
BitArray               -> fixed-size list[bool] bit storage (O(1) set/get)
DoubleHashingStrategy  -> k indexes from one md5 digest split into two halves
BloomFilter            -> sizes m & k from (n, p); add + might_contain
```

## File layout

```
bloom_filter/
├── __main__.py                       # demo: 1000 items @ 1% FP, measures empirical rate
├── models/
│   └── bit_array.py                  # BitArray — fixed-size bit storage
├── interfaces/
│   ├── bloom_filter.py               # IBloomFilter — add, might_contain, bit_size, hash_count
│   └── hash_strategy.py              # IHashStrategy — indexes(item, k, m)
├── strategies/
│   └── double_hashing.py             # DoubleHashingStrategy — one md5 split into h1, h2
└── services/
    └── bloom_filter.py               # BloomFilter — sizing math + core logic
```

## Trade-offs

| Property | Bloom filter |
|---|---|
| False negatives | Never |
| False positives | Yes, bounded by `p` |
| Memory | Tiny (bits, not elements) |
| Deletion | Not supported (use Counting Bloom filter) |
| Resize | Not supported (use Scalable Bloom filter) |

# Formulae Derivation

Here's the full derivation of both formulas, step by step.

## Setup

- `m` = number of bits in the array
- `n` = number of items inserted
- `k` = number of hash functions
- `p` = false-positive probability

## Step 1: Probability a specific bit is still 0

Each inserted item sets `k` bits. Assuming hashes are uniform and independent, one hash sets a given bit with probability $\frac{1}{m}$, so it leaves that bit as 0 with probability $1 - \frac{1}{m}$.

Inserting `n` items = `kn` total bit-sets. The probability a **specific bit is still 0** afterwards:

$$P(\text{bit} = 0) = \left(1 - \frac{1}{m}\right)^{kn}$$

## Step 2: Simplify with the exponential limit

Using the identity $\left(1 - \frac{1}{m}\right)^{m} \approx e^{-1}$ for large `m`:

$$\left(1 - \frac{1}{m}\right)^{kn} \approx e^{-kn/m}$$

So the probability a bit is **1** (set):

$$P(\text{bit} = 1) = 1 - e^{-kn/m}$$

## Step 3: False-positive probability

A false positive happens when a **non-member** hashes to `k` positions that are **all already 1**. Those `k` events (approximately independent):

$$p = \left(1 - e^{-kn/m}\right)^{k}$$

This is the master equation — both formulas fall out of optimizing it.

## Step 4: Derive optimal `k` (minimize `p`)

For fixed `m` and `n`, find the `k` that minimizes `p`. Take the log and differentiate; the minimum occurs when exactly **half the bits are set**. The result:

$$\boxed{k = \frac{m}{n}\ln 2}$$

Intuition: too few hashes → not discriminating enough; too many → the array fills with 1s too fast. The sweet spot is where $P(\text{bit}=1) = \frac{1}{2}$.

## Step 5: Derive optimal `m` (from target `p`)

Substitute the optimal `k` back into the master equation. At the optimum, $e^{-kn/m} = \frac12$, so:

$$p = \left(\tfrac{1}{2}\right)^{k} = 2^{-k}$$

Take $\ln$ of both sides:

$$\ln p = -k \ln 2$$

Substitute $k = \frac{m}{n}\ln 2$:

$$\ln p = -\frac{m}{n}\ln 2 \cdot \ln 2 = -\frac{m}{n}(\ln 2)^2$$

Solve for `m`:

$$\boxed{m = -\frac{n \ln p}{(\ln 2)^2}}$$

## Summary of the chain

```
(1 - 1/m)^(kn)              a bit stays 0
   → e^(-kn/m)              exponential approximation
p = (1 - e^(-kn/m))^k       false-positive master equation
   → minimize over k        gives  k = (m/n) ln 2   (half the bits set)
   → sub back, solve for m  gives  m = -(n ln p)/(ln 2)^2
```

## Quick sanity check

For `p = 0.01`, $\ln 2 \approx 0.693$:

- Bits per item: $\frac{m}{n} = -\frac{\ln 0.01}{(\ln 2)^2} = \frac{4.605}{0.480} \approx 9.6$ bits/item → matches your `m = 9586` for `n = 1000`.
- Hashes: $k = \frac{m}{n}\ln 2 \approx 9.6 \times 0.693 \approx 6.65 \to 7$ → matches your `k = 7`.

**One-liner takeaway:** Everything derives from *"probability a bit is still 0 after `kn` sets"* → the false-positive equation $p = (1 - e^{-kn/m})^k$; minimizing it gives `k = (m/n)ln2` (half the bits set), and substituting back gives `m = -(n·ln p)/(ln2)²`.
