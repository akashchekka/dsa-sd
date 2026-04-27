# Dynamic Programming — Interview Prep (Google, Meta, Uber, Netflix)

---

## 1. Core Concepts

### What Is Dynamic Programming?

Dynamic Programming (DP) is an optimization technique that solves problems by breaking them into **overlapping subproblems** and storing their results to avoid redundant computation.

**Two required properties:**
1. **Optimal Substructure** — an optimal solution can be built from optimal solutions to subproblems
2. **Overlapping Subproblems** — the same subproblems are solved multiple times

### Top-Down (Memoization) vs Bottom-Up (Tabulation)

| Approach | Description | Pros | Cons |
|---|---|---|---|
| **Top-Down** | Recursive + cache (memo) | Intuitive, only computes needed states | Recursion overhead, stack limits |
| **Bottom-Up** | Iterative, fill table from base cases up | No recursion overhead, often space-optimizable | Must determine computation order |

```python
# Top-Down (Memoization)
from functools import lru_cache

@lru_cache(maxsize=None)
def fib_memo(n):
    if n <= 1:
        return n
    return fib_memo(n - 1) + fib_memo(n - 2)

# Bottom-Up (Tabulation)
def fib_tab(n):
    if n <= 1:
        return n
    dp = [0] * (n + 1)
    dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n]

# Space-Optimized Bottom-Up
def fib_opt(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
```

---

## 2. DP Patterns

### Pattern 1 — 1D DP (Linear Sequence)

State depends on previous 1-2 elements. Classic examples: Fibonacci, Climbing Stairs, House Robber.

### Pattern 2 — 2D DP (Grid / Two Sequences)

State depends on two dimensions — grid position `(i, j)` or two string indices. Examples: Unique Paths, Edit Distance, LCS.

### Pattern 3 — Knapsack Variants

Choose items with constraints (weight, capacity). Includes 0/1 knapsack, unbounded knapsack, subset sum, partition problems.

### Pattern 4 — Interval DP

Solve over a range `[i, j]`, trying every split point `k`. Examples: Matrix Chain Multiplication, Burst Balloons.

### Pattern 5 — State Machine DP

Model states with transitions. Examples: Best Time to Buy/Sell Stock series.

### Pattern 6 — DP on Strings

LCS, Edit Distance, Palindromes, Distinct Subsequences.

### Pattern 7 — DP with Bitmask

Use a bitmask to represent subsets. Examples: Traveling Salesman, Partition into K equal subsets.

---

## 3. Framework for Solving DP Problems

1. **Define the state** — What does `dp[i]` (or `dp[i][j]`) represent?
2. **Write the recurrence** — How does `dp[i]` relate to previous states?
3. **Identify base cases** — What are the trivially known values?
4. **Determine computation order** — Bottom-up: which direction to iterate?
5. **Optimize space** if possible — Can you reduce from 2D to 1D, or 1D to O(1)?

---

## 4. Problems — Easy

### 4.1 Climbing Stairs (LC 70)

You can climb 1 or 2 steps. How many distinct ways to reach step `n`?

**State:** `dp[i]` = number of ways to reach step `i`  
**Recurrence:** `dp[i] = dp[i-1] + dp[i-2]`

```python
def climb_stairs(n):
    if n <= 2:
        return n
    a, b = 1, 2
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b
```

**Time:** O(n) &nbsp; **Space:** O(1)

---

### 4.2 Min Cost Climbing Stairs (LC 746)

```python
def min_cost_climbing_stairs(cost):
    a, b = cost[0], cost[1]
    for i in range(2, len(cost)):
        a, b = b, min(a, b) + cost[i]
    return min(a, b)
```

---

### 4.3 House Robber (LC 198) ⭐

Cannot rob two adjacent houses. Maximize total.

**State:** `dp[i]` = max money robbing from house 0..i  
**Recurrence:** `dp[i] = max(dp[i-1], dp[i-2] + nums[i])`

```python
def rob(nums):
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]

    prev2, prev1 = 0, 0
    for num in nums:
        prev2, prev1 = prev1, max(prev1, prev2 + num)
    return prev1
```

**Time:** O(n) &nbsp; **Space:** O(1)

---

### 4.4 Maximum Subarray (LC 53) — Kadane's Algorithm

```python
def max_subarray(nums):
    max_sum = cur_sum = nums[0]
    for num in nums[1:]:
        cur_sum = max(num, cur_sum + num)
        max_sum = max(max_sum, cur_sum)
    return max_sum
```

**Key insight:** At each position, either extend the current subarray or start fresh.

---

### 4.5 Pascal's Triangle (LC 118)

```python
def generate(num_rows):
    triangle = [[1]]
    for i in range(1, num_rows):
        prev = triangle[-1]
        row = [1]
        for j in range(1, i):
            row.append(prev[j - 1] + prev[j])
        row.append(1)
        triangle.append(row)
    return triangle
```

---

## 5. Problems — Medium

### 5.1 Longest Increasing Subsequence (LC 300) ⭐

**O(n²) DP:**

**State:** `dp[i]` = length of LIS ending at index `i`  
**Recurrence:** `dp[i] = max(dp[j] + 1)` for all `j < i` where `nums[j] < nums[i]`

```python
def length_of_lis(nums):
    n = len(nums)
    dp = [1] * n

    for i in range(1, n):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)

    return max(dp)
```

**O(n log n) with patience sorting:**

```python
import bisect

def length_of_lis_optimal(nums):
    tails = []
    for num in nums:
        pos = bisect.bisect_left(tails, num)
        if pos == len(tails):
            tails.append(num)
        else:
            tails[pos] = num
    return len(tails)
```

**Key insight:** Maintain `tails` where `tails[i]` is the smallest tail element for an increasing subsequence of length `i+1`.

---

### 5.2 Coin Change (LC 322) ⭐

Find the fewest coins to make up `amount`.

**State:** `dp[a]` = min coins to make amount `a`  
**Recurrence:** `dp[a] = min(dp[a - coin] + 1)` for each coin

```python
def coin_change(coins, amount):
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0

    for a in range(1, amount + 1):
        for coin in coins:
            if coin <= a:
                dp[a] = min(dp[a], dp[a - coin] + 1)

    return dp[amount] if dp[amount] != float('inf') else -1
```

**Time:** O(amount × len(coins)) &nbsp; **Space:** O(amount)

---

### 5.3 Coin Change II (LC 518) — Count Combinations

```python
def change(amount, coins):
    dp = [0] * (amount + 1)
    dp[0] = 1

    for coin in coins:           # iterate coins in outer loop to avoid permutations
        for a in range(coin, amount + 1):
            dp[a] += dp[a - coin]

    return dp[amount]
```

**Key insight:** Iterating coins in the outer loop counts each combination once (not permutations).

---

### 5.4 Longest Common Subsequence (LC 1143) ⭐

**State:** `dp[i][j]` = LCS of `text1[:i]` and `text2[:j]`

```python
def longest_common_subsequence(text1, text2):
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i - 1] == text2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[m][n]
```

**Space-optimized to O(min(m, n)):**

```python
def lcs_optimized(text1, text2):
    if len(text1) < len(text2):
        text1, text2 = text2, text1
    m, n = len(text1), len(text2)
    prev = [0] * (n + 1)

    for i in range(1, m + 1):
        curr = [0] * (n + 1)
        for j in range(1, n + 1):
            if text1[i - 1] == text2[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev = curr

    return prev[n]
```

---

### 5.5 Word Break (LC 139) ⭐

Can `s` be segmented into space-separated dictionary words?

**State:** `dp[i]` = True if `s[:i]` can be segmented

```python
def word_break(s, word_dict):
    word_set = set(word_dict)
    n = len(s)
    dp = [False] * (n + 1)
    dp[0] = True

    for i in range(1, n + 1):
        for j in range(i):
            if dp[j] and s[j:i] in word_set:
                dp[i] = True
                break

    return dp[n]
```

---

### 5.6 Unique Paths (LC 62)

**State:** `dp[r][c]` = number of ways to reach cell `(r, c)`

```python
def unique_paths(m, n):
    dp = [1] * n
    for _ in range(1, m):
        for j in range(1, n):
            dp[j] += dp[j - 1]
    return dp[-1]
```

**Time:** O(m × n) &nbsp; **Space:** O(n)

---

### 5.7 Decode Ways (LC 91) ⭐

```python
def num_decodings(s):
    if not s or s[0] == '0':
        return 0

    n = len(s)
    prev2, prev1 = 1, 1  # dp[i-2], dp[i-1]

    for i in range(1, n):
        curr = 0
        if s[i] != '0':
            curr = prev1
        two_digit = int(s[i - 1:i + 1])
        if 10 <= two_digit <= 26:
            curr += prev2
        prev2, prev1 = prev1, curr

    return prev1
```

---

### 5.8 Partition Equal Subset Sum (LC 416) — 0/1 Knapsack ⭐

Can you partition `nums` into two subsets with equal sum?

```python
def can_partition(nums):
    total = sum(nums)
    if total % 2 != 0:
        return False

    target = total // 2
    dp = [False] * (target + 1)
    dp[0] = True

    for num in nums:
        for j in range(target, num - 1, -1):  # reverse to avoid reuse
            dp[j] = dp[j] or dp[j - num]

    return dp[target]
```

**Key insight:** This is a 0/1 knapsack problem. Iterate in reverse to ensure each number is used at most once.

---

### 5.9 Longest Palindromic Substring (LC 5) ⭐

**Expand around center approach (O(n²) time, O(1) space):**

```python
def longest_palindrome(s):
    res = ""

    def expand(l, r):
        nonlocal res
        while l >= 0 and r < len(s) and s[l] == s[r]:
            if r - l + 1 > len(res):
                res = s[l:r + 1]
            l -= 1
            r += 1

    for i in range(len(s)):
        expand(i, i)      # odd length
        expand(i, i + 1)  # even length

    return res
```

**DP approach:**

```python
def longest_palindrome_dp(s):
    n = len(s)
    dp = [[False] * n for _ in range(n)]
    start, max_len = 0, 1

    for i in range(n):
        dp[i][i] = True

    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                if length == 2 or dp[i + 1][j - 1]:
                    dp[i][j] = True
                    if length > max_len:
                        start, max_len = i, length

    return s[start:start + max_len]
```

---

### 5.10 House Robber II (LC 213)

Houses are in a **circle** — first and last are adjacent.

```python
def rob_ii(nums):
    if len(nums) == 1:
        return nums[0]

    def rob_linear(houses):
        prev2, prev1 = 0, 0
        for h in houses:
            prev2, prev1 = prev1, max(prev1, prev2 + h)
        return prev1

    return max(rob_linear(nums[1:]), rob_linear(nums[:-1]))
```

**Key insight:** Run House Robber I twice — once excluding the first house, once excluding the last.

---

### 5.11 Best Time to Buy and Sell Stock with Cooldown (LC 309) — State Machine

States: **hold**, **sold**, **rest**

```python
def max_profit_cooldown(prices):
    if len(prices) < 2:
        return 0

    hold = -prices[0]   # holding a stock
    sold = 0             # just sold
    rest = 0             # cooldown / idle

    for price in prices[1:]:
        prev_hold = hold
        hold = max(hold, rest - price)
        rest = max(rest, sold)
        sold = prev_hold + price

    return max(sold, rest)
```

---

### 5.12 Target Sum (LC 494)

Assign `+` or `-` to each number to reach `target`. This reduces to subset sum.

```python
def find_target_sum_ways(nums, target):
    total = sum(nums)
    if (total + target) % 2 != 0 or abs(target) > total:
        return 0

    subset_sum = (total + target) // 2
    dp = [0] * (subset_sum + 1)
    dp[0] = 1

    for num in nums:
        for j in range(subset_sum, num - 1, -1):
            dp[j] += dp[j - num]

    return dp[subset_sum]
```

**Key insight:** If we split into positive set P and negative set N:
- `P + N = total`, `P - N = target` → `P = (total + target) / 2`

---

## 6. Problems — Hard

### 6.1 Edit Distance (LC 72) ⭐

Minimum operations (insert, delete, replace) to convert `word1` → `word2`.

**State:** `dp[i][j]` = edit distance between `word1[:i]` and `word2[:j]`

```python
def min_distance(word1, word2):
    m, n = len(word1), len(word2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i - 1] == word2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],      # delete
                    dp[i][j - 1],      # insert
                    dp[i - 1][j - 1]   # replace
                )

    return dp[m][n]
```

**Space-optimized:**

```python
def min_distance_opt(word1, word2):
    m, n = len(word1), len(word2)
    prev = list(range(n + 1))

    for i in range(1, m + 1):
        curr = [i] + [0] * n
        for j in range(1, n + 1):
            if word1[i - 1] == word2[j - 1]:
                curr[j] = prev[j - 1]
            else:
                curr[j] = 1 + min(prev[j], curr[j - 1], prev[j - 1])
        prev = curr

    return prev[n]
```

---

### 6.2 Longest Increasing Path in a Matrix (LC 329)

```python
def longest_increasing_path(matrix):
    if not matrix:
        return 0

    rows, cols = len(matrix), len(matrix[0])
    memo = {}

    def dfs(r, c):
        if (r, c) in memo:
            return memo[(r, c)]

        best = 1
        for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and matrix[nr][nc] > matrix[r][c]:
                best = max(best, 1 + dfs(nr, nc))

        memo[(r, c)] = best
        return best

    return max(dfs(r, c) for r in range(rows) for c in range(cols))
```

**Time:** O(m × n) — each cell computed once. **Space:** O(m × n).

---

### 6.3 Burst Balloons (LC 312) — Interval DP ⭐

**State:** `dp[i][j]` = max coins from bursting balloons in range `(i, j)` exclusive.

```python
def max_coins(nums):
    nums = [1] + nums + [1]
    n = len(nums)
    dp = [[0] * n for _ in range(n)]

    for length in range(2, n):               # gap between i and j
        for i in range(n - length):
            j = i + length
            for k in range(i + 1, j):        # k is the LAST balloon to burst
                dp[i][j] = max(
                    dp[i][j],
                    dp[i][k] + dp[k][j] + nums[i] * nums[k] * nums[j]
                )

    return dp[0][n - 1]
```

**Key insight:** Think of `k` as the **last** balloon to burst in the range, not the first. This makes subproblems independent.

---

### 6.4 Word Break II (LC 140)

Return all possible sentence segmentations.

```python
def word_break_ii(s, word_dict):
    word_set = set(word_dict)
    memo = {}

    def backtrack(start):
        if start in memo:
            return memo[start]
        if start == len(s):
            return [""]

        sentences = []
        for end in range(start + 1, len(s) + 1):
            word = s[start:end]
            if word in word_set:
                for rest in backtrack(end):
                    if rest:
                        sentences.append(word + " " + rest)
                    else:
                        sentences.append(word)

        memo[start] = sentences
        return sentences

    return backtrack(0)
```

---

### 6.5 Regular Expression Matching (LC 10) ⭐

`.` matches any character, `*` matches zero or more of the preceding element.

**State:** `dp[i][j]` = does `s[:i]` match `p[:j]`?

```python
def is_match(s, p):
    m, n = len(s), len(p)
    dp = [[False] * (n + 1) for _ in range(m + 1)]
    dp[0][0] = True

    # Handle patterns like a*, a*b*, a*b*c* matching empty string
    for j in range(2, n + 1):
        if p[j - 1] == '*':
            dp[0][j] = dp[0][j - 2]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if p[j - 1] == '*':
                # Zero occurrences of preceding element
                dp[i][j] = dp[i][j - 2]
                # One or more occurrences
                if p[j - 2] == '.' or p[j - 2] == s[i - 1]:
                    dp[i][j] = dp[i][j] or dp[i - 1][j]
            elif p[j - 1] == '.' or p[j - 1] == s[i - 1]:
                dp[i][j] = dp[i - 1][j - 1]

    return dp[m][n]
```

---

### 6.6 Distinct Subsequences (LC 115)

Count the number of distinct subsequences of `s` that equal `t`.

**State:** `dp[i][j]` = number of ways `s[:i]` contains `t[:j]` as a subsequence

```python
def num_distinct(s, t):
    m, n = len(s), len(t)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = 1  # empty t is a subsequence of any prefix

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            dp[i][j] = dp[i - 1][j]  # skip s[i-1]
            if s[i - 1] == t[j - 1]:
                dp[i][j] += dp[i - 1][j - 1]  # use s[i-1]

    return dp[m][n]
```

---

### 6.7 Palindrome Partitioning II (LC 132) — Min Cuts

```python
def min_cut(s):
    n = len(s)
    # is_pal[i][j] = True if s[i:j+1] is a palindrome
    is_pal = [[False] * n for _ in range(n)]
    for i in range(n - 1, -1, -1):
        for j in range(i, n):
            if s[i] == s[j] and (j - i <= 2 or is_pal[i + 1][j - 1]):
                is_pal[i][j] = True

    # dp[i] = min cuts for s[:i+1]
    dp = list(range(n))  # worst case: cut before every char

    for i in range(1, n):
        if is_pal[0][i]:
            dp[i] = 0
            continue
        for j in range(1, i + 1):
            if is_pal[j][i]:
                dp[i] = min(dp[i], dp[j - 1] + 1)

    return dp[n - 1]
```

---

### 6.8 Best Time to Buy and Sell Stock IV (LC 188) — At Most K Transactions

```python
def max_profit_k(k, prices):
    n = len(prices)
    if not prices or k == 0:
        return 0

    # If k >= n/2, it's unlimited transactions
    if k >= n // 2:
        return sum(max(prices[i + 1] - prices[i], 0) for i in range(n - 1))

    # dp[t][d] = max profit using at most t transactions on day d
    dp = [[0] * n for _ in range(k + 1)]

    for t in range(1, k + 1):
        max_prev = -prices[0]  # max of dp[t-1][j] - prices[j]
        for d in range(1, n):
            dp[t][d] = max(dp[t][d - 1], prices[d] + max_prev)
            max_prev = max(max_prev, dp[t - 1][d] - prices[d])

    return dp[k][n - 1]
```

---

### 6.9 Interleaving String (LC 97)

Is `s3` formed by interleaving `s1` and `s2`?

```python
def is_interleave(s1, s2, s3):
    m, n = len(s1), len(s2)
    if m + n != len(s3):
        return False

    dp = [False] * (n + 1)
    dp[0] = True

    for j in range(1, n + 1):
        dp[j] = dp[j - 1] and s2[j - 1] == s3[j - 1]

    for i in range(1, m + 1):
        dp[0] = dp[0] and s1[i - 1] == s3[i - 1]
        for j in range(1, n + 1):
            dp[j] = (dp[j] and s1[i - 1] == s3[i + j - 1]) or \
                     (dp[j - 1] and s2[j - 1] == s3[i + j - 1])

    return dp[n]
```

---

### 6.10 Minimum Window Subsequence (LC 727)

Find the smallest window in `s` that contains `t` as a subsequence.

```python
def min_window_subsequence(s, t):
    m, n = len(s), len(t)
    # dp[i][j] = starting index in s such that s[dp[i][j]:i+1] contains t[:j+1]
    # We simplify: for each position in s matching end of t, find the start

    best_start, best_len = -1, float('inf')

    for i in range(m):
        if s[i] == t[0]:
            # Try to match t starting from s[i]
            j = 0
            k = i
            while k < m and j < n:
                if s[k] == t[j]:
                    j += 1
                k += 1
            if j == n:
                # Found t ending at k-1, now go backward to tighten
                k -= 1
                j = n - 1
                while j >= 0:
                    if s[k] == t[j]:
                        j -= 1
                    k -= 1
                k += 1
                if k - i < best_len:  # actually use k as start
                    window_len = (i - k)  # we need to recalc
                # Simpler: use DP approach below

    # Clean DP approach
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i  # starting index when t is empty

    for j in range(1, n + 1):
        dp[0][j] = -1  # can't match t[:j] with empty s

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s[i - 1] == t[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = dp[i - 1][j]

    result = ""
    best_len = float('inf')
    for i in range(1, m + 1):
        if dp[i][n] != -1:
            start = dp[i][n]
            if i - start < best_len:
                best_len = i - start
                result = s[start:i]

    return result
```

---

### 6.11 Russian Doll Envelopes (LC 354)

Sort envelopes, then find LIS on heights.

```python
import bisect

def max_envelopes(envelopes):
    # Sort by width ascending; if same width, height descending
    envelopes.sort(key=lambda x: (x[0], -x[1]))

    # LIS on heights
    tails = []
    for _, h in envelopes:
        pos = bisect.bisect_left(tails, h)
        if pos == len(tails):
            tails.append(h)
        else:
            tails[pos] = h

    return len(tails)
```

**Key insight:** Sort width ascending; for same width, sort height **descending** so we can't pick two envelopes with the same width. Then it reduces to LIS on heights.

---

### 6.12 Minimum Cost to Cut a Stick (LC 1547) — Interval DP

```python
def min_cost(n, cuts):
    cuts = sorted([0] + cuts + [n])
    m = len(cuts)
    dp = [[0] * m for _ in range(m)]

    for length in range(2, m):
        for i in range(m - length):
            j = i + length
            dp[i][j] = float('inf')
            for k in range(i + 1, j):
                dp[i][j] = min(
                    dp[i][j],
                    dp[i][k] + dp[k][j] + cuts[j] - cuts[i]
                )

    return dp[0][m - 1]
```

---

## 7. Classic DP Templates

### 0/1 Knapsack

```python
def knapsack_01(weights, values, capacity):
    dp = [0] * (capacity + 1)
    for i in range(len(weights)):
        for w in range(capacity, weights[i] - 1, -1):  # reverse!
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    return dp[capacity]
```

### Unbounded Knapsack

```python
def knapsack_unbounded(weights, values, capacity):
    dp = [0] * (capacity + 1)
    for w in range(1, capacity + 1):
        for i in range(len(weights)):
            if weights[i] <= w:
                dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    return dp[capacity]
```

### Longest Palindromic Subsequence

```python
def longest_palindrome_subseq(s):
    n = len(s)
    dp = [[0] * n for _ in range(n)]
    for i in range(n):
        dp[i][i] = 1

    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                dp[i][j] = dp[i + 1][j - 1] + 2
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])

    return dp[0][n - 1]
```

### Matrix Chain Multiplication

```python
def matrix_chain(dims):
    """dims: list of dimensions. Matrix i has dims[i] x dims[i+1]."""
    n = len(dims) - 1
    dp = [[0] * n for _ in range(n)]

    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            dp[i][j] = float('inf')
            for k in range(i, j):
                cost = dp[i][k] + dp[k + 1][j] + dims[i] * dims[k + 1] * dims[j + 1]
                dp[i][j] = min(dp[i][j], cost)

    return dp[0][n - 1]
```

---

## 8. Cheat Sheet — When to Use What

| Pattern | Clue in Problem Statement |
|---|---|
| 1D DP | "minimum/maximum ending at index i", linear sequence |
| 2D DP (Grid) | Grid traversal, two strings comparison |
| Knapsack (0/1) | "choose or not choose", subset with constraint, **each item used once** |
| Knapsack (Unbounded) | "unlimited supply", **each item reusable** |
| LIS | "longest increasing", sort + subsequence |
| LCS | "longest common", comparing two sequences |
| Interval DP | "merge/split range [i,j]", cost to process a range |
| State Machine | Multiple states with transitions (buy/sell/cooldown) |
| Bitmask DP | Small n (≤ 20), subsets, permutations |
| String DP | Edit distance, matching, subsequences |

---

## 9. Common Mistakes

1. **Wrong base case** — Always verify `dp[0]` (or `dp[0][0]`) is correct
2. **Wrong iteration direction** — 0/1 knapsack must iterate capacity in **reverse**; unbounded iterates **forward**
3. **Combinations vs permutations** — Coin Change II: coins in outer loop = combinations; inner loop = permutations
4. **Off-by-one** — `dp` arrays are often size `n+1`, indices shifted by 1
5. **Not considering empty strings** — String DP needs `dp[0][j]` and `dp[i][0]` initialized
6. **Forgetting space optimization invalidates backtracking** — If you need to reconstruct the solution, keep the full table

---

## 10. Complexity Reference

| Problem | Time | Space |
|---|---|---|
| Fibonacci / Climbing Stairs | O(n) | O(1) |
| House Robber | O(n) | O(1) |
| Kadane's (Max Subarray) | O(n) | O(1) |
| LIS (DP) | O(n²) | O(n) |
| LIS (Binary Search) | O(n log n) | O(n) |
| Coin Change | O(amount × coins) | O(amount) |
| LCS | O(m × n) | O(min(m, n)) optimized |
| Edit Distance | O(m × n) | O(min(m, n)) optimized |
| 0/1 Knapsack | O(n × W) | O(W) |
| Interval DP | O(n³) | O(n²) |
| Bitmask DP | O(2ⁿ × n) | O(2ⁿ) |
| Regex Matching | O(m × n) | O(m × n) |
