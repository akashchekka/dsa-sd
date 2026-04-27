# Object-Oriented Programming (OOP) – Interview Guide

## Table of Contents

1. [Four Pillars of OOP](#four-pillars-of-oop)
2. [Memory Internals & Object Layout](#memory-internals--object-layout)
3. [Classes and Objects](#classes-and-objects)
4. [C# Keywords Reference](#c-keywords-reference)
5. [Encapsulation](#encapsulation)
6. [Inheritance](#inheritance)
7. [Polymorphism](#polymorphism)
8. [Abstraction](#abstraction)
9. [SOLID Principles](#solid-principles)
10. [Design Patterns](#design-patterns)
11. [Common Interview Questions](#common-interview-questions)

---

## Four Pillars of OOP

| Pillar | Purpose |
|---|---|
| **Encapsulation** | Bundle data + methods, hide internals |
| **Inheritance** | Reuse code via parent-child relationships |
| **Polymorphism** | Same interface, different behavior |
| **Abstraction** | Expose only what's necessary, hide complexity |

---

## Memory Internals & Object Layout

Understanding how objects are laid out in memory is critical for senior-level interviews. These concepts are largely the same across C# and Java — both use managed runtimes with garbage collectors, heap/stack separation, and similar object models.

### Stack vs Heap

Every program has two main memory regions. The **stack** is a fast, LIFO (last-in, first-out) region used for method call frames — local variables, parameters, and return addresses live here. Each thread gets its own stack. When a method returns, its entire frame is popped instantly — no cleanup needed.

The **heap** is a large, shared pool of memory where objects live. Allocation on the heap is more expensive than the stack, and objects on the heap must eventually be cleaned up by the **garbage collector**. The heap is shared across all threads, which is why heap-allocated objects need synchronization when accessed from multiple threads.

```
┌─────────────────────────────────────────────────────┐
│                     PROCESS MEMORY                   │
├──────────────┬──────────────────────────────────────┤
│   STACK      │            HEAP                       │
│  (per thread)│         (shared)                      │
│              │                                       │
│  ┌────────┐  │   ┌──────────────────────────┐       │
│  │ main() │  │   │  Object: Person           │       │
│  │ p ─────│──│──►│  [Header | Name | Age ]   │       │
│  │ x = 42 │  │   └──────────────────────────┘       │
│  │ y = 3.0│  │   ┌──────────────────────────┐       │
│  ├────────┤  │   │  String: "Alice"          │       │
│  │ Foo()  │  │   │  [Header | chars[] ]      │       │
│  │ temp=7 │  │   └──────────────────────────┘       │
│  └────────┘  │                                       │
└──────────────┴──────────────────────────────────────┘
```

| Aspect | Stack | Heap |
|---|---|---|
| **Speed** | Very fast (pointer bump) | Slower (allocation + GC) |
| **Size** | Small (~1-8 MB per thread) | Large (GBs) |
| **Lifetime** | Automatic (method scope) | Until GC collects |
| **Thread safety** | Private per thread | Shared — needs synchronization |
| **What goes here** | Value types, references (pointers), method frames | Objects, arrays, strings |
| **Fragmentation** | None (LIFO) | Possible (GC compacts) |

```csharp
void Example()
{
    int x = 42;                    // x is on the STACK (value type)
    double y = 3.14;               // y is on the STACK

    Person p = new Person("Alice"); // 'p' (the reference) is on the STACK
                                    // the Person object is on the HEAP
                                    // "Alice" string is on the HEAP

    int[] arr = new int[100];       // 'arr' (reference) on STACK
                                    // the array of 100 ints on HEAP
}
// When Example() returns: x, y, p, arr popped from stack instantly
// Person and array become eligible for GC (no more references)
```

### How an Object Is Laid Out in Memory

When you create an object with `new`, the runtime allocates a contiguous block on the heap. This block contains more than just your fields — it has a **header** that the runtime uses for type information, locking, and GC tracking.

#### Object Header (Common to C# and Java)

```
┌───────────────────────────────────────────────┐
│              OBJECT ON THE HEAP                │
├───────────────┬───────────────────────────────┤
│  Object Header│  Sync block / mark word        │  ← locking, GC bits, hash code
│  (8-16 bytes) │  Type pointer / class pointer  │  ← points to class metadata (vtable)
├───────────────┼───────────────────────────────┤
│  Field: Name  │  reference → String "Alice"    │  ← 4 or 8 bytes (pointer)
│  Field: Age   │  30                            │  ← 4 bytes (int)
│  Field: Score │  95.5                          │  ← 8 bytes (double)
│  (padding)    │  ....                          │  ← alignment padding
└───────────────┴───────────────────────────────┘
```

**Object header details:**

| Component | C# (.NET) | Java (HotSpot) | Purpose |
|---|---|---|---|
| Sync block / Mark word | 4-8 bytes | 4-8 bytes | Lock state, hash code, GC age |
| Type handle / Klass pointer | 4-8 bytes | 4-8 bytes | Pointer to type metadata (vtable) |
| **Minimum overhead** | **8-16 bytes** per object | **12-16 bytes** per object | Before any fields |

This means even an empty `new Object()` costs 16 bytes on a 64-bit system. A `Boolean` field in a class uses 1 byte of data + 15 bytes of overhead (header + alignment). This is why arrays of primitives are far more memory-efficient than arrays of boxed objects.

### Where Each Kind of Member Lives

```csharp
public class Employee
{
    // STATIC FIELDS → stored once in a special area (High Frequency Heap in .NET,
    //                  Metaspace/PermGen in Java), NOT on the per-object heap
    private static int _employeeCount = 0;
    private static readonly Dictionary<int, Employee> _registry = new();

    // INSTANCE FIELDS → stored inside each object on the heap
    private string _name;          // reference field (4/8 bytes pointer on heap)
    private int _age;              // value field (4 bytes, stored inline in object)
    private Address _address;      // reference field (points to another heap object)

    // CONSTANTS → inlined at compile time, not stored at runtime at all
    private const int MaxAge = 150;

    // METHODS → stored once in code memory (JITted native code)
    //           NOT stored per object — all instances share the same code
    public void Work() { }
    public virtual void Report() { }  // virtual → resolved via vtable
}
```

```
Memory Layout:
                                                    
  ┌─ High Frequency Heap / Metaspace ──────────┐   
  │  static _employeeCount = 0                  │   
  │  static _registry → (Dictionary on heap)    │   
  └─────────────────────────────────────────────┘   
                                                    
  ┌─ Code Memory (JIT compiled) ───────────────┐   
  │  Work()   → native instructions             │   
  │  Report() → native instructions             │   
  └─────────────────────────────────────────────┘   
                                                    
  ┌─ Heap: Employee instance #1 ───────────────┐   
  │  [Header]  [_name→"Alice"]  [_age=30]       │   
  │  [_address→Address#1]                        │   
  └─────────────────────────────────────────────┘   
  ┌─ Heap: Employee instance #2 ───────────────┐   
  │  [Header]  [_name→"Bob"]  [_age=25]         │   
  │  [_address→Address#2]                        │   
  └─────────────────────────────────────────────┘   
```

| Member Type | Where Stored | How Many Copies | Lifetime |
|---|---|---|---|
| Instance fields | Heap (inside each object) | One per object | Until object is GC'd |
| Static fields | Special static area | Exactly one, ever | Entire app lifetime |
| Constants (`const`) | Inlined at compile time | Zero at runtime | N/A |
| `readonly` fields | Heap (instance) or static area | Per object or one | Object or app lifetime |
| Methods (non-virtual) | Code memory | One (shared) | App lifetime |
| Virtual methods | Code memory + vtable entry | One code + one vtable ptr/class | App lifetime |
| Local variables (value) | Stack | One per call | Method scope |
| Local variables (ref type) | Reference on stack, object on heap | One ref per call | Ref: method scope; Object: until GC'd |

### The Virtual Method Table (vtable / VMT)

When you call a `virtual` method, the runtime needs to figure out *which* implementation to call based on the actual type of the object. It does this using a **vtable** (virtual method table) — a lookup table stored once per class (not per object) that maps method slots to actual code addresses.

```
   class Animal { virtual Speak(); virtual Move(); }
   class Dog : Animal { override Speak(); }
   class Cat : Animal { override Speak(); override Move(); }

   ┌─ Animal vtable ────────┐
   │ Speak → Animal.Speak   │
   │ Move  → Animal.Move    │
   └────────────────────────┘

   ┌─ Dog vtable ───────────┐
   │ Speak → Dog.Speak      │  ← overridden
   │ Move  → Animal.Move    │  ← inherited (same pointer)
   └────────────────────────┘

   ┌─ Cat vtable ───────────┐
   │ Speak → Cat.Speak      │  ← overridden
   │ Move  → Cat.Move       │  ← overridden
   └────────────────────────┘

   Animal a = new Dog();
   a.Speak();
   // 1. Read object header → get type = Dog
   // 2. Look up Dog's vtable
   // 3. Find Speak slot → points to Dog.Speak
   // 4. Call Dog.Speak()
```

This is why `virtual` calls have a slight overhead compared to non-virtual calls — they require an extra pointer indirection through the vtable. The JIT compiler can sometimes optimize this away (devirtualization) when it can prove the exact type at compile time, especially for `sealed` classes.

**Non-virtual methods** skip the vtable entirely — the compiler knows the exact method to call at compile time (static dispatch). This is why `new` (method hiding) uses compile-time resolution while `override` uses runtime resolution.

### Boxing and Unboxing

**Boxing** is what happens when a value type (stored on the stack) needs to be treated as a reference type. The runtime allocates a new object on the heap, copies the value into it, and returns a reference. **Unboxing** is the reverse — extracting the value from the boxed object.

This matters because boxing is **expensive**: it causes a heap allocation, a memory copy, and eventually a GC collection.

```csharp
int x = 42;           // stack: 4 bytes

// BOXING: value type → heap object
object boxed = x;     // allocates 16+ bytes on heap (header + 4 bytes data)
                       // copies 42 into the heap object

// UNBOXING: heap object → value type
int y = (int)boxed;   // copies value back to stack
                       // throws InvalidCastException if types don't match

// ❌ Hidden boxing — common performance trap
ArrayList list = new ArrayList();
list.Add(42);          // boxes int → object on every Add
list.Add(3.14);        // boxes double → object

// ✅ No boxing — generic collections
List<int> list2 = new List<int>();
list2.Add(42);         // no boxing — stores int directly
```

```
Stack:                Heap:
┌─────────┐          ┌──────────────────┐
│ x = 42  │          │                  │
│ boxed ──│─────────►│ [Header] [42]    │  ← boxed int
│ y = 42  │          │                  │
└─────────┘          └──────────────────┘
```

**Where boxing silently occurs:**
- Assigning value type to `object`, `dynamic`, or interface variable
- Calling `ToString()`, `GetHashCode()`, `Equals()` on a struct that doesn't override them
- Using non-generic collections (`ArrayList`, `Hashtable`)
- String interpolation with value types (before .NET 6 optimizations)
- LINQ operations on value types without careful handling

### Value Types vs Reference Types — Memory Layout

```csharp
// VALUE TYPE (struct) — stored inline, no header, no GC
struct Point { public int X; public int Y; }    // 8 bytes total, stack or inline

// REFERENCE TYPE (class) — header + fields on heap
class PointClass { public int X; public int Y; } // 8 (header) + 8 (fields) = 24+ bytes on heap

// Value type as field in a class — stored INLINE in the object
class Line
{
    Point Start;      // 8 bytes inline (no separate heap allocation)
    Point End;        // 8 bytes inline
    PointClass Other; // 8 bytes (just a reference/pointer to heap object)
}
```

```
Line object on heap:
┌──────────────────────────────────────────────┐
│ [Header 16B] [Start.X, Start.Y] [End.X, End.Y] [Other→] │
│               8 bytes inline     8 bytes inline  pointer  │
└──────────────────────────────────────────────┘
                                                      │
                                                      ▼
                                               ┌──────────────┐
                                               │ PointClass    │
                                               │ [Header][X][Y]│
                                               └──────────────┘
```

| | Value Type (struct) | Reference Type (class) |
|---|---|---|
| **Header** | None | 8-16 bytes |
| **Location** | Stack (local) or inline in parent object | Always on heap |
| **Assignment** | Full copy of data | Copy of reference (pointer) |
| **Null** | Cannot be null (unless `Nullable<T>`) | Can be null |
| **GC pressure** | None (stack-allocated or inline) | Yes (must be collected) |
| **Identity** | No identity — compared by value | Has identity — compared by reference |
| **Best for** | Small (<16 bytes), immutable, short-lived | Large, mutable, long-lived, polymorphic |

### Garbage Collection

Since objects on the heap aren't freed manually (unlike C/C++), the runtime uses a **garbage collector (GC)** to reclaim memory. Both .NET and Java use **generational GC** based on the observation that most objects die young.

```
┌─────────────────────────────────────────────────┐
│  GENERATIONAL HEAP                               │
├──────────┬──────────┬───────────────────────────┤
│  Gen 0   │  Gen 1   │  Gen 2                    │
│ (newest) │ (middle) │ (oldest / long-lived)      │
│          │          │                            │
│ New      │ Survived │ Static refs, singletons,  │
│ objects  │ one GC   │ caches, long-lived objects │
│          │          │                            │
│ ~256 KB  │ ~2 MB    │ Grows as needed            │
│ Collected│ Less     │ Rarely collected           │
│ very     │ frequent │ (expensive — full GC)      │
│ often    │          │                            │
└──────────┴──────────┴───────────────────────────┘
    ▲ New objects are always allocated in Gen 0
    │ Objects that survive a collection get promoted to the next generation
```

**How GC works (mark-and-sweep):**

1. **Mark phase**: Starting from "roots" (static fields, local variables on stack, CPU registers), the GC traverses all reachable objects and marks them as alive.
2. **Sweep phase**: All unmarked objects are considered dead — their memory is reclaimed.
3. **Compact phase** (optional): Live objects are moved together to eliminate fragmentation. References are updated.

```csharp
void GCExample()
{
    var a = new Person("Alice");   // Gen 0
    var b = new Person("Bob");     // Gen 0
    b = null;                       // Bob is now unreachable

    // GC runs → Bob is collected, Alice survives → promoted to Gen 1
    GC.Collect(0);                  // Force Gen 0 collection (don't do this in production!)

    // Alice survives another GC → promoted to Gen 2
    GC.Collect(1);
}
```

**GC Roots — what keeps objects alive:**

| Root Type | Example | Location |
|---|---|---|
| Local variables | `var p = new Person()` | Stack |
| Static fields | `static List<User> _cache` | Static area |
| CPU registers | Currently executing references | CPU |
| Finalization queue | Objects with destructors | Runtime internal |
| Pinned objects | `GCHandle.Alloc(obj, Pinned)` | Special |

**Interview Tip:** "What keeps an object alive?" Answer: **any reachable reference from a GC root.** The moment the last reference to an object is gone (or goes out of scope), the object becomes eligible for collection — but collection doesn't happen immediately.

### Large Object Heap (LOH) / Large Arrays

Objects larger than 85,000 bytes (in .NET) are allocated on a separate **Large Object Heap** that is not compacted by default (compaction of large objects is expensive). This means large arrays and strings can cause fragmentation.

```csharp
// Small object → Gen 0 (compacted normally)
var small = new byte[1000];           // < 85KB → normal heap

// Large object → LOH (not compacted by default)
var large = new byte[100_000];        // > 85KB → Large Object Heap

// In Java: similar concept with Humongous regions in G1 GC
```

### String Interning and Immutability

Strings deserve special mention because they behave differently from other objects in both C# and Java.

```csharp
// Strings are IMMUTABLE — every "modification" creates a new object
string s1 = "hello";
string s2 = s1 + " world";   // new string allocated — s1 is unchanged

// String INTERNING — identical literals share the same object
string a = "hello";
string b = "hello";
Console.WriteLine(ReferenceEquals(a, b)); // True — same object in memory!

// Not interned — created at runtime
string c = new string("hello".ToCharArray());
Console.WriteLine(ReferenceEquals(a, c)); // False — different object

// Manual interning
string d = string.Intern(c);
Console.WriteLine(ReferenceEquals(a, d)); // True — now shares the interned copy
```

```
String Intern Pool (special area, not GC'd):
┌──────────────────────────┐
│ "hello" ← a, b point here│
│ "world"                   │
│ "hello world"             │
└──────────────────────────┘

Regular Heap:
┌──────────────────────────┐
│ "hello" ← c (separate copy, GC'd when unused) │
└──────────────────────────┘
```

**Why strings are immutable:**
- **Thread safety**: Any thread can read a string without synchronization
- **Security**: Connection strings, file paths can't be tampered with after creation
- **Hashing**: Hash code is computed once and cached (used as dictionary keys)
- **Interning**: Identical strings can safely share memory

### Memory-Efficient Patterns

```csharp
// ❌ BAD — creates many intermediate strings (N allocations)
string result = "";
for (int i = 0; i < 10000; i++)
    result += i.ToString();  // each += allocates a new string

// ✅ GOOD — single buffer, minimal allocations
var sb = new StringBuilder();
for (int i = 0; i < 10000; i++)
    sb.Append(i);
string result = sb.ToString();

// ❌ BAD — boxing value types in non-generic collection
ArrayList list = new();
list.Add(42);          // int boxed to object → heap allocation

// ✅ GOOD — no boxing with generics
List<int> list = new();
list.Add(42);          // stored directly, no boxing

// ❌ BAD — struct with reference types defeats the purpose
struct BadStruct
{
    public string Name;        // string is on heap anyway
    public List<int> Items;    // list is on heap
    // The struct itself may be on stack, but its fields point to heap
}

// ✅ GOOD — struct with only value-type fields (truly stack-allocated)
struct GoodStruct
{
    public int X;
    public int Y;
    public double Value;
}

// ✅ GOOD — Span<T> for zero-allocation slicing
ReadOnlySpan<char> span = "Hello, World!".AsSpan(0, 5); // no allocation, just a view
```

### Object Finalization and Destructor Cost

Objects with finalizers (destructors in C#) have extra overhead — they survive at least one additional GC cycle because the GC must run the finalizer before reclaiming the memory.

```
Normal object lifecycle:
  Allocate → Unreachable → GC collects → DONE

Object with finalizer:
  Allocate → Unreachable → Moved to finalization queue → Finalizer runs
           → STILL ALIVE (promoted to next generation)
           → Next GC finally collects → DONE
```

This means finalizeable objects live **at least one generation longer** than necessary. This is why the Dispose pattern exists — `Dispose()` cleans up resources immediately and calls `GC.SuppressFinalize(this)` to skip the costly finalization step.

### Memory Layout Summary

```
┌──────────────────────────────────────────────────────────────┐
│                        PROCESS MEMORY                         │
├──────────────┬───────────────────────────────────────────────┤
│              │  Managed Heap                                  │
│  Stack       │  ┌─ Gen 0 (new objects, collected often) ────┐│
│  (per thread)│  │  Gen 1 (survived 1 GC)                    ││
│  ┌────────┐  │  │  Gen 2 (long-lived, collected rarely)     ││
│  │ locals │  │  │  LOH   (>85KB, not compacted by default)  ││
│  │ params │  │  └────────────────────────────────────────────┘│
│  │ return │  │                                                │
│  │ addrs  │  │  Static Area / Metaspace                       │
│  └────────┘  │  ┌────────────────────────────────────────────┐│
│              │  │  Static fields, type metadata, vtables     ││
│              │  │  String intern pool                         ││
│              │  └────────────────────────────────────────────┘│
│              │                                                │
│              │  Code Memory                                   │
│              │  ┌────────────────────────────────────────────┐│
│              │  │  JIT-compiled native method bodies         ││
│              │  └────────────────────────────────────────────┘│
└──────────────┴───────────────────────────────────────────────┘
```

---

## Classes and Objects

A **class** is a blueprint. An **object** is an instance of that blueprint.

```csharp
public class Car
{
    public string Make { get; set; }
    public string Model { get; set; }
    public int Year { get; set; }

    public Car(string make, string model, int year)
    {
        Make = make;
        Model = model;
        Year = year;
    }

    public string GetInfo() => $"{Year} {Make} {Model}";
}

// Usage
var car = new Car("Tesla", "Model S", 2024);
Console.WriteLine(car.GetInfo()); // 2024 Tesla Model S
```

### Structs vs Classes

| Feature | Class | Struct |
|---|---|---|
| Type | Reference type | Value type |
| Heap/Stack | Heap | Stack |
| Inheritance | Yes | No |
| Default constructor | Yes | Parameterless auto-generated |
| Nullability | Can be null | Cannot (unless `Nullable<T>`) |

```csharp
public struct Point
{
    public int X { get; set; }
    public int Y { get; set; }

    public Point(int x, int y) { X = x; Y = y; }
}

Point p1 = new Point(1, 2);
Point p2 = p1;  // Value copy — p2 is independent of p1
p2.X = 10;
Console.WriteLine(p1.X); // 1 (unchanged)
```

---

## C# Keywords Reference

Understanding these keywords is essential for interviews — interviewers often ask subtle differences between them, and incorrect usage signals weak OOP fundamentals.

### `virtual`

Marks a method in a **base class** as overridable. The base class provides a default implementation, but derived classes *may* replace it. Without `virtual`, a method cannot be overridden — it's resolved at compile time.

```csharp
public class Logger
{
    public virtual void Log(string message)
    {
        Console.WriteLine($"[LOG] {message}");  // default behavior
    }
}
```

**Key points:**
- The base class *must* mark a method `virtual` to allow overriding
- Calling a `virtual` method uses **dynamic dispatch** (resolved at runtime based on actual object type)
- Fields cannot be `virtual` — only methods, properties, indexers, and events
- `virtual` methods have a small performance cost due to vtable lookup

### `override`

Used in a **derived class** to replace the behavior of a `virtual` or `abstract` method from the base class. The overridden method is called based on the **runtime type** of the object, not the variable type.

```csharp
public class FileLogger : Logger
{
    public override void Log(string message)
    {
        File.AppendAllText("log.txt", $"[FILE] {message}\n");
    }
}

Logger logger = new FileLogger();
logger.Log("hello");  // calls FileLogger.Log — runtime dispatch
```

**Key points:**
- You can only `override` a method that is `virtual`, `abstract`, or already `override`
- The method signature must match exactly (name, parameters, return type)
- An `override` method is itself implicitly `virtual` — further derived classes can override it again
- Use `base.MethodName()` to call the parent's implementation from inside the override

### `abstract`

Declares a method **with no body** — derived classes are **forced** to provide an implementation. A class containing any `abstract` member must itself be marked `abstract` and cannot be instantiated directly.

```csharp
public abstract class Shape
{
    public abstract double Area();           // no body — must override
    public abstract double Perimeter();      // no body — must override

    public void PrintInfo()                  // concrete method — inherited as-is
    {
        Console.WriteLine($"Area: {Area():F2}, Perimeter: {Perimeter():F2}");
    }
}

public class Circle : Shape
{
    public double Radius { get; }
    public Circle(double r) { Radius = r; }

    public override double Area() => Math.PI * Radius * Radius;
    public override double Perimeter() => 2 * Math.PI * Radius;
}

// Shape s = new Shape();     // ❌ Cannot instantiate abstract class
Shape s = new Circle(5);      // ✅ Must use a concrete derived class
s.PrintInfo();                 // "Area: 78.54, Perimeter: 31.42"
```

**Key points:**
- `abstract` methods can only exist in `abstract` classes
- An abstract class can have both abstract and concrete members
- If a derived class doesn't implement all abstract members, it must also be marked `abstract`
- Abstract classes can have constructors (called via `base(...)` from derived classes)

### `virtual` vs `abstract` vs `override` — Side by Side

| Keyword | Where | Body? | Must override? | Purpose |
|---|---|---|---|---|
| `virtual` | Base class | ✅ Yes (default impl) | ❌ Optional | Allow customization |
| `abstract` | Abstract base class | ❌ No body | ✅ Required | Force implementation |
| `override` | Derived class | ✅ Yes (replacement) | N/A | Replace base behavior |

### `sealed`

Prevents a class from being inherited, or prevents a method from being further overridden. Used for security (prevent behavior changes), performance (JIT can devirtualize calls), and design intent (signal "this is final").

```csharp
// Sealed class — cannot be inherited
public sealed class StringHelper
{
    public static string Capitalize(string s) => char.ToUpper(s[0]) + s[1..];
}
// class MyHelper : StringHelper { }  // ❌ Compile error

// Sealed method — prevent further overriding in the chain
public class A
{
    public virtual void Foo() => Console.WriteLine("A");
}

public class B : A
{
    public sealed override void Foo() => Console.WriteLine("B");  // no further overrides
}

public class C : B
{
    // public override void Foo() { }  // ❌ Compile error — Foo is sealed in B
}
```

**Key points:**
- `sealed` on a class: no one can inherit from it (e.g., `System.String` is sealed)
- `sealed` on a method: the override chain stops here — subclasses cannot override further
- Sealed classes give the JIT compiler optimization opportunities (devirtualization)
- All `struct` types are implicitly sealed

### `new` (Method Hiding)

Hides a base class member instead of overriding it. The method called depends on the **compile-time type** of the variable, not the runtime type. This is almost always a design smell — it breaks polymorphism.

```csharp
public class Animal
{
    public virtual void Speak() => Console.WriteLine("...");
}

public class Dog : Animal
{
    public new void Speak() => Console.WriteLine("Woof!");  // HIDES, doesn't override
}

Dog d = new Dog();
d.Speak();           // "Woof!" — variable type is Dog

Animal a = new Dog();
a.Speak();           // "..." — variable type is Animal, calls Animal.Speak!

// Compare with override:
public class Cat : Animal
{
    public override void Speak() => Console.WriteLine("Meow!");
}

Animal a2 = new Cat();
a2.Speak();          // "Meow!" — override uses runtime type
```

**Interview Tip:** If an interviewer asks "what's the difference between `new` and `override`?" — the answer is **dispatch mechanism**: `override` = runtime (vtable lookup), `new` = compile-time (based on declared variable type). Using `new` breaks the Liskov Substitution Principle.

### `static`

Belongs to the **type itself**, not to any instance. Static members are shared across all instances and can be accessed without creating an object.

```csharp
public class MathUtils
{
    public static double Pi = 3.14159;           // shared across all
    public static int Add(int a, int b) => a + b; // no instance needed

    public int InstanceValue { get; set; }         // needs an object
}

// Access without an instance
double pi = MathUtils.Pi;
int sum = MathUtils.Add(1, 2);

// Static class — cannot be instantiated, all members must be static
public static class Extensions
{
    public static string ToTitleCase(this string s)
        => CultureInfo.CurrentCulture.TextInfo.ToTitleCase(s);
}
```

**Key points:**
- Static classes cannot be instantiated or inherited
- Static constructors run once, before first access (thread-safe by CLR)
- Static fields persist for the lifetime of the AppDomain
- Extension methods must be in static classes and use `this` parameter
- Overuse of `static` makes code hard to test (can't mock/substitute)

### `readonly` vs `const`

Both represent values that don't change, but they work differently.

```csharp
public class Config
{
    public const double Pi = 3.14159;            // compile-time constant — inlined at call sites
    public const string AppName = "MyApp";       // must be known at compile time

    public readonly DateTime StartTime;           // runtime constant — set once
    public static readonly int CoreCount          // can use runtime values
        = Environment.ProcessorCount;

    public Config()
    {
        StartTime = DateTime.UtcNow;              // readonly can be set in constructor
    }
}
```

| Feature | `const` | `readonly` |
|---|---|---|
| When set | Compile time | Runtime (constructor or declaration) |
| Implicit | `static` (always) | Instance or `static` |
| Types | Primitives, `string`, `null` | Any type |
| Inlined | ✅ Yes (at call sites) | ❌ No (read from field) |
| Versioning | ⚠️ Recompile all consumers if changed | ✅ Only recompile defining assembly |

**Interview Tip:** `const` values are **baked into the calling assembly** at compile time. If you change a `const` in a library and don't recompile the consumers, they still use the old value. `readonly` avoids this problem.

### `partial`

Splits a class, struct, or interface definition across multiple files. This is commonly used for code generators (e.g., Entity Framework, WinForms designer, source generators) so that generated code and hand-written code don't conflict.

```csharp
// File: User.cs
public partial class User
{
    public string Name { get; set; }
    public void Greet() => Console.WriteLine($"Hi, I'm {Name}");
}

// File: User.Validation.cs
public partial class User
{
    public bool IsValid() => !string.IsNullOrEmpty(Name);
}

// At compile time, these merge into a single class
var user = new User { Name = "Alice" };
user.Greet();           // works
bool valid = user.IsValid(); // works — same class
```

**Partial methods** (C# 9+) allow one part to declare a method signature and another part to implement it:

```csharp
public partial class OrderProcessor
{
    partial void OnOrderPlaced(Order order);  // declaration (no body)
}

public partial class OrderProcessor
{
    partial void OnOrderPlaced(Order order)   // implementation
    {
        SendNotification(order);
    }
}
```

### `params`

Allows a method to accept a variable number of arguments. The arguments are collected into an array.

```csharp
public static int Sum(params int[] numbers)
{
    return numbers.Sum();
}

Sum(1, 2, 3);           // 6
Sum(1, 2, 3, 4, 5);     // 15
Sum();                   // 0 — empty array
Sum(new int[] { 1, 2 }); // also valid — pass array directly
```

**Key points:**
- `params` must be the last parameter
- Only one `params` parameter per method
- Behind the scenes, the compiler creates an array — there's a small allocation cost

### `ref`, `out`, `in` — Parameter Passing

These keywords control **how arguments are passed** to methods — a frequent interview topic.

```csharp
// ref — pass by reference, must be initialized before call
void Swap(ref int a, ref int b)
{
    (a, b) = (b, a);
}
int x = 1, y = 2;
Swap(ref x, ref y);  // x=2, y=1

// out — pass by reference, must be assigned inside the method
bool TryParse(string s, out int result)
{
    return int.TryParse(s, out result);
}
if (TryParse("42", out int value))
    Console.WriteLine(value);  // 42

// in — pass by readonly reference (no copy for large structs, can't modify)
double Distance(in Vector3 a, in Vector3 b)
{
    // a.X = 5;  // ❌ Compile error — 'in' is readonly
    return Math.Sqrt(
        Math.Pow(b.X - a.X, 2) +
        Math.Pow(b.Y - a.Y, 2) +
        Math.Pow(b.Z - a.Z, 2));
}
```

| Keyword | Must init before call | Must assign in method | Caller can read | Method can modify |
|---|---|---|---|---|
| `ref` | ✅ | ❌ | ✅ | ✅ |
| `out` | ❌ | ✅ | ❌ (until assigned) | ✅ |
| `in` | ✅ | ❌ | ✅ | ❌ (readonly) |
| (none) | ✅ | ❌ | ✅ | Copy only |

### `is` and `as` — Type Checking and Casting

```csharp
object obj = "hello";

// 'is' — type check (returns bool)
if (obj is string s)           // pattern matching — checks AND casts
{
    Console.WriteLine(s.ToUpper());  // "HELLO"
}

if (obj is not null and string) { } // combined patterns

// 'as' — safe cast (returns null on failure instead of throwing)
string str = obj as string;    // "hello" or null
int? num = obj as int?;        // null (obj is not int)

// Direct cast — throws InvalidCastException on failure
string str2 = (string)obj;     // works
int num2 = (int)obj;           // ❌ InvalidCastException
```

| | `is` | `as` | Direct cast `(T)` |
|---|---|---|---|
| Returns | `bool` | `T` or `null` | `T` or throws |
| On failure | `false` | `null` | `InvalidCastException` |
| Value types | ✅ (with pattern) | ❌ (only reference/nullable) | ✅ |
| Best for | Conditional logic | When null is acceptable | When failure is a bug |

### `using` — Resource Management

The `using` keyword has three meanings in C#:

```csharp
// 1. Import namespace
using System.Collections.Generic;

// 2. Dispose pattern — guarantees cleanup
using var conn = new SqlConnection(connString);  // disposed at end of scope
conn.Open();
// conn.Dispose() called automatically, even if exception occurs

// Equivalent to:
var conn2 = new SqlConnection(connString);
try { conn2.Open(); }
finally { conn2.Dispose(); }

// 3. Type alias
using UserId = System.Int32;
using UserMap = System.Collections.Generic.Dictionary<string, User>;
```

### Keywords Quick Reference

```
virtual          → "You MAY override me" (base class, has body)
abstract         → "You MUST override me" (no body, class must be abstract)
override         → "I AM replacing the base behavior" (runtime dispatch)
new              → "I AM hiding the base member" (compile-time, breaks polymorphism)
sealed           → "No one can inherit/override further"
static           → "Belongs to the type, not an instance"
readonly         → "Set once (constructor or declaration), then immutable"
const            → "Compile-time constant, inlined everywhere"
partial          → "This type is split across multiple files"
params           → "Accept variable number of arguments"
ref              → "Pass by reference (read + write)"
out              → "Pass by reference (write required, then read)"
in               → "Pass by readonly reference (read only, no copy)"
is               → "Type check + pattern match"
as               → "Safe cast (returns null on failure)"
using            → "Import namespace / dispose resource / type alias"
```

---

## Encapsulation

Hide internal state and require interaction through well-defined methods.

### Access Modifiers

| Modifier | Accessibility |
|---|---|
| `public` | Everywhere |
| `private` | Same class only |
| `protected` | Same class + derived classes |
| `internal` | Same assembly |
| `protected internal` | Same assembly OR derived classes |
| `private protected` | Same assembly AND derived classes |

```csharp
public class BankAccount
{
    private decimal _balance;           // hidden from outside
    public string AccountHolder { get; private set; }  // read-only from outside

    public BankAccount(string holder, decimal initialBalance)
    {
        AccountHolder = holder;
        _balance = initialBalance;
    }

    public decimal GetBalance() => _balance;

    public void Deposit(decimal amount)
    {
        if (amount <= 0) throw new ArgumentException("Amount must be positive");
        _balance += amount;
    }

    public void Withdraw(decimal amount)
    {
        if (amount <= 0) throw new ArgumentException("Amount must be positive");
        if (amount > _balance) throw new InvalidOperationException("Insufficient funds");
        _balance -= amount;
    }
}
```

**Interview Tip:** Encapsulation != just making fields private. It's about controlling access and ensuring object invariants are always valid.

---

## Inheritance

A class derives from another class, inheriting its members.

```csharp
public class Animal
{
    public string Name { get; set; }

    public Animal(string name) { Name = name; }

    public virtual void Speak() => Console.WriteLine($"{Name} makes a sound");
}

public class Dog : Animal
{
    public string Breed { get; set; }

    public Dog(string name, string breed) : base(name)
    {
        Breed = breed;
    }

    public override void Speak() => Console.WriteLine($"{Name} barks");
}

public class Cat : Animal
{
    public Cat(string name) : base(name) { }

    public override void Speak() => Console.WriteLine($"{Name} meows");
}
```

### Types of Inheritance

| Type | C# Support |
|---|---|
| Single | ✅ `class B : A` |
| Multilevel | ✅ `class C : B`, `class B : A` |
| Multiple (classes) | ❌ Not supported |
| Multiple (interfaces) | ✅ `class A : IFoo, IBar` |
| Hierarchical | ✅ Multiple classes derive from one base |

### `sealed` — Prevent Inheritance

```csharp
public sealed class Singleton
{
    private static readonly Singleton _instance = new();
    private Singleton() { }
    public static Singleton Instance => _instance;
}
// class Derived : Singleton { } // ❌ Compile error
```

### `new` Keyword — Method Hiding

```csharp
public class Base
{
    public void Show() => Console.WriteLine("Base");
}

public class Derived : Base
{
    public new void Show() => Console.WriteLine("Derived");
}

Base obj = new Derived();
obj.Show();  // "Base" — method hiding, NOT polymorphism
```

**Interview Tip:** `new` hides the base method (compile-time resolution). `override` replaces it (runtime resolution). This is a classic interview question.

---

## Polymorphism

### Compile-Time (Static) — Method Overloading

```csharp
public class Calculator
{
    public int Add(int a, int b) => a + b;
    public double Add(double a, double b) => a + b;
    public int Add(int a, int b, int c) => a + b + c;
}
```

### Run-Time (Dynamic) — Method Overriding

```csharp
public abstract class Shape
{
    public abstract double Area();
    public virtual string Describe() => $"Shape with area {Area():F2}";
}

public class Circle : Shape
{
    public double Radius { get; }
    public Circle(double radius) { Radius = radius; }

    public override double Area() => Math.PI * Radius * Radius;
    public override string Describe() => $"Circle: radius={Radius}, area={Area():F2}";
}

public class Rectangle : Shape
{
    public double Width { get; }
    public double Height { get; }
    public Rectangle(double w, double h) { Width = w; Height = h; }

    public override double Area() => Width * Height;
}

// Polymorphism in action
List<Shape> shapes = new() { new Circle(5), new Rectangle(4, 6) };
foreach (var shape in shapes)
    Console.WriteLine(shape.Describe()); // Calls the correct override
```

### Operator Overloading

```csharp
public class Vector2D
{
    public double X { get; }
    public double Y { get; }

    public Vector2D(double x, double y) { X = x; Y = y; }

    public static Vector2D operator +(Vector2D a, Vector2D b)
        => new(a.X + b.X, a.Y + b.Y);

    public static Vector2D operator -(Vector2D a, Vector2D b)
        => new(a.X - b.X, a.Y - b.Y);

    public override string ToString() => $"({X}, {Y})";
}

var v = new Vector2D(1, 2) + new Vector2D(3, 4); // (4, 6)
```

---

## Abstraction

### Abstract Classes

- Cannot be instantiated
- Can have abstract (no body) and concrete (with body) members
- Can have constructors, fields, state

```csharp
public abstract class PaymentProcessor
{
    public string MerchantId { get; }

    protected PaymentProcessor(string merchantId) { MerchantId = merchantId; }

    public abstract bool ProcessPayment(decimal amount);  // must override
    public virtual void LogTransaction(decimal amount)     // can override
        => Console.WriteLine($"[{MerchantId}] Processed: ${amount}");

    public void Execute(decimal amount)   // template method pattern
    {
        if (ProcessPayment(amount))
            LogTransaction(amount);
    }
}

public class StripeProcessor : PaymentProcessor
{
    public StripeProcessor() : base("STRIPE") { }

    public override bool ProcessPayment(decimal amount)
    {
        Console.WriteLine($"Charging ${amount} via Stripe API");
        return true;
    }
}
```

### Interfaces

- Pure contract — no state, no constructors
- A class can implement multiple interfaces
- Since C# 8: default interface methods allowed

```csharp
public interface IRepository<T>
{
    T GetById(int id);
    IEnumerable<T> GetAll();
    void Add(T entity);
    void Delete(int id);
}

public interface IAuditable
{
    DateTime CreatedAt { get; }
    DateTime? UpdatedAt { get; }
}

public class UserRepository : IRepository<User>, IAuditable
{
    private readonly List<User> _users = new();

    public DateTime CreatedAt { get; } = DateTime.UtcNow;
    public DateTime? UpdatedAt { get; private set; }

    public User GetById(int id) => _users.FirstOrDefault(u => u.Id == id);
    public IEnumerable<User> GetAll() => _users.AsReadOnly();

    public void Add(User entity)
    {
        _users.Add(entity);
        UpdatedAt = DateTime.UtcNow;
    }

    public void Delete(int id)
    {
        _users.RemoveAll(u => u.Id == id);
        UpdatedAt = DateTime.UtcNow;
    }
}
```

### Abstract Class vs Interface

| Feature | Abstract Class | Interface |
|---|---|---|
| Multiple inheritance | ❌ | ✅ |
| Constructors | ✅ | ❌ |
| Fields / state | ✅ | ❌ (properties only) |
| Access modifiers on members | ✅ | ❌ (public by default) |
| Default implementations | ✅ (always) | ✅ (C# 8+) |
| Use when | Shared state/behavior among related classes | Defining a capability contract |

---

## SOLID Principles

### S — Single Responsibility Principle

> A class should have only one reason to change.

```csharp
// ❌ Bad — one class does everything
public class UserService
{
    public void Register(User user) { /* save to DB */ }
    public void SendEmail(User user) { /* send welcome email */ }
    public string GenerateReport(User user) { /* build PDF */ }
}

// ✅ Good — each class has one job
public class UserRepository { public void Save(User user) { } }
public class EmailService { public void SendWelcome(User user) { } }
public class ReportGenerator { public string Generate(User user) => ""; }
```

### O — Open/Closed Principle

> Open for extension, closed for modification.

```csharp
// ✅ Add new discount types without modifying existing code
public interface IDiscountStrategy
{
    decimal Apply(decimal price);
}

public class RegularDiscount : IDiscountStrategy
{
    public decimal Apply(decimal price) => price * 0.9m;
}

public class PremiumDiscount : IDiscountStrategy
{
    public decimal Apply(decimal price) => price * 0.8m;
}

public class PricingEngine
{
    public decimal CalculatePrice(decimal price, IDiscountStrategy strategy)
        => strategy.Apply(price);
}
```

### L — Liskov Substitution Principle

> Subtypes must be substitutable for their base types without breaking behavior.

```csharp
// ❌ Bad — Square violates Rectangle's contract
public class Rectangle
{
    public virtual int Width { get; set; }
    public virtual int Height { get; set; }
    public int Area => Width * Height;
}

public class Square : Rectangle
{
    public override int Width
    {
        get => base.Width;
        set { base.Width = value; base.Height = value; }
    }
    public override int Height
    {
        get => base.Height;
        set { base.Height = value; base.Width = value; }
    }
}

// ✅ Good — use a common interface
public interface IShape
{
    int Area { get; }
}

public class RectangleFixed : IShape
{
    public int Width { get; set; }
    public int Height { get; set; }
    public int Area => Width * Height;
}

public class SquareFixed : IShape
{
    public int Side { get; set; }
    public int Area => Side * Side;
}
```

### I — Interface Segregation Principle

> Clients should not be forced to depend on methods they don't use.

```csharp
// ❌ Bad — fat interface
public interface IWorker
{
    void Work();
    void Eat();
    void Sleep();
}

// ✅ Good — segregated interfaces
public interface IWorkable { void Work(); }
public interface IFeedable { void Eat(); }
public interface ISleepable { void Sleep(); }

public class HumanWorker : IWorkable, IFeedable, ISleepable
{
    public void Work() => Console.WriteLine("Working");
    public void Eat() => Console.WriteLine("Eating");
    public void Sleep() => Console.WriteLine("Sleeping");
}

public class Robot : IWorkable  // Robots don't eat or sleep
{
    public void Work() => Console.WriteLine("Working 24/7");
}
```

### D — Dependency Inversion Principle

> Depend on abstractions, not concretions.

```csharp
// ❌ Bad — high-level module depends on low-level module
public class MySqlDatabase { public void Save(string data) { } }

public class OrderServiceBad
{
    private readonly MySqlDatabase _db = new();
    public void PlaceOrder(string order) => _db.Save(order);
}

// ✅ Good — both depend on an abstraction
public interface IDatabase
{
    void Save(string data);
}

public class MySqlDb : IDatabase { public void Save(string data) { } }
public class MongoDb : IDatabase { public void Save(string data) { } }

public class OrderService
{
    private readonly IDatabase _db;
    public OrderService(IDatabase db) { _db = db; }   // injected
    public void PlaceOrder(string order) => _db.Save(order);
}
```

---

## Design Patterns

### Creational

#### Singleton

```csharp
public sealed class Logger
{
    private static readonly Lazy<Logger> _instance = new(() => new Logger());
    private Logger() { }
    public static Logger Instance => _instance.Value;

    public void Log(string message) => Console.WriteLine($"[{DateTime.UtcNow}] {message}");
}
```

#### Factory Method

```csharp
public abstract class Notification
{
    public abstract void Send(string message);
}

public class EmailNotification : Notification
{
    public override void Send(string message) => Console.WriteLine($"Email: {message}");
}

public class SmsNotification : Notification
{
    public override void Send(string message) => Console.WriteLine($"SMS: {message}");
}

public class PushNotification : Notification
{
    public override void Send(string message) => Console.WriteLine($"Push: {message}");
}

public static class NotificationFactory
{
    public static Notification Create(string type) => type.ToLower() switch
    {
        "email" => new EmailNotification(),
        "sms"   => new SmsNotification(),
        "push"  => new PushNotification(),
        _ => throw new ArgumentException($"Unknown type: {type}")
    };
}
```

#### Builder

```csharp
public class HttpRequest
{
    public string Url { get; set; }
    public string Method { get; set; }
    public Dictionary<string, string> Headers { get; set; } = new();
    public string Body { get; set; }
}

public class HttpRequestBuilder
{
    private readonly HttpRequest _request = new();

    public HttpRequestBuilder SetUrl(string url) { _request.Url = url; return this; }
    public HttpRequestBuilder SetMethod(string method) { _request.Method = method; return this; }
    public HttpRequestBuilder AddHeader(string key, string value)
    {
        _request.Headers[key] = value;
        return this;
    }
    public HttpRequestBuilder SetBody(string body) { _request.Body = body; return this; }

    public HttpRequest Build() => _request;
}

// Usage
var request = new HttpRequestBuilder()
    .SetUrl("https://api.example.com/users")
    .SetMethod("POST")
    .AddHeader("Content-Type", "application/json")
    .SetBody("{\"name\": \"John\"}")
    .Build();
```

### Structural

#### Adapter

```csharp
// Legacy system returns XML
public class LegacyApi
{
    public string GetDataXml() => "<data><name>John</name></data>";
}

// New system expects JSON
public interface IModernApi
{
    string GetDataJson();
}

public class LegacyApiAdapter : IModernApi
{
    private readonly LegacyApi _legacy;
    public LegacyApiAdapter(LegacyApi legacy) { _legacy = legacy; }

    public string GetDataJson()
    {
        string xml = _legacy.GetDataXml();
        // Convert XML → JSON (simplified)
        return "{\"name\": \"John\"}";
    }
}
```

#### Decorator

```csharp
public interface IDataSource
{
    string Read();
    void Write(string data);
}

public class FileDataSource : IDataSource
{
    private string _data = "";
    public string Read() => _data;
    public void Write(string data) => _data = data;
}

public class EncryptionDecorator : IDataSource
{
    private readonly IDataSource _source;
    public EncryptionDecorator(IDataSource source) { _source = source; }

    public string Read() => Decrypt(_source.Read());
    public void Write(string data) => _source.Write(Encrypt(data));

    private string Encrypt(string data) => Convert.ToBase64String(
        System.Text.Encoding.UTF8.GetBytes(data));
    private string Decrypt(string data) => System.Text.Encoding.UTF8.GetString(
        Convert.FromBase64String(data));
}

public class CompressionDecorator : IDataSource
{
    private readonly IDataSource _source;
    public CompressionDecorator(IDataSource source) { _source = source; }

    public string Read() => Decompress(_source.Read());
    public void Write(string data) => _source.Write(Compress(data));

    private string Compress(string data) => data;   // simplified
    private string Decompress(string data) => data;
}

// Stack decorators
IDataSource source = new CompressionDecorator(
    new EncryptionDecorator(
        new FileDataSource()));
source.Write("secret data");
```

### Behavioral

#### Observer

```csharp
public interface IObserver<T>
{
    void Update(T data);
}

public class EventBus<T>
{
    private readonly List<IObserver<T>> _observers = new();

    public void Subscribe(IObserver<T> observer) => _observers.Add(observer);
    public void Unsubscribe(IObserver<T> observer) => _observers.Remove(observer);

    public void Publish(T data)
    {
        foreach (var observer in _observers)
            observer.Update(data);
    }
}

public class OrderPlacedEvent
{
    public int OrderId { get; set; }
    public decimal Total { get; set; }
}

public class InventoryService : IObserver<OrderPlacedEvent>
{
    public void Update(OrderPlacedEvent data)
        => Console.WriteLine($"Inventory: Reserving stock for order {data.OrderId}");
}

public class BillingService : IObserver<OrderPlacedEvent>
{
    public void Update(OrderPlacedEvent data)
        => Console.WriteLine($"Billing: Charging ${data.Total} for order {data.OrderId}");
}
```

#### Strategy

```csharp
public interface ISortStrategy<T>
{
    void Sort(List<T> list);
}

public class QuickSort<T> : ISortStrategy<T> where T : IComparable<T>
{
    public void Sort(List<T> list) => list.Sort();  // simplified
}

public class BubbleSort<T> : ISortStrategy<T> where T : IComparable<T>
{
    public void Sort(List<T> list)
    {
        for (int i = 0; i < list.Count; i++)
            for (int j = 0; j < list.Count - i - 1; j++)
                if (list[j].CompareTo(list[j + 1]) > 0)
                    (list[j], list[j + 1]) = (list[j + 1], list[j]);
    }
}

public class Sorter<T> where T : IComparable<T>
{
    private ISortStrategy<T> _strategy;
    public void SetStrategy(ISortStrategy<T> strategy) => _strategy = strategy;
    public void Sort(List<T> list) => _strategy.Sort(list);
}
```

---

## Common Interview Questions

### 1. Composition vs Inheritance

> **"Favor composition over inheritance"** — Gang of Four

```csharp
// ❌ Inheritance — tightly coupled
public class Engine { public void Start() { } }
public class CarBad : Engine { }  // A car IS-NOT an engine

// ✅ Composition — loosely coupled
public class CarGood
{
    private readonly Engine _engine;  // A car HAS an engine
    public CarGood(Engine engine) { _engine = engine; }
    public void Start() => _engine.Start();
}
```

**When to use inheritance:** true IS-A relationship (Dog IS-A Animal).
**When to use composition:** HAS-A relationship (Car HAS-A Engine).

### 2. Shallow Copy vs Deep Copy

```csharp
public class Address
{
    public string City { get; set; }
}

public class Person : ICloneable
{
    public string Name { get; set; }
    public Address Address { get; set; }

    // Shallow copy — Address is shared
    public object Clone() => MemberwiseClone();

    // Deep copy — Address is duplicated
    public Person DeepClone() => new()
    {
        Name = Name,
        Address = new Address { City = Address.City }
    };
}

var p1 = new Person { Name = "Alice", Address = new Address { City = "NYC" } };

var p2 = (Person)p1.Clone();      // shallow
p2.Address.City = "LA";
Console.WriteLine(p1.Address.City); // "LA" ← both affected!

var p3 = p1.DeepClone();           // deep
p3.Address.City = "Chicago";
Console.WriteLine(p1.Address.City); // "LA" ← p1 unaffected
```

### 3. `virtual` vs `abstract` vs `interface`

| | `virtual` | `abstract` | `interface` |
|---|---|---|---|
| Has body | ✅ | ❌ | ❌ (or default since C#8) |
| Must override | ❌ | ✅ | ✅ |
| Can have state | ✅ | ✅ | ❌ |
| Multiple | N/A | Single base only | Multiple |

### 4. `==` vs `.Equals()` vs `ReferenceEquals()`

```csharp
string a = "hello";
string b = "hello";
string c = new string("hello");

Console.WriteLine(a == b);                       // True (value comparison for strings)
Console.WriteLine(a.Equals(b));                   // True
Console.WriteLine(ReferenceEquals(a, b));          // True (string interning)
Console.WriteLine(ReferenceEquals(a, c));          // False (different object)
```

### 5. Generics and Constraints

```csharp
public class Repository<T> where T : class, IEntity, new()
{
    private readonly List<T> _items = new();

    public T Create()
    {
        var entity = new T();   // possible because of new() constraint
        _items.Add(entity);
        return entity;
    }

    public T FindById(int id) => _items.FirstOrDefault(x => x.Id == id);
}

public interface IEntity { int Id { get; set; } }
```

| Constraint | Meaning |
|---|---|
| `where T : class` | Reference type |
| `where T : struct` | Value type |
| `where T : new()` | Has parameterless constructor |
| `where T : BaseClass` | Derives from BaseClass |
| `where T : IInterface` | Implements IInterface |
| `where T : notnull` | Non-nullable |

### 6. Delegates, Events, and Lambdas

```csharp
// Delegate
public delegate bool Predicate<T>(T item);

// Func / Action — built-in delegates
Func<int, int, int> add = (a, b) => a + b;      // returns int
Action<string> print = msg => Console.WriteLine(msg); // returns void
Predicate<int> isEven = n => n % 2 == 0;

// Events
public class Button
{
    public event EventHandler<string> Clicked;

    public void Click()
    {
        Clicked?.Invoke(this, "Button was clicked");
    }
}

var button = new Button();
button.Clicked += (sender, msg) => Console.WriteLine(msg);
button.Click(); // "Button was clicked"
```

### 7. Dependency Injection in Practice

```csharp
// Registration (ASP.NET Core)
builder.Services.AddScoped<IOrderRepository, SqlOrderRepository>();
builder.Services.AddTransient<IEmailService, SmtpEmailService>();
builder.Services.AddSingleton<ICacheService, RedisCacheService>();

// Usage — constructor injection
public class OrderController : ControllerBase
{
    private readonly IOrderRepository _repo;
    private readonly IEmailService _email;

    public OrderController(IOrderRepository repo, IEmailService email)
    {
        _repo = repo;
        _email = email;
    }
}
```

| Lifetime | Behavior |
|---|---|
| `Transient` | New instance every time |
| `Scoped` | One instance per request |
| `Singleton` | One instance for app lifetime |

### 8. Records (C# 9+)

```csharp
public record Person(string Name, int Age);

var p1 = new Person("Alice", 30);
var p2 = new Person("Alice", 30);

Console.WriteLine(p1 == p2);      // True — value equality
Console.WriteLine(p1.Equals(p2)); // True

var p3 = p1 with { Age = 31 };    // Non-destructive mutation
Console.WriteLine(p3);            // Person { Name = Alice, Age = 31 }
```

### 9. Covariance and Contravariance

```csharp
// Covariance (out) — can return more derived type
IEnumerable<Animal> animals = new List<Dog>(); // ✅ Dog is Animal

// Contravariance (in) — can accept more base type
Action<Dog> dogAction = (Animal a) => Console.WriteLine(a.Name); // ✅

public interface IProducer<out T> { T Produce(); }       // covariant
public interface IConsumer<in T>  { void Consume(T item); } // contravariant
```

### 10. Dispose Pattern and `IDisposable`

```csharp
public class DatabaseConnection : IDisposable
{
    private bool _disposed;
    private IntPtr _handle;  // unmanaged resource

    public void Execute(string query)
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        Console.WriteLine($"Executing: {query}");
    }

    protected virtual void Dispose(bool disposing)
    {
        if (_disposed) return;

        if (disposing)
        {
            // Free managed resources
        }

        // Free unmanaged resources
        _handle = IntPtr.Zero;
        _disposed = true;
    }

    public void Dispose()
    {
        Dispose(true);
        GC.SuppressFinalize(this);
    }

    ~DatabaseConnection() => Dispose(false);
}

// Always use 'using' to guarantee disposal
using var conn = new DatabaseConnection();
conn.Execute("SELECT * FROM Users");
```

---

## Quick Reference Cheat Sheet

```
Class vs Struct         → Reference vs Value type
Abstract vs Interface   → State + single inheritance vs Contract + multiple implementation
virtual vs abstract     → Optional vs Required override
new vs override         → Compile-time hiding vs Runtime polymorphism
== vs Equals            → Operator (customizable) vs Method (override for value equality)
Shallow vs Deep copy    → Shared refs vs Independent copy
Composition vs Inherit  → HAS-A vs IS-A
Covariance (out)        → Produce derived types
Contravariance (in)     → Consume base types
```