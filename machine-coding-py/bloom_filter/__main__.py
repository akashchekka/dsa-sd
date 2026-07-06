"""
=============================================================================
 BloomFilter — entry point
=============================================================================
 Run:  python -m bloom_filter   (from machine-coding-py/)
=============================================================================
"""
from __future__ import annotations

from interfaces.bloom_filter import IBloomFilter
from services.bloom_filter import BloomFilter


def main() -> None:
    bf: IBloomFilter = BloomFilter(expected_items=1000, false_positive_rate=0.01)
    print(f"bit array size m={bf.bit_size}, hash functions k={bf.hash_count}")

    present = ["apple", "banana", "cherry", "date"]
    for word in present:
        bf.add(word)

    print("\nMembership checks:")
    for word in present + ["mango", "grape", "kiwi"]:
        hit = bf.might_contain(word)
        tag = "possibly present" if hit else "definitely NOT present"
        print(f"  {word:8} -> {tag}")

    # Empirical false-positive rate on items never added.
    tests = [f"missing_{i}" for i in range(10_000)]
    false_positives = sum(1 for w in tests if bf.might_contain(w))
    print(f"\nEmpirical false-positive rate: {false_positives / len(tests):.4f} (target 0.01)")


if __name__ == "__main__":
    main()
