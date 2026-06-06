
# Splitwise LLD (Uber / Google / Apple Interview Ready)

## Features
- User Registration
- Expense Creation
- Equal Split
- Exact Split
- Percentage Split
- Strategy Pattern
- Debt Simplification
  - Two Pointer
  - Heap Based

## Design

User
Expense
SplitStrategy
  - EqualSplitStrategy
  - ExactSplitStrategy
  - PercentageSplitStrategy

SimplifyStrategy
  - TwoPointerSimplifyStrategy
  - HeapSimplifyStrategy

SplitwiseService

## Two Pointer Simplification

Balances:

A=-80
D=-20
B=50
C=50

Debtors:
A(80), D(20)

Creditors:
B(50), C(50)

Transactions:

A -> B = 50
A -> C = 30
D -> C = 20

Time Complexity: O(N)

## Heap Simplification

Max debtor matched with max creditor.

Heap:
A(80), D(20)
B(50), C(50)

Transactions:

A -> B = 50
A -> C = 30
D -> C = 20

Time Complexity: O(N log N)

## Interview Discussion

### Patterns
- Strategy Pattern
- Domain Driven Modeling
- Dependency Injection

### Follow Ups
- Thread-safe expense creation
- Group support
- Multi-currency support
- Persistent storage
- Event driven settlement updates

### Why Two Pointer?
Best for one-time settlement.

### Why Heap?
Useful when balances change continuously and largest debtor-creditor matching is required.
