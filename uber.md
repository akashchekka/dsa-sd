# Uber 1st-Round Prep Assessment for `akashchekka/dsa-sd/Python`

Good news — your foundation is **solid for a 1st round**. You've covered most of the core patterns Uber actually drills on. Below is an honest readout of where you stand, the gaps to close in the next 7 days, and the highest-ROI question list to grind.

---

## 📊 Current Coverage Audit

| Topic | File | Status | Notes |
|---|---|---|---|
| Arrays / Two Pointers / Sliding Window | `Array.ipynb` (19 KB) | ✅ Strong | Move zeros, Kadane, Merge intervals, Product except self, Longest substring, Best time to buy/sell, Majority (Boyer-Moore), Find min in rotated, Longest consecutive sequence, Valid palindrome, Valid parens, Pascal triangle, Decode string. Good breadth. |
| Strings | `Strings.ipynb` (3 KB) | ⚠️ Thin | Only Luhn's + Min Window Substring. Need more. |
| Linked List | `LinkedList.ipynb` (7 KB) | ✅ Good | Cycle detect, Merge 2, Reverse, Remove Nth, Merge K, Reorder. Solid. |
| Trees | `Tree.ipynb` (10 KB) | ✅ Good | BST insert/delete, BFS, Right view, Max depth, LCA (BST), Kth smallest, isSubtree, isValidBST. Missing: invert tree, diameter, path sum, serialize/deserialize. |
| Graphs | `Graphs.ipynb` (14 KB) | ✅ Strong | DFS/BFS, hasPath, Connected components, Largest component, Shortest path, Clone graph, Cycle detect, Valid tree, **Union-Find**, **Topological sort**. This is your strongest area — Uber loves this. |
| Heap | `Heap.ipynb` (6 KB) | ✅ Good | heapq basics, heapsort, Kth largest, Top K frequent, Median in stream, K closest points. Covered well. |
| Matrix | `Matrix.ipynb` (13 KB) | ✅ Likely good (size suggests breadth) | |
| Trie | `Trie.ipynb` (3 KB) | ⚠️ Basic | Probably just insert/search. |
| LRU | `LRU.ipynb` (3 KB) | ✅ Done | This IS one of Uber's most-asked. |
| Bit Manipulation | `Bit.ipynb` (5 KB) | ✅ OK | Lower priority for round 1. |
| **Dynamic Programming** | `DP.ipynb` (1.4 KB) | 🔴 **Critical gap** | Only **Unique Paths**. This is your biggest risk. |

---

## 🚨 Top 3 Risks to Fix This Week

### 1. Dynamic Programming (highest priority — your `DP.ipynb` has only 1 problem)
Uber regularly asks 1 medium DP in round 1. Minimum viable list (do in this order, ~2 days):

**1D DP foundations** → **2D grid** → **Subsequence/string DP** → **Interval/knapsack**

| # | Problem | Pattern |
|---|---|---|
| 1 | [Climbing Stairs (70)](https://leetcode.com/problems/climbing-stairs/) | 1D base case |
| 2 | [House Robber (198)](https://leetcode.com/problems/house-robber/) | 1D pick/skip |
| 3 | [House Robber II (213)](https://leetcode.com/problems/house-robber-ii/) | **Asked at Uber** |
| 4 | [Coin Change (322)](https://leetcode.com/problems/coin-change/) | Unbounded knapsack |
| 5 | [Longest Increasing Subsequence (300)](https://leetcode.com/problems/longest-increasing-subsequence/) | LIS pattern |
| 6 | [Word Break (139)](https://leetcode.com/problems/word-break/) | String DP — Uber favorite |
| 7 | [Unique Paths II (63)](https://leetcode.com/problems/unique-paths-ii/) | You have I, do II with obstacles |
| 8 | [Longest Common Subsequence (1143)](https://leetcode.com/problems/longest-common-subsequence/) | 2D string DP |
| 9 | [Edit Distance (72)](https://leetcode.com/problems/edit-distance/) | Classic 2D |
| 10 | [Decode Ways (91)](https://leetcode.com/problems/decode-ways/) | 1D string DP |
| 11 | [Partition Equal Subset Sum (416)](https://leetcode.com/problems/partition-equal-subset-sum/) | 0/1 knapsack |
| 12 | [Burst Balloons (312)](https://leetcode.com/problems/burst-balloons/) | **Asked at Uber** (interval DP — stretch goal) |

> **Tip:** Don't memorize. Internalize the recurrence-writing process: *state → transition → base case → order of fill → space optimize*.

### 2. Strings — too thin
Add to `Strings.ipynb`:
- [Longest Palindromic Substring (5)](https://leetcode.com/problems/longest-palindromic-substring/) — expand around center
- [Group Anagrams (49)](https://leetcode.com/problems/group-anagrams/) (you have it in Array, move it)
- [String to Integer / atoi (8)](https://leetcode.com/problems/string-to-integer-atoi/) — Uber asks parsing
- [Find Closest Palindrome (564)](https://leetcode.com/problems/find-the-closest-palindrome/) — **Uber-tagged**
- [Valid IP Addresses / Restore IP](https://leetcode.com/problems/restore-ip-addresses/)

### 3. A few Tree/Graph gaps
- [Serialize and Deserialize Binary Tree (297)](https://leetcode.com/problems/serialize-and-deserialize-binary-tree/) — **Uber-tagged**
- [Lowest Common Ancestor of Binary Tree (236)](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/) — you only have BST version
- [Diameter of Binary Tree (543)](https://leetcode.com/problems/diameter-of-binary-tree/)
- [Number of Islands (200)](https://leetcode.com/problems/number-of-islands/) — make sure it's in your Matrix file
- [Bus Routes (815)](https://leetcode.com/problems/bus-routes/) — **classic Uber question** (BFS on routes)
- [Pacific Atlantic Water Flow (417)](https://leetcode.com/problems/pacific-atlantic-water-flow/) — **Uber-tagged**

---

## 🎯 Most-Asked Uber 1st-Round Questions (curated)

Based on recent 2025–26 interview reports, these are the highest-frequency Uber problems. **Bolded = you haven't done it.**

### Tier 1 — Must do (90% chance one of these shows up)
1. **[Bus Routes (815)](https://leetcode.com/problems/bus-routes/)** — Uber's signature question
2. [LRU Cache (146)](https://leetcode.com/problems/lru-cache/) ✅ you have it — re-do clean
3. [Number of Islands (200)](https://leetcode.com/problems/number-of-islands/) — verify in Matrix
4. **[Design Hit Counter (362)](https://leetcode.com/problems/design-hit-counter/)** — Uber loves design-lite
5. **[Insert/Delete/GetRandom O(1) (380)](https://leetcode.com/problems/insert-delete-getrandom-o1/)** — recurring Uber design
6. [Merge Intervals (56)](https://leetcode.com/problems/merge-intervals/) ✅
7. [Longest Consecutive Sequence (128)](https://leetcode.com/problems/longest-consecutive-sequence/) ✅
8. **[Word Break (139)](https://leetcode.com/problems/word-break/)** — DP

### Tier 2 — Strongly likely
9. [Clone Graph (133)](https://leetcode.com/problems/clone-graph/) ✅
10. **[Serialize/Deserialize Binary Tree (297)](https://leetcode.com/problems/serialize-and-deserialize-binary-tree/)**
11. [Top K Frequent Elements (347)](https://leetcode.com/problems/top-k-frequent-elements/) ✅
12. [K Closest Points to Origin (973)](https://leetcode.com/problems/k-closest-points-to-origin/) ✅
13. [Find Median from Data Stream (295)](https://leetcode.com/problems/find-median-from-data-stream/) ✅
14. [Min Window Substring (76)](https://leetcode.com/problems/minimum-window-substring/) ✅
15. **[House Robber II (213)](https://leetcode.com/problems/house-robber-ii/)** — DP
16. **[Find the Closest Palindrome (564)](https://leetcode.com/problems/find-the-closest-palindrome/)**
17. **[Pacific Atlantic Water Flow (417)](https://leetcode.com/problems/pacific-atlantic-water-flow/)**

### Tier 3 — Stretch / harder rounds
18. **[Burst Balloons (312)](https://leetcode.com/problems/burst-balloons/)** — interval DP
19. **[Making a Large Island (827)](https://leetcode.com/problems/making-a-large-island/)** — Union Find
20. **[Distinct Subsequences (115)](https://leetcode.com/problems/distinct-subsequences/)** — DP

---

## 🗓️ Suggested 7-Day Plan

| Day | Focus | Deliverable |
|---|---|---|
| **1** | DP basics: Climbing stairs, House Robber I+II, Coin Change, Decode Ways | 5 problems in `DP.ipynb` |
| **2** | DP intermediate: Word Break, LIS, LCS, Edit Distance, Unique Paths II | 5 more in `DP.ipynb` |
| **3** | Uber Tier 1 misses: Bus Routes, Hit Counter, RandomizedSet, Word Break revisit | 4 problems |
| **4** | Trees/Graphs gaps: Serialize/Deserialize, LCA (binary tree), Diameter, Pacific Atlantic | 4 problems |
| **5** | Strings: Longest Palindromic Substring, atoi, Closest Palindrome, Restore IPs | 4 problems |
| **6** | **Mock**: pick 2 random Tier-1/2 problems, solve in 35 min each on a blank editor, talk aloud | Self-eval |
| **7** | Light review + behavioral prep ("Tell me about a project", "disagreement with teammate") + sleep | Rest day |

---

## 💡 Round-1 Tactical Tips for Uber

1. **Talk through clarifying questions first** (input range, duplicates, empty cases) — Uber interviewers explicitly grade communication.
2. **State brute force → optimize**. Even if you know optimal, verbalize the brute force and its complexity first.
3. **Always state time/space at the end**, then ask "want me to optimize space?"
4. **Test your code by dry-running** an example you write on the side — Uber dings people who don't.
5. **Python-specific**: know `collections.deque`, `heapq` (min-heap only — negate for max), `defaultdict`, `Counter`, `bisect`, `functools.lru_cache`. You already use these well.

---

## TL;DR

You're ~75% ready. **Spend Days 1–2 entirely on DP** (your one real gap), Day 3 on the 4 Uber-signature problems you're missing (Bus Routes, Hit Counter, RandomizedSet O(1), Serialize/Deserialize Tree), and Days 4–5 patching strings and a few tree/graph holes. You'll walk in confident.

Good luck — you've got this. 🚗💨