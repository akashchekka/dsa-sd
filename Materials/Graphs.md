# Graphs — Interview Prep (Google, Meta, Uber, Netflix)

---

## 1. Core Concepts

### What Is a Graph?

A graph **G = (V, E)** is a set of **vertices** (nodes) connected by **edges**.

| Property | Meaning |
|---|---|
| Directed vs Undirected | Edges have direction or not |
| Weighted vs Unweighted | Edges carry a cost/distance or not |
| Cyclic vs Acyclic | Contains cycles or not |
| Connected vs Disconnected | All nodes reachable from any node or not |
| DAG | Directed Acyclic Graph — used in topological sort, scheduling |

### Representations

#### Adjacency List (most common in interviews)

```python
graph = {
    0: [1, 2],
    1: [0, 3],
    2: [0],
    3: [1]
}
```

**Space:** O(V + E)  
**Edge lookup:** O(degree of node)

#### Adjacency Matrix

```python
#       0  1  2  3
mat = [[0, 1, 1, 0],   # 0
       [1, 0, 0, 1],   # 1
       [1, 0, 0, 0],   # 2
       [0, 1, 0, 0]]   # 3
```

**Space:** O(V²)  
**Edge lookup:** O(1)

#### Edge List

```python
edges = [(0, 1), (0, 2), (1, 3)]
```

Useful for Kruskal's, Bellman-Ford.

---

## 2. Traversals

### BFS (Breadth-First Search)

- Uses a **queue**
- Explores **level by level**
- Ideal for **shortest path in unweighted graphs**, level-order problems

```python
from collections import deque

def bfs(graph, start):
    visited = set([start])
    queue = deque([start])
    order = []

    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return order
```

**Time:** O(V + E) &nbsp; **Space:** O(V)

### DFS (Depth-First Search)

- Uses a **stack** (or recursion)
- Goes **as deep as possible** before backtracking
- Ideal for **cycle detection, connected components, topological sort**

```python
def dfs(graph, start):
    visited = set()
    order = []

    def helper(node):
        visited.add(node)
        order.append(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                helper(neighbor)

    helper(start)
    return order
```

**Time:** O(V + E) &nbsp; **Space:** O(V)

---

## 3. Key Patterns & Algorithms

### Pattern 1 — Connected Components

Count or enumerate groups of connected nodes.

```python
def count_components(n, edges):
    graph = {i: [] for i in range(n)}
    for u, v in edges:
        graph[u].append(v)
        graph[v].append(u)

    visited = set()
    count = 0

    def dfs(node):
        visited.add(node)
        for nei in graph[node]:
            if nei not in visited:
                dfs(nei)

    for i in range(n):
        if i not in visited:
            dfs(i)
            count += 1

    return count
```

### Pattern 2 — Cycle Detection

**Undirected Graph** — a back-edge to a visited node that isn't the parent.

```python
def has_cycle_undirected(graph, n):
    visited = set()

    def dfs(node, parent):
        visited.add(node)
        for nei in graph[node]:
            if nei not in visited:
                if dfs(nei, node):
                    return True
            elif nei != parent:
                return True
        return False

    for i in range(n):
        if i not in visited:
            if dfs(i, -1):
                return True
    return False
```

**Directed Graph** — use 3-color (white/gray/black) or recursion-stack tracking.

```python
def has_cycle_directed(graph, n):
    WHITE, GRAY, BLACK = 0, 1, 2
    color = [WHITE] * n

    def dfs(node):
        color[node] = GRAY
        for nei in graph[node]:
            if color[nei] == GRAY:
                return True
            if color[nei] == WHITE and dfs(nei):
                return True
        color[node] = BLACK
        return False

    for i in range(n):
        if color[i] == WHITE:
            if dfs(i):
                return True
    return False
```

### Pattern 3 — Topological Sort (DAG only)

**Kahn's Algorithm (BFS — Indegree based)**

```python
from collections import deque

def topo_sort_bfs(n, edges):
    graph = {i: [] for i in range(n)}
    indegree = [0] * n
    for u, v in edges:
        graph[u].append(v)
        indegree[v] += 1

    queue = deque([i for i in range(n) if indegree[i] == 0])
    order = []

    while queue:
        node = queue.popleft()
        order.append(node)
        for nei in graph[node]:
            indegree[nei] -= 1
            if indegree[nei] == 0:
                queue.append(nei)

    return order if len(order) == n else []  # empty → cycle exists
```

**DFS-based Topological Sort**

```python
def topo_sort_dfs(n, edges):
    graph = {i: [] for i in range(n)}
    for u, v in edges:
        graph[u].append(v)

    visited = set()
    stack = []

    def dfs(node):
        visited.add(node)
        for nei in graph[node]:
            if nei not in visited:
                dfs(nei)
        stack.append(node)

    for i in range(n):
        if i not in visited:
            dfs(i)

    return stack[::-1]
```

### Pattern 4 — Shortest Path

#### Dijkstra's Algorithm (non-negative weights)

```python
import heapq

def dijkstra(graph, start):
    """graph: {node: [(neighbor, weight), ...]}"""
    dist = {node: float('inf') for node in graph}
    dist[start] = 0
    heap = [(0, start)]

    while heap:
        d, node = heapq.heappop(heap)
        if d > dist[node]:
            continue
        for nei, w in graph[node]:
            nd = d + w
            if nd < dist[nei]:
                dist[nei] = nd
                heapq.heappush(heap, (nd, nei))

    return dist
```

**Time:** O((V + E) log V)

#### Bellman-Ford (handles negative weights)

```python
def bellman_ford(n, edges, start):
    dist = [float('inf')] * n
    dist[start] = 0

    for _ in range(n - 1):
        for u, v, w in edges:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w

    # Negative cycle check
    for u, v, w in edges:
        if dist[u] + w < dist[v]:
            return None  # negative cycle

    return dist
```

**Time:** O(V · E)

#### Floyd-Warshall (all-pairs shortest path)

```python
def floyd_warshall(n, edges):
    dist = [[float('inf')] * n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0
    for u, v, w in edges:
        dist[u][v] = w

    for k in range(n):
        for i in range(n):
            for j in range(n):
                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])

    return dist
```

**Time:** O(V³)

### Pattern 5 — Union-Find (Disjoint Set Union)

```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.components = n

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # path compression
        return self.parent[x]

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return False
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        self.components -= 1
        return True
```

### Pattern 6 — Minimum Spanning Tree

#### Kruskal's (uses Union-Find)

```python
def kruskal(n, edges):
    """edges: [(weight, u, v), ...]"""
    edges.sort()
    uf = UnionFind(n)
    mst_cost = 0
    mst_edges = []

    for w, u, v in edges:
        if uf.union(u, v):
            mst_cost += w
            mst_edges.append((u, v, w))

    return mst_cost, mst_edges
```

#### Prim's (uses heap)

```python
import heapq

def prim(graph, start=0):
    """graph: {node: [(neighbor, weight), ...]}"""
    visited = set()
    heap = [(0, start)]
    mst_cost = 0

    while heap:
        w, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        mst_cost += w
        for nei, weight in graph[node]:
            if nei not in visited:
                heapq.heappush(heap, (weight, nei))

    return mst_cost
```

---

## 4. Problems — Easy

### 4.1 Find if Path Exists in Graph (LC 1971)

Given `n` nodes and `edges`, determine if there is a path from `source` to `destination`.

```python
def valid_path(n, edges, source, destination):
    graph = {i: [] for i in range(n)}
    for u, v in edges:
        graph[u].append(v)
        graph[v].append(u)

    visited = set()

    def dfs(node):
        if node == destination:
            return True
        visited.add(node)
        for nei in graph[node]:
            if nei not in visited and dfs(nei):
                return True
        return False

    return dfs(source)
```

**Why it works:** Simple DFS reachability check. O(V + E).

---

### 4.2 Flood Fill (LC 733)

```python
def flood_fill(image, sr, sc, color):
    original = image[sr][sc]
    if original == color:
        return image

    rows, cols = len(image), len(image[0])

    def dfs(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return
        if image[r][c] != original:
            return
        image[r][c] = color
        dfs(r + 1, c)
        dfs(r - 1, c)
        dfs(r, c + 1)
        dfs(r, c - 1)

    dfs(sr, sc)
    return image
```

**Key insight:** Classic grid-DFS. Change color as you visit to avoid revisiting.

---

### 4.3 Island Perimeter (LC 463)

```python
def island_perimeter(grid):
    rows, cols = len(grid), len(grid[0])
    perimeter = 0

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 1:
                perimeter += 4
                if r > 0 and grid[r - 1][c] == 1:
                    perimeter -= 2
                if c > 0 and grid[r][c - 1] == 1:
                    perimeter -= 2

    return perimeter
```

---

## 5. Problems — Medium

### 5.1 Number of Islands (LC 200) ⭐

```python
def num_islands(grid):
    if not grid:
        return 0

    rows, cols = len(grid), len(grid[0])
    count = 0

    def dfs(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] != '1':
            return
        grid[r][c] = '0'  # mark visited
        dfs(r + 1, c)
        dfs(r - 1, c)
        dfs(r, c + 1)
        dfs(r, c - 1)

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1':
                dfs(r, c)
                count += 1

    return count
```

**Time:** O(M × N) &nbsp; **Space:** O(M × N) worst-case recursion stack.

---

### 5.2 Clone Graph (LC 133) ⭐

```python
def clone_graph(node):
    if not node:
        return None

    clones = {}

    def dfs(n):
        if n in clones:
            return clones[n]
        copy = Node(n.val)
        clones[n] = copy
        for nei in n.neighbors:
            copy.neighbors.append(dfs(nei))
        return copy

    return dfs(node)
```

**Key insight:** Use a hashmap to track already-cloned nodes and avoid infinite loops.

---

### 5.3 Course Schedule (LC 207) ⭐

Detect if all courses can be finished → **cycle detection in a directed graph**.

```python
def can_finish(num_courses, prerequisites):
    graph = {i: [] for i in range(num_courses)}
    for course, pre in prerequisites:
        graph[pre].append(course)

    # 0 = unvisited, 1 = visiting, 2 = visited
    state = [0] * num_courses

    def has_cycle(node):
        if state[node] == 1:
            return True
        if state[node] == 2:
            return False
        state[node] = 1
        for nei in graph[node]:
            if has_cycle(nei):
                return True
        state[node] = 2
        return False

    for i in range(num_courses):
        if has_cycle(i):
            return False
    return True
```

---

### 5.4 Course Schedule II (LC 210) — Topological Order

```python
from collections import deque

def find_order(num_courses, prerequisites):
    graph = {i: [] for i in range(num_courses)}
    indegree = [0] * num_courses
    for course, pre in prerequisites:
        graph[pre].append(course)
        indegree[course] += 1

    queue = deque([i for i in range(num_courses) if indegree[i] == 0])
    order = []

    while queue:
        node = queue.popleft()
        order.append(node)
        for nei in graph[node]:
            indegree[nei] -= 1
            if indegree[nei] == 0:
                queue.append(nei)

    return order if len(order) == num_courses else []
```

---

### 5.5 Rotting Oranges (LC 994) — Multi-source BFS ⭐

```python
from collections import deque

def oranges_rotting(grid):
    rows, cols = len(grid), len(grid[0])
    queue = deque()
    fresh = 0

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 2:
                queue.append((r, c))
            elif grid[r][c] == 1:
                fresh += 1

    if fresh == 0:
        return 0

    minutes = 0
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    while queue:
        minutes += 1
        for _ in range(len(queue)):
            r, c = queue.popleft()
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                    grid[nr][nc] = 2
                    fresh -= 1
                    queue.append((nr, nc))

    return minutes - 1 if fresh == 0 else -1
```

**Key insight:** Push ALL rotten oranges into the queue first, then BFS level-by-level.

---

### 5.6 Pacific Atlantic Water Flow (LC 417)

```python
def pacific_atlantic(heights):
    if not heights:
        return []

    rows, cols = len(heights), len(heights[0])
    pacific = set()
    atlantic = set()

    def dfs(r, c, visited, prev_height):
        if (r, c) in visited or r < 0 or r >= rows or c < 0 or c >= cols:
            return
        if heights[r][c] < prev_height:
            return
        visited.add((r, c))
        for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
            dfs(r + dr, c + dc, visited, heights[r][c])

    for c in range(cols):
        dfs(0, c, pacific, heights[0][c])
        dfs(rows - 1, c, atlantic, heights[rows - 1][c])

    for r in range(rows):
        dfs(r, 0, pacific, heights[r][0])
        dfs(r, cols - 1, atlantic, heights[r][cols - 1])

    return list(pacific & atlantic)
```

**Key insight:** Reverse the problem — start DFS from ocean borders going uphill.

---

### 5.7 Graph Valid Tree (LC 261)

A graph is a valid tree if it's **connected** and has **no cycles** (equivalently, V-1 edges and connected).

```python
def valid_tree(n, edges):
    if len(edges) != n - 1:
        return False

    graph = {i: [] for i in range(n)}
    for u, v in edges:
        graph[u].append(v)
        graph[v].append(u)

    visited = set()

    def dfs(node):
        visited.add(node)
        for nei in graph[node]:
            if nei not in visited:
                dfs(nei)

    dfs(0)
    return len(visited) == n
```

---

### 5.8 Word Ladder (LC 127) — BFS Shortest Path ⭐

```python
from collections import deque

def ladder_length(begin_word, end_word, word_list):
    word_set = set(word_list)
    if end_word not in word_set:
        return 0

    queue = deque([(begin_word, 1)])
    visited = {begin_word}

    while queue:
        word, steps = queue.popleft()
        for i in range(len(word)):
            for c in 'abcdefghijklmnopqrstuvwxyz':
                next_word = word[:i] + c + word[i+1:]
                if next_word == end_word:
                    return steps + 1
                if next_word in word_set and next_word not in visited:
                    visited.add(next_word)
                    queue.append((next_word, steps + 1))

    return 0
```

**Time:** O(M² × N) where M = word length, N = word list size.

---

### 5.9 Network Delay Time (LC 743) — Dijkstra ⭐

```python
import heapq

def network_delay_time(times, n, k):
    graph = {i: [] for i in range(1, n + 1)}
    for u, v, w in times:
        graph[u].append((v, w))

    dist = {i: float('inf') for i in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]

    while heap:
        d, node = heapq.heappop(heap)
        if d > dist[node]:
            continue
        for nei, w in graph[node]:
            nd = d + w
            if nd < dist[nei]:
                dist[nei] = nd
                heapq.heappush(heap, (nd, nei))

    ans = max(dist.values())
    return ans if ans < float('inf') else -1
```

---

### 5.10 Cheapest Flights Within K Stops (LC 787) — Modified BFS/Bellman-Ford

```python
from collections import deque

def find_cheapest_price(n, flights, src, dst, k):
    graph = {i: [] for i in range(n)}
    for u, v, w in flights:
        graph[u].append((v, w))

    dist = [float('inf')] * n
    dist[src] = 0
    queue = deque([(src, 0, 0)])  # node, cost, stops

    while queue:
        node, cost, stops = queue.popleft()
        if stops > k:
            continue
        for nei, w in graph[node]:
            new_cost = cost + w
            if new_cost < dist[nei]:
                dist[nei] = new_cost
                queue.append((nei, new_cost, stops + 1))

    return dist[dst] if dist[dst] < float('inf') else -1
```

---

## 6. Problems — Hard

### 6.1 Alien Dictionary (LC 269) ⭐

Given a sorted list of words in an alien language, derive the character ordering.

```python
from collections import deque

def alien_order(words):
    # Build graph
    graph = {c: set() for word in words for c in word}
    indegree = {c: 0 for c in graph}

    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i + 1]
        min_len = min(len(w1), len(w2))

        # Invalid: prefix comes after longer word
        if len(w1) > len(w2) and w1[:min_len] == w2[:min_len]:
            return ""

        for j in range(min_len):
            if w1[j] != w2[j]:
                if w2[j] not in graph[w1[j]]:
                    graph[w1[j]].add(w2[j])
                    indegree[w2[j]] += 1
                break

    # Topological sort (BFS)
    queue = deque([c for c in indegree if indegree[c] == 0])
    result = []

    while queue:
        c = queue.popleft()
        result.append(c)
        for nei in graph[c]:
            indegree[nei] -= 1
            if indegree[nei] == 0:
                queue.append(nei)

    if len(result) != len(graph):
        return ""  # cycle detected

    return "".join(result)
```

**Key insight:** Compare adjacent words to derive ordering constraints, then topological sort.

---

### 6.2 Word Ladder II (LC 126) — BFS + Backtrack

Find **all** shortest transformation sequences.

```python
from collections import deque, defaultdict

def find_ladders(begin_word, end_word, word_list):
    word_set = set(word_list)
    if end_word not in word_set:
        return []

    # BFS to build parent map (shortest path DAG)
    parents = defaultdict(set)
    layer = {begin_word}
    found = False

    while layer and not found:
        word_set -= layer
        next_layer = set()
        for word in layer:
            for i in range(len(word)):
                for c in 'abcdefghijklmnopqrstuvwxyz':
                    next_word = word[:i] + c + word[i+1:]
                    if next_word in word_set:
                        next_layer.add(next_word)
                        parents[next_word].add(word)
        if end_word in next_layer:
            found = True
        layer = next_layer

    # Backtrack from end_word to begin_word
    result = []

    def backtrack(word, path):
        if word == begin_word:
            result.append(list(reversed(path)))
            return
        for parent in parents[word]:
            path.append(parent)
            backtrack(parent, path)
            path.pop()

    backtrack(end_word, [end_word])
    return result
```

---

### 6.3 Critical Connections in a Network (LC 1192) — Tarjan's Bridge Finding

```python
def critical_connections(n, connections):
    graph = {i: [] for i in range(n)}
    for u, v in connections:
        graph[u].append(v)
        graph[v].append(u)

    disc = [-1] * n
    low = [-1] * n
    bridges = []
    timer = [0]

    def dfs(node, parent):
        disc[node] = low[node] = timer[0]
        timer[0] += 1

        for nei in graph[node]:
            if nei == parent:
                continue
            if disc[nei] == -1:
                dfs(nei, node)
                low[node] = min(low[node], low[nei])
                if low[nei] > disc[node]:
                    bridges.append([node, nei])
            else:
                low[node] = min(low[node], disc[nei])

    dfs(0, -1)
    return bridges
```

**Key insight:** An edge (u, v) is a bridge if `low[v] > disc[u]` — meaning v cannot reach u or above without the edge.

---

### 6.4 Swim in Rising Water (LC 778) — Binary Search + BFS / Dijkstra

```python
import heapq

def swim_in_water(grid):
    n = len(grid)
    visited = set()
    heap = [(grid[0][0], 0, 0)]  # (max elevation so far, r, c)

    while heap:
        t, r, c = heapq.heappop(heap)
        if r == n - 1 and c == n - 1:
            return t
        if (r, c) in visited:
            continue
        visited.add((r, c))
        for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in visited:
                heapq.heappush(heap, (max(t, grid[nr][nc]), nr, nc))

    return -1
```

**Key insight:** Modified Dijkstra where the "distance" is the max elevation on the path.

---

### 6.5 Number of Islands II (LC 305) — Union-Find Online

```python
def num_islands2(m, n, positions):
    uf_parent = {}
    uf_rank = {}
    count = [0]
    result = []

    def find(x):
        if uf_parent[x] != x:
            uf_parent[x] = find(uf_parent[x])
        return uf_parent[x]

    def union(a, b):
        pa, pb = find(a), find(b)
        if pa == pb:
            return
        if uf_rank[pa] < uf_rank[pb]:
            pa, pb = pb, pa
        uf_parent[pb] = pa
        if uf_rank[pa] == uf_rank[pb]:
            uf_rank[pa] += 1
        count[0] -= 1

    for r, c in positions:
        if (r, c) in uf_parent:
            result.append(count[0])
            continue
        uf_parent[(r, c)] = (r, c)
        uf_rank[(r, c)] = 0
        count[0] += 1
        for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in uf_parent:
                union((r, c), (nr, nc))
        result.append(count[0])

    return result
```

---

### 6.6 Reconstruct Itinerary (LC 332) — Eulerian Path (Hierholzer's)

```python
from collections import defaultdict

def find_itinerary(tickets):
    graph = defaultdict(list)
    for src, dst in sorted(tickets, reverse=True):
        graph[src].append(dst)

    route = []

    def dfs(airport):
        while graph[airport]:
            dfs(graph[airport].pop())
        route.append(airport)

    dfs("JFK")
    return route[::-1]
```

**Key insight:** Hierholzer's algorithm — greedily visit the lexicographically smallest neighbor, post-order append gives the reversed Eulerian path.

---

## 7. Cheat Sheet — When to Use What

| Technique | Use When |
|---|---|
| BFS | Shortest path (unweighted), level-order, multi-source |
| DFS | Connectivity, cycle detection, backtracking, paths |
| Topological Sort | Ordering with dependencies (DAG) |
| Dijkstra | Shortest path (weighted, non-negative) |
| Bellman-Ford | Shortest path (negative weights allowed) |
| Floyd-Warshall | All-pairs shortest path (small V) |
| Union-Find | Dynamic connectivity, MST (Kruskal) |
| Tarjan's | Bridges, articulation points, SCCs |
| Multi-source BFS | Multiple starting points spreading simultaneously |
| 0-1 BFS | Shortest path when weights are only 0 or 1 |

---

## 8. Common Mistakes

1. **Forgetting to mark visited before pushing to queue** → infinite loop in BFS
2. **Using DFS for shortest path in an unweighted graph** → BFS is correct
3. **Not handling disconnected components** → always loop over all nodes
4. **Confusing directed vs undirected cycle detection** → algorithms differ
5. **Topological sort on a cyclic graph** → check if result length = number of nodes
6. **Off-by-one in grid problems** → always validate bounds first

---

## 9. Complexity Reference

| Algorithm | Time | Space |
|---|---|---|
| BFS / DFS | O(V + E) | O(V) |
| Topological Sort | O(V + E) | O(V + E) |
| Dijkstra (heap) | O((V + E) log V) | O(V + E) |
| Bellman-Ford | O(V · E) | O(V) |
| Floyd-Warshall | O(V³) | O(V²) |
| Union-Find (amortized) | O(α(N)) ≈ O(1) | O(N) |
| Kruskal's MST | O(E log E) | O(V) |
| Prim's MST (heap) | O((V + E) log V) | O(V + E) |
| Tarjan's Bridges/SCCs | O(V + E) | O(V) |
