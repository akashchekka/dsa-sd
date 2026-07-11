# Design Patterns in Python — Simple Guide

A practical, easy-to-read reference for the design patterns you actually use in machine coding rounds and real code. Each pattern has:

- **What it is** — one line.
- **When to use** — the trigger.
- **Python example** — minimal, runnable.
- **Real-world use** — where you've seen it.

> Tip: In Python, many GoF patterns collapse because functions are first-class, modules are singletons, and duck typing replaces explicit interfaces. Use the pattern only when it adds clarity.

---

## Table of Contents

**Creational** — how objects are created

1. [Singleton](#1-singleton)
2. [Factory](#2-factory)
3. [Abstract Factory](#3-abstract-factory)
4. [Builder](#4-builder)
5. [Prototype](#5-prototype)

**Structural** — how objects compose

6. [Adapter](#6-adapter)
7. [Decorator](#7-decorator)
8. [Facade](#8-facade)
9. [Composite](#9-composite)
10. [Proxy](#10-proxy)

**Behavioral** — how objects interact

11. [Strategy](#11-strategy)
12. [Observer](#12-observer)
13. [Command](#13-command)
14. [State](#14-state)
15. [Template Method](#15-template-method)
16. [Iterator](#16-iterator)
17. [Chain of Responsibility](#17-chain-of-responsibility)

---

## Creational Patterns

### 1. Singleton

**What:** Only one instance of a class exists.
**When:** Logger, config, connection pool, ID generator.

```python
class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def log(self, msg):
        print(f"[LOG] {msg}")

a = Logger()
b = Logger()
print(a is b)   # True — same object
```

**Pythonic shortcut:** a module is already a singleton.

```python
# logger.py
def log(msg): print(f"[LOG] {msg}")
# just `import logger` everywhere
```

---

### 2. Factory

**What:** A function/class decides which concrete object to create.
**When:** You want callers to ask for "a sender" without knowing if it's email/SMS.

```python
class EmailSender:
    def send(self, msg): print(f"Email: {msg}")

class SmsSender:
    def send(self, msg): print(f"SMS: {msg}")

class NotifierFactory:
    @staticmethod
    def create(kind: str):
        if kind == "email": return EmailSender()
        if kind == "sms":   return SmsSender()
        raise ValueError(kind)

NotifierFactory.create("email").send("hi")
NotifierFactory.create("sms").send("hi")
```

**Real use:** [notification_service](../machine-coding-py/notification_service/), payment processors, DB drivers.

---

### 3. Abstract Factory

**What:** A factory that creates *families* of related objects.
**When:** UI toolkit needs `Button + Window + Menu` per OS (Mac, Windows).

```python
from abc import ABC, abstractmethod

class Button(ABC):
    @abstractmethod
    def click(self): ...

class MacButton(Button):
    def click(self): print("Mac click")

class WinButton(Button):
    def click(self): print("Windows click")

class UIFactory(ABC):
    @abstractmethod
    def make_button(self) -> Button: ...

class MacFactory(UIFactory):
    def make_button(self): return MacButton()

class WinFactory(UIFactory):
    def make_button(self): return WinButton()

def app(factory: UIFactory):
    factory.make_button().click()

app(MacFactory())   # Mac click
app(WinFactory())   # Windows click
```

---

### 4. Builder

**What:** Build a complex object step-by-step.
**When:** Object has many optional fields and you want readable construction.

```python
class Pizza:
    def __init__(self):
        self.size = None
        self.cheese = False
        self.toppings = []

    def __repr__(self):
        return f"Pizza(size={self.size}, cheese={self.cheese}, toppings={self.toppings})"

class PizzaBuilder:
    def __init__(self):
        self.pizza = Pizza()

    def size(self, s):       self.pizza.size = s;       return self
    def add_cheese(self):    self.pizza.cheese = True;  return self
    def add(self, topping):  self.pizza.toppings.append(topping); return self
    def build(self):         return self.pizza

p = PizzaBuilder().size("large").add_cheese().add("mushroom").add("olives").build()
print(p)
```

**Pythonic shortcut:** dataclasses + keyword args often replace Builder.

---

### 5. Prototype

**What:** Copy an existing object instead of building from scratch.
**When:** Construction is expensive; you want a clone.

```python
import copy

class Document:
    def __init__(self, title, content, tags):
        self.title, self.content, self.tags = title, content, list(tags)

template = Document("Template", "Hello {name}", ["draft"])
clone    = copy.deepcopy(template)
clone.title = "Welcome Aakash"
print(template.title, "|", clone.title)
```

---

## Structural Patterns

### 6. Adapter

**What:** Wrap an incompatible interface so it looks like the one you expect.
**When:** Third-party class has a different method name; you can't change it.

```python
class OldPrinter:
    def print_text(self, text): print(f"OLD: {text}")

class NewPrinter:
    def show(self, text): print(f"NEW: {text}")

# We want everyone to use .show(...). Adapt OldPrinter.
class PrinterAdapter:
    def __init__(self, old: OldPrinter):
        self.old = old
    def show(self, text):
        self.old.print_text(text)

printers = [NewPrinter(), PrinterAdapter(OldPrinter())]
for p in printers:
    p.show("hello")
```

---

### 7. Decorator

**What:** Add behavior to an object without modifying its class.
**When:** Logging, caching, auth, retry — cross-cutting concerns.

```python
# Function decorator (very Pythonic)
import time
from functools import wraps

def timed(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        start = time.perf_counter()
        out   = fn(*a, **kw)
        print(f"{fn.__name__} took {time.perf_counter()-start:.4f}s")
        return out
    return wrapper

@timed
def slow():
    time.sleep(0.1)

slow()
```

Class-style (classic GoF):

```python
class Coffee:
    def cost(self): return 5

class MilkDecorator:
    def __init__(self, coffee): self.coffee = coffee
    def cost(self): return self.coffee.cost() + 2

class SugarDecorator:
    def __init__(self, coffee): self.coffee = coffee
    def cost(self): return self.coffee.cost() + 1

drink = SugarDecorator(MilkDecorator(Coffee()))
print(drink.cost())   # 8
```

---

### 8. Facade

**What:** One simple class hides a messy subsystem.
**When:** Client shouldn't know about 5 internal modules.

```python
class CPU:    def start(self):  print("CPU start")
class Memory: def load(self):   print("Memory load")
class Disk:   def read(self):   print("Disk read")

class Computer:                         # Facade
    def __init__(self):
        self.cpu, self.mem, self.disk = CPU(), Memory(), Disk()
    def boot(self):
        self.cpu.start(); self.mem.load(); self.disk.read()

Computer().boot()
```

**Real use:** SDK wrappers (`boto3.client("s3")`), service classes in machine coding.

---

### 9. Composite

**What:** Treat a single object and a group of objects uniformly.
**When:** Trees — file system, UI components, org chart.

```python
from abc import ABC, abstractmethod

class FileNode(ABC):
    @abstractmethod
    def size(self) -> int: ...

class File(FileNode):
    def __init__(self, name, sz): self.name, self.sz = name, sz
    def size(self): return self.sz

class Folder(FileNode):
    def __init__(self, name): self.name, self.children = name, []
    def add(self, node): self.children.append(node); return self
    def size(self): return sum(c.size() for c in self.children)

root = (Folder("root")
        .add(File("a.txt", 100))
        .add(Folder("sub").add(File("b.txt", 200)).add(File("c.txt", 50))))
print(root.size())   # 350
```

---

### 10. Proxy

**What:** A stand-in that controls access to the real object.
**When:** Lazy loading, access control, caching, remote calls.

```python
class Image:
    def __init__(self, path):
        self.path = path
        print(f"Loading {path}...")          # expensive
    def render(self): print(f"Render {self.path}")

class ImageProxy:
    def __init__(self, path):
        self.path = path
        self._real = None
    def render(self):
        if self._real is None:               # lazy
            self._real = Image(self.path)
        self._real.render()

img = ImageProxy("photo.jpg")   # no load yet
img.render()                    # loads, then renders
img.render()                    # just renders
```

---

## Behavioral Patterns

### 11. Strategy

**What:** Swap algorithms behind a common interface.
**When:** Pricing, matching, sorting, retry policy, compression.

```python
from abc import ABC, abstractmethod

class PaymentStrategy(ABC):
    @abstractmethod
    def pay(self, amount): ...

class CreditCard(PaymentStrategy):
    def pay(self, amount): print(f"Charge card ${amount}")

class Upi(PaymentStrategy):
    def pay(self, amount): print(f"UPI ${amount}")

class Checkout:
    def __init__(self, strategy: PaymentStrategy):
        self.strategy = strategy
    def buy(self, amount):
        self.strategy.pay(amount)

Checkout(CreditCard()).buy(100)
Checkout(Upi()).buy(100)
```

**Real use:** Everywhere in [machine-coding-py](../machine-coding-py/) — pricing, matching, rate-limit algorithms.

---

### 12. Observer (Pub-Sub)

**What:** When one object changes, notify all listeners.
**When:** Event systems, UI, notifications, order status updates.

```python
class Subject:
    def __init__(self):
        self._observers = []
    def subscribe(self, fn): self._observers.append(fn)
    def notify(self, event):
        for fn in self._observers:
            fn(event)

orders = Subject()
orders.subscribe(lambda e: print(f"Email: {e}"))
orders.subscribe(lambda e: print(f"SMS:   {e}"))
orders.notify("Order #42 placed")
```

**Real use:** [pub_sub](../machine-coding-py/pub_sub/), [notification_service](../machine-coding-py/notification_service/).

---

### 13. Command

**What:** Wrap a request as an object so you can queue, log, undo.
**When:** Undo/redo, task queue, macro recording.

```python
from abc import ABC, abstractmethod

class Command(ABC):
    @abstractmethod
    def execute(self): ...
    @abstractmethod
    def undo(self): ...

class Light:
    def on(self):  print("Light ON")
    def off(self): print("Light OFF")

class LightOnCommand(Command):
    def __init__(self, light): self.light = light
    def execute(self): self.light.on()
    def undo(self):    self.light.off()

class Remote:
    def __init__(self): self.history = []
    def press(self, cmd):
        cmd.execute()
        self.history.append(cmd)
    def undo(self):
        if self.history: self.history.pop().undo()

r = Remote()
r.press(LightOnCommand(Light()))
r.undo()
```

---

### 14. State

**What:** Object's behavior changes based on internal state — without giant `if` chains.
**When:** Trip lifecycle, order lifecycle, vending machine, TCP connection.

```python
from abc import ABC, abstractmethod

class State(ABC):
    @abstractmethod
    def next(self, ctx): ...

class Draft(State):
    def next(self, ctx):
        print("Draft -> Submitted"); ctx.state = Submitted()

class Submitted(State):
    def next(self, ctx):
        print("Submitted -> Approved"); ctx.state = Approved()

class Approved(State):
    def next(self, ctx):
        print("Already approved")

class Document:
    def __init__(self): self.state = Draft()
    def next(self):     self.state.next(self)

d = Document()
d.next(); d.next(); d.next()
```

---

### 15. Template Method

**What:** Parent defines the skeleton; children fill in the steps.
**When:** Same workflow, different details (e.g., parse → validate → save).

```python
from abc import ABC, abstractmethod

class DataPipeline(ABC):
    def run(self):                  # template
        data = self.read()
        clean = self.transform(data)
        self.save(clean)

    @abstractmethod
    def read(self): ...
    @abstractmethod
    def transform(self, data): ...
    @abstractmethod
    def save(self, data): ...

class CsvPipeline(DataPipeline):
    def read(self):           return "raw,csv,rows"
    def transform(self, d):   return d.upper()
    def save(self, d):        print(f"Saved: {d}")

CsvPipeline().run()
```

---

### 16. Iterator

**What:** Walk a collection without exposing its structure.
**When:** Custom collections, lazy sequences.
**Python:** Built-in — just implement `__iter__` and `__next__`, or use a generator.

```python
class CountDown:
    def __init__(self, start): self.n = start
    def __iter__(self): return self
    def __next__(self):
        if self.n <= 0: raise StopIteration
        self.n -= 1
        return self.n + 1

for x in CountDown(3): print(x)   # 3 2 1
```

Generator version (preferred):

```python
def countdown(n):
    while n > 0:
        yield n
        n -= 1

list(countdown(3))   # [3, 2, 1]
```

---

### 17. Chain of Responsibility

**What:** Pass a request along a chain until someone handles it.
**When:** Middleware, logging filters, approval workflows, event bubbling.

```python
class Handler:
    def __init__(self): self.next = None
    def set_next(self, h):
        self.next = h
        return h
    def handle(self, req):
        if self.next: self.next.handle(req)

class AuthHandler(Handler):
    def handle(self, req):
        if "user" not in req: print("Reject: no user"); return
        print("Auth OK"); super().handle(req)

class LogHandler(Handler):
    def handle(self, req):
        print(f"Log: {req}"); super().handle(req)

class BusinessHandler(Handler):
    def handle(self, req):
        print("Process business logic")

chain = AuthHandler()
chain.set_next(LogHandler()).set_next(BusinessHandler())

chain.handle({"user": "aakash", "action": "buy"})
print("---")
chain.handle({"action": "buy"})
```

---

## Quick Picker — "Which pattern fits?"

| You want to... | Use |
|---|---|
| Create only one instance | Singleton |
| Hide which concrete class is built | Factory / Abstract Factory |
| Build complex object step-by-step | Builder |
| Clone an existing object | Prototype |
| Make two incompatible APIs work together | Adapter |
| Add behavior without subclassing | Decorator |
| Hide a complex subsystem | Facade |
| Model a tree of part + whole | Composite |
| Control access / lazy-load / cache | Proxy |
| Swap algorithms at runtime | Strategy |
| Notify many listeners of a change | Observer |
| Queue or undo actions | Command |
| Behavior depends on state | State |
| Fix the skeleton, vary the steps | Template Method |
| Iterate a custom collection | Iterator / generator |
| Pass a request through filters | Chain of Responsibility |

---

## SOLID Cheat Sheet (the "why" behind the patterns)

- **S — Single Responsibility:** one class, one reason to change.
- **O — Open/Closed:** open for extension (add a new Strategy), closed for modification.
- **L — Liskov Substitution:** subclasses must be drop-in replacements.
- **I — Interface Segregation:** small, focused interfaces beat one fat one.
- **D — Dependency Inversion:** depend on abstractions (inject Strategy), not concretes.

---

## Pythonic Reminders

- **First-class functions** often replace Strategy/Command — just pass a function.
- **Modules are singletons** — `import config` is your singleton.
- **`@decorator` syntax** is the native Decorator pattern for functions.
- **Duck typing** removes the need for explicit interfaces; `abc.ABC` is optional and only helps document intent.
- **`dataclasses`** remove most Builder boilerplate.
- **Generators (`yield`)** are the natural Iterator.

Use patterns to communicate intent — not to add ceremony.
