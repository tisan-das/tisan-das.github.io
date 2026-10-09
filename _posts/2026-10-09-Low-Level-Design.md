---
layout: post
title: "Low-Level Design: Class Relationships and Design Patterns in Go and Python"
image: /images/lld/01-class-relationships/08-patterns-as-relationships.webp
date: 2026-10-09 09:00:00 +0530
read_time: "57 min read" # prose only; the quizzes and code inflate the computed estimate
categories: ["Programming", "Low-Level Design"]
tags: [low-level-design, design-patterns, uml, class-diagrams, object-oriented-design, go, python, interviews]
published: true
---

Low-level design rests on two skills: telling how two classes are related, and recognizing design patterns, which are those same relationships arranged on purpose to solve a problem that keeps coming back. This post consists of six parts. [Part 1](#relationships) and [Part 2](#practice) cover relationships, with 100 practice questions. Parts 3 to 5 ([creational](#creational), [structural](#structural), [behavioral](#behavioral)) cover the patterns, each with a class diagram, Go code (Python where the idiom differs), the APIs you already use that follow it, and the traps. [Part 6](#field-guide) is a field guide for when you have a real problem and need the right pattern.

Each part ends with a quiz. Answers are saved in this browser, so you can revisit after few days and re-run them cold. The Go samples need Go 1.21 or later (1.23 for `iter` and `unique`); the Python samples need 3.10 or later.

> **Disclaimer.** This post is drafted with assistance from large language models (Claude Opus 5.5 and DeepSeek V4.1 Flash) based on conversations exploring low-level design and design patterns. All content has been reviewed, edited, and verified by a human author.
{: .prompt-info }

## Part 1: Association, aggregation or composition?
{: #relationships}

Most low-level design problems, from parking lots to movie booking, keep asking one question: **how are these two classes related?** Association, aggregation and composition look identical in code. What separates them is ownership and lifetime. Get that call right and the rest of the design follows: who constructs what, what a delete cascades to, who may close a connection, and what a lock actually protects.

### The two questions that separate them
{: #the-two-questions-that-separate-them}

In code, all three are a field in class `A` that refers to class `B`. Two questions about ownership and lifetime tell them apart:

- If I delete `A`, what happens to `B`?
- Can `B` belong to more than one `A` at the same time?

|  | Whole–part? | `B` survives deleting `A`? | `B` shareable? |
| --- | --- | --- | --- |
| **Association** | No, they're peers | Yes | Yes, often many-to-many |
| **Aggregation** | Yes | Yes | Yes, or it can move between wholes |
| **Composition** | Yes | No, it dies with `A` | No, exactly one owner |

Three examples from common interview problems:

- **Association.** A parking lot's `Vehicle` and `ParkingSpot`: the car existed before it parked and drives away after.
- **Aggregation.** Splitwise's `Group` and `User`: delete the trip group and your friends keep their accounts.
- **Composition.** Movie booking's `Screen` and `Seat`: seat A9 means nothing without its screen.

### The full spectrum and its notation
{: #the-full-spectrum-and-its-notation}

Those three sit in the middle of a wider range of relationships, ordered by how tightly the two classes are coupled:

![The relationship spectrum from weaker to stronger coupling: dependency (uses-a, dashed arrow), association (knows-a, plain line), aggregation (has-a, hollow diamond), composition (owns-a, filled diamond), and at the strong end inheritance (is-a, hollow triangle) with realization (implements, hollow triangle on a dashed line) at the same level](/images/lld/01-class-relationships/01-relationship-spectrum.webp)
_The middle three are the ones most designs argue about. Realization, implementing an interface, sits level with inheritance: the same hollow triangle, on a dashed line._

How to read the notation:

- **The diamond always sits on the whole's end.** Hollow ◇ is aggregation, filled ◆ is composition. In plain text you'll see them typed as `A <>-- B` and `A <#>-- B`.
- **A plain solid line is an association.** Multiplicities such as `1` and `0..*` go on its ends.
- **A dashed open arrow is a dependency.** `A` uses `B` somewhere in its code but doesn't keep it.
- **A hollow triangle points at a parent type.** A solid line means inheritance from a class; a dashed line means realization of an interface.
- **An association class** hangs off the middle of an association line by a dashed line.

### Spotting them in code and schemas
{: #spotting-them-in-code-and-schemas}

In code, the tell is who calls `B`'s constructor, and whether `B` is handed in or created inside.

```python
# Association: peers created independently, linked by reference
class Teacher:
    def __init__(self, name: str):
        self.name = name
        self.students: list["Student"] = []

    def enroll(self, s: "Student"):
        self.students.append(s)
        s.teachers.append(self)          # often bidirectional

# Aggregation: the whole holds parts that were created elsewhere
class Library:
    def __init__(self):
        self.books: list[Book] = []

    def add(self, book: Book):           # passed in: the caller created it
        self.books.append(book)

# Composition: the whole creates its parts and never hands out ownership
class House:
    def __init__(self, room_specs):
        self._rooms = [Room(s) for s in room_specs]   # created inside
```
{: file="Python · the same field, three relationships"}

In a garbage-collected language nothing is destroyed when `A` goes away; `B` is freed only once nothing points to it. So composition is a design rule the runtime won't enforce: `A` alone creates and manages `B`, and no other object keeps a reference to `B` after `A` is gone. Other code may borrow `B` during a call, but it shouldn't store it.

The database view makes the difference concrete, and interviewers do probe it:

| Relationship | Schema shape | On delete of `A` |
| --- | --- | --- |
| **Association** | Join table, such as `teacher_student` | Delete only the join rows |
| **Aggregation** | Nullable foreign key on `B`, such as `book.library_id` | `ON DELETE SET NULL` |
| **Composition** | `NOT NULL` foreign key on `B`, such as `room.house_id` | `ON DELETE CASCADE` |
| **[Association class](#when-the-link-has-data)** | Join table with its own columns, such as `enrollment(student_id, course_id, grade)` | Delete the link rows, and their data goes with them; or `RESTRICT` the delete if that data must be kept |

> **In Go.** Composition is a struct that creates and holds its parts, often as value fields or unexported pointers. Aggregation is a struct holding pointers injected through its constructor. Struct embedding isn't inheritance: it's composition with method promotion. And the advice "favor composition over inheritance" uses the word loosely, meaning "hold an object instead of subclassing", which covers aggregation and association too.
{: .prompt-tip }

Association versus aggregation is the blurriest line. UML leaves aggregation's meaning loose, and Martin Fowler's *UML Distilled* recommends essentially ignoring it. The distinction that matters most is composition versus everything else, because it decides cascading deletes, who constructs what, and whether a part can be shared.

### Dependency or association?
{: #dependency-or-association}

These two get confused more than any other pair. One question settles it: **does `A` still hold a reference to `B` after the method returns?**

- **Yes:** association. `B` is part of `A`'s state, stored in a field.
- **No:** dependency. `A` touches `B` only while one method runs, through a parameter, a local variable, a return value or a static call.

Put another way, **an association is a link between objects, and a dependency is a link between pieces of code.** In `lot.park(car)`, the lot reaches the car only through the parameter, then builds a `Ticket` that stores it in a field. So `ParkingLot → Vehicle` is a dependency and `Ticket → Vehicle` is an association: the same `Vehicle` in two relationships, decided by who keeps the reference.

> **The snapshot test.** Freeze the program at a moment when no method is running and look at the object graph. Every arrow you can still see is an association. Dependencies never show up in a snapshot, because they exist only while code is running.
{: .prompt-tip }

```python
# Dependency: A uses B, then forgets it
class ParkingLot:
    def park(self, vehicle: Vehicle) -> Ticket:     # parameter
        spot = self._find_spot(vehicle.size)
        return Ticket(spot, vehicle)                # creates and returns, keeps nothing

# Association: A keeps B
class Ticket:
    def __init__(self, spot: ParkingSpot, vehicle: Vehicle):
        self.spot = spot                            # stored
        self.vehicle = vehicle                      # stored
```
{: file="Python · dependency versus association"}

On a class diagram, fields draw solid lines and method signatures draw dashed ones.

![Class diagram of Order: its fields customer and items draw solid lines, an association to Customer and a composition with LineItem; its methods total(tax: TaxCalculator), notify(mailer: Mailer) and invoice() returning Invoice draw dashed dependency arrows](/images/lld/01-class-relationships/04-fields-vs-methods.webp)
_Trace each line back to the member it comes from. Fields, which `Order` keeps, draw solid lines; types that only appear in a method signature draw dashed arrows._

|  | Dependency | Association |
| --- | --- | --- |
| **Lives in** | Parameters, locals, return types, static calls | Fields (instance state) |
| **Link lasts** | One method call | As long as `A` holds the field |
| **UML** | Dashed arrow | Solid line |
| **Database** | Nothing in the schema | Foreign key or join table |
| **Coupling** | Weaker; prefer it when you can | Stronger |

#### The gray areas
{: #the-gray-areas}

- **Injected services.** `OrderService.__init__(self, repo)` that stores `self.repo` is an association by the strict test. Many teams still draw injected collaborators as dashed dependencies to keep only domain relationships solid. Either is defensible if you state your convention; this post uses the strict test.
- **Storing an ID.** `Order.customer_id` is still an association at the domain level. The ID is just how the link is stored.
- **Create and return.** A factory that builds a `Car` and returns it depends on `Car` (UML even has a `«create»` dependency) but keeps nothing.
- **The same pair can be either.** `Report.print(printer)` is a dependency; a `Report` holding `self.printer` is an association. The code decides, not the class names.

Two design signals come out of this. If you pass the same object into most of a class's methods, it's probably state: make it a field. If a field is used by only one method, it probably isn't state: make it a parameter. Less state means fewer lifecycle and concurrency problems, so default to dependency and promote to association only when `A` genuinely needs to remember `B`.

### When the link has data
{: #when-the-link-has-data}

Sometimes the relationship itself carries data. A grade belongs neither to the student nor to the course, but to the pairing. The quantity of a product belongs neither to the cart nor to the product. When the link has attributes, promote it to a class of its own, an **association class**: `Enrollment`, `CartItem`, `Membership`.

- **Parking lot:** the spot–vehicle link carries an entry time and a fee, so it becomes `Ticket`.
- **Movie booking:** `Screen ◆ Seat` is composition, but "seat A9 for the 7 pm show" is a different thing: `ShowSeat`, the association class between `Show` and `Seat` that holds booking status and price. It's also what gets locked when two people try to book the same seat.

In a database, an association class is a join table with its own columns. One subtlety: strictly, a UML association class allows one link per pair. If the same pair can repeat, such as the same song twice in one playlist, model the link as a full class, or mark the association ends `{nonunique}`.

### The decision tree
{: #the-decision-tree}

Everything above folds into five questions, asked in order. Stop at the first one that gives an answer. The order is for classification, not preference: inheritance comes first because it's the easiest to rule in or out.

![The decision tree: 1. kind of or implements? (extends gives inheritance, implements gives realization); 2. is the link stored? (no gives dependency); 3. does the link carry data? (yes gives association class); 4. is it whole–part? (no gives association); 5. can the part outlive the whole or be shared? (yes gives aggregation, no gives composition)](/images/lld/01-class-relationships/05-decision-tree.webp)
_Highlighted outcomes are the stored-link family; the rest are type relationships or transient use._

#### What to look for at each step
{: #what-to-look-for-at-each-step}

| Step | Signals in code and schemas |
| --- | --- |
| **1. Kind of, or implements?** | `extends` or a subclass, including an abstract class with concrete methods → inheritance. `implements`, a Python `Protocol`, a Go method set, or Rust `impl Trait for` → realization. |
| **2. Stored?** | A field of any kind, including injected services, IDs, weak references and borrowed references → stored. A parameter, local, return type, thrown exception, static or module-level call, or something created and returned → dependency. |
| **3. Link has data?** | Data that belongs to neither side alone. A join table with extra columns. |
| **4. Whole–part?** | Is `A` made of `B`? Possessive English isn't enough: a doctor "has" patients but isn't made of them. |
| **5. Outlive or shared?** | Composition: created inside, private, a value field, `unique_ptr`, `Box`, `NOT NULL` plus `CASCADE`. Aggregation: passed in, the same instance in several wholes, `shared_ptr`, a nullable foreign key with `SET NULL`. |

The conventions used throughout this post, so that every question has one defensible answer:

- Injected services stored in a field count as associations (the strict test).
- **Storing an ID instead of an object is still an association.**
- Value fields, `unique_ptr` and `Box` are composition; Go struct embedding by value is composition, not inheritance.
- Composition fixes when parts *must* die, not when they *may*: deleting the whole deletes its remaining parts, but the whole can delete a part earlier, such as removing one line item from an order. That's still composition; UML allows it.
- Domain rules beat class names. `Car → Engine` is composition at a carmaker and aggregation at an engine-refurbishing shop.

### What the decision buys you
{: #what-the-decision-buys-you}

Classifying relationships is the vocabulary. What you use it for is the decision every design comes down to: who creates each object, who is allowed to destroy it, and who else can reach it. Once you've chosen the relationship, a set of code decisions follows:

| `A → B` is… | Who creates `B` | Who cleans `B` up | Database | Locking |
| --- | --- | --- | --- | --- |
| **Dependency** | The caller, per call | The caller | Nothing | Nothing held, nothing to guard |
| **Association** | Someone else; injected | `B`'s real owner, never `A` | Foreign key on the "many" side (often `A`, such as `ticket.vehicle_id`) or a join table; no cascade | `B` is shared, so it must be safe on its own |
| **Aggregation** | Outside, then added to `A` | Outside; `B` can outlive `A` | Nullable foreign key on `B` pointing to `A`, `SET NULL` | `A`'s lock doesn't cover `B`: other wholes can reach it |
| **Composition** | `A`, in its constructor | `A`, when it closes or is deleted | `NOT NULL` foreign key on `B` pointing to `A`, `CASCADE` | `A`'s lock can guard `B`; nobody else holds it |
| **Association class** | Whoever creates the link | Removed with the link | Join table with foreign keys to both sides, plus its own columns | Often the row you lock, such as `ShowSeat` |

Two rules from that table come up constantly:

- **Only close what you composed.** If a struct receives a `*sql.DB` or a `*grpc.ClientConn` through its constructor, that's an association, and it must never call `Close()` on it. The owner does.
- **A lock on the whole protects only its composed parts.** If a part can be shared, another whole can reach it without taking your lock, so the part needs its own protection.

### Where it fits in a design
{: #where-it-fits-in-a-design}

Relationships are step 3 of a repeatable low-level design process:

1. **Clarify requirements.** Four to six use cases as verbs ("park vehicle", "exit and pay"). Ask only questions that change the design.
2. **Identify entities.** The nouns in those use cases, minus attributes posing as classes: a vehicle's color is a field.
3. **Map relationships.** Run the decision tree on each pair, and promote links that carry data to association classes.
4. **Assign behavior.** Give each verb to the class that already has the data it needs.
5. **Model state.** Anything with a lifecycle gets an enum and its legal transitions, such as `ShowSeat: AVAILABLE → LOCKED → BOOKED`.
6. **Apply patterns where things vary.** Pricing rules suggest Strategy; spot or vehicle types suggest Factory.
7. **Handle concurrency.** Two cars, one spot: pick a per-entity lock, an optimistic version check or a unique constraint, and make payment idempotent.
8. **Code and walk through.** Interfaces, core classes and one end-to-end method such as `park()`, then trace a use case through them.

#### Step 3 for a parking lot
{: #step-3-for-a-parking-lot}

![Parking lot class diagram: ParkingLot composes Floor, which composes ParkingSpot; Ticket links ParkingSpot and Vehicle; Car and Truck inherit from Vehicle; ParkingLot is associated with PricingStrategy, which Hourly and Flat rate implement](/images/lld/01-class-relationships/07-parking-lot-relationships.webp)
_Most of the relationship types in one picture. `Ticket`, in orange, is the association class: the spot–vehicle link promoted to a class of its own because it carries data._

- `ParkingLot ◆ Floor ◆ ParkingSpot` is composition all the way down. The lot builds floors and spots from configuration, and spot "F2-17" means nothing without them.
- `Ticket` is the spot–vehicle link promoted to an association class: it carries an entry time and a fee, and the car exists before and after it parks.
- `ParkingLot — PricingStrategy` is a plain association: injected and swappable, but a lot isn't made of its pricing rules. It's also the Strategy pattern.
- `Car` and `Truck` inherit from `Vehicle`. If they differ only in size, a `VehicleType` enum is simpler; subclass only when behavior differs.

The usual traps: labelling everything composition because "the lot has spots", spending twenty minutes on aggregation versus association, and running out of time before state and concurrency, which is where strong answers stand out.

### A real-world call: who owns the instance?
{: #a-real-world-call-who-owns-the-instance}

Relationship thinking settles real infrastructure questions too. Say a service keeps a pool of pre-warmed virtual machines in an AWS Auto Scaling group, hands one out per customer request, applies the customer's configuration, and terminates the machine when the customer is done. Should the instance be detached from the group once it's assigned?

The question is really which object should compose the instance once it's assigned:

- **If you don't detach, the group still owns it.** A scale-in event or a failed health check can terminate a customer's live machine. Instance scale-in protection stops the first, but not health-check replacement.
- **If you detach, ownership moves to the site.** That's still composition, because a part can leave its whole before the whole is deleted. The duties move with ownership: the service must now terminate the instance when the site is discarded, and replace it if it fails.
- **Detaching can also refill the pool.** Detach without decrementing the group's desired capacity and the group launches a replacement.

### Check your understanding
{: #check-your-understanding}

{% include quiz.html id="lld-relationships-checkpoint" %}

## Part 2: 100 questions on class relationships
{: #practice}

Running the [decision tree](#the-decision-tree) quickly on code you've never seen takes practice. These 100 questions cover code in Python, Go, Java, TypeScript, C++ and Rust, SQL schemas, UML and real systems. Pairs that differ by one fact recur, so you practice the deciding detail rather than the class names. Answers follow the conventions from Part 1; where a second answer is defensible, it's marked as also accepted. *Walk the tree* mode asks the five questions one at a time and shows which step went wrong.

{% include quiz.html id="lld-relationships-bank" %}

### How to tell them apart
{: #how-to-tell-them-apart}

- **Dependency or association?** Ignore the class names and look for a field. If `A` stores `B`, it's an association; if `B` appears only in a parameter, local or return type, it's a dependency.
- **Composition or aggregation?** "Has" doesn't mean "owns". It's composition only if `B` dies with `A` and no other object shares it. If `B` is passed in, shared or survives `A`, it's aggregation.
- **Association class?** Look for data that belongs to the pairing rather than either side, such as a quantity, status, date or role. That data needs a class of its own, such as `Enrollment` or `CartItem`.
- **Inheritance or realization?** Check what the parent is. Extending a class is inheritance; implementing an interface, protocol or trait is realization.
- **Two questions that look alike?** Find the one fact that differs between them; that fact decides the answer.

### Patterns are arrangements of these relationships
{: #patterns-are-arrangements-of-these-relationships}

Most design patterns are fixed arrangements of the relationships from [Part 1](#relationships), which makes them much easier to learn once the relationships are second nature:

![Four patterns as relationship shapes: Strategy (Checkout holds a Pricing interface that Hourly implements), Observer (Ticker holds many Observers that EmailAlert implements), Composite (File and Folder are Nodes, and a Folder owns many Nodes), Decorator (LoggingStore is a Store and wraps a Store)](/images/lld/01-class-relationships/08-patterns-as-relationships.webp)
_Green boxes are interfaces or abstract types. Composite and Decorator share one trick: a class that both is a type and holds that same type._

Strategy and Observer have the same shape; the differences are one holder versus many, and the intent. Seen this way, you can recognize a pattern in unfamiliar code just from how its types connect. Parts 3 to 5 draw every pattern this way.

## Part 3: Creational patterns
{: #creational}

**Who gets to call `new`?** Creating an object hides three decisions: how many to make, which concrete type, and how to put it together. Each creational pattern takes over one of them.

| Pattern | Decides | In one line |
| --- | --- | --- |
| [Singleton](#singleton) | How many? | Exactly one, shared by everyone. |
| [Factory](#factory) | Which type? | Decided in one place, returned as an interface. |
| [Builder](#builder) | How assembled? | Step by step, checked once at the end. |

### Reading the diagrams
{: #reading-the-diagrams}

Each pattern gets a class diagram. The arrows are the relationships from [Part 1](#relationships), and this notation holds for the rest of the post.

![UML notation used in this post: class box compartments and seven arrow types](/images/lld/03-creational-patterns/01-uml-notation.webp)
*Go has no classes, so read a class box as a struct or an interface. Exported (capitalized) names are `+`, unexported names are `-`.*

### Singleton
{: #singleton}

**How many?** Make exactly one instance, and give the whole program one way to reach it.

- **Reach for it when:** A second copy would waste or corrupt something: a connection pool, a metrics registry, a cache, a loaded config.
- **Go idiom:** `sync.Once`, or `sync.OnceValue` in Go 1.21+
- **Python idiom:** A module-level object. Modules are already singletons.

#### Class diagram
{: #class-diagram}

In UML, a singleton is a class that keeps a reference to its only instance and exposes a static accessor. Go has no static members, so the "static" parts are package-level variables.

![Class diagram: Config singleton with package-level instance and once fields, a static Get method, and two clients that call Get](/images/lld/03-creational-patterns/03-singleton-class-diagram.webp)
*`Config` keeps a reference to its only instance (the arrow that loops back to itself, multiplicity 1). Callers never construct a `Config`; they call `Get()`, which is underlined because it belongs to the package, not to an instance.*

#### The race it has to survive
{: #the-race-it-has-to-survive}

The obvious version checks for `nil` and then creates. Two goroutines can both pass the check before either one assigns, and now you have two objects. This is the most common singleton bug.

![Timeline comparison: the naive check-then-create lets two goroutines each create a Config; sync.Once makes the second goroutine wait and reuse the first one](/images/lld/03-creational-patterns/04-singleton-timeline.webp)
*`go test -race` flags the naive version. `sync.Once` makes the second caller wait for the first, then skip the work entirely.*

#### Code
{: #code}

```go
package config

import (
    "os"
    "sync"
)

type Config struct {
    DSN      string
    MaxConns int
}

var (
    instance *Config   // the one and only
    once     sync.Once // guards the first creation
)

// Get returns the shared Config. Safe to call from any goroutine.
func Get() *Config {
    once.Do(func() {
        instance = &Config{
            DSN:      os.Getenv("DB_DSN"),
            MaxConns: 20,
        }
    })
    return instance
}
```
{: file="config/config.go"}

```python
# config.py
# The Pythonic singleton is a module-level object. Python runs a module
# once and caches it in sys.modules, so every import gets the same object.
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    dsn: str
    max_conns: int = 20

settings = Config(dsn=os.environ.get("DB_DSN", ""))

# anywhere else: `from config import settings` gets this same object
```
{: file="Python · config.py: the Pythonic way"}

**Where you'll find it:** `http.DefaultClient` and `slog.Default()` (shared package-level defaults), `prometheus.MustRegister` (one global registry, which panics on a duplicate metric), and `logging.getLogger("app")` (one logger per name, process-wide).

#### Traps
{: #traps}

**Hidden dependencies.** A function that calls `config.Get()` inside hides that dependency from its signature, and a test can't swap it. Create the instance once in `main` and pass it down: still exactly one, with no global lookup.

**One per process, not one per system.** Three replicas, four gunicorn workers or a `multiprocessing` pool each get their own copy. Shared state belongs in a database or Redis, and one actor across replicas needs leader election (client-go's `leaderelection` with a Lease).

**A failed first initialization is cached.** `sync.Once` never retries. Use `sync.OnceValues` so every caller at least gets the error, or load in `main` and exit on failure.

**The GIL doesn't make check-then-create safe.** A thread can be switched out between the `is None` check and the assignment. A class-based singleton needs a lock and a second check inside it; the module-level object needs neither.

### Factory
{: #factory}

**Which type?** Put the decision about which concrete type to create in one place, and hand back an interface.

- **Reach for it when:** The concrete type depends on config or input (storage backend, cloud, payment provider), or the same `switch` on type shows up in several places.
- **Go idiom:** `func NewStore(kind string) (Store, error)`, returning an interface
- **Python idiom:** A dict of classes, filled by a `@register` decorator

#### Class diagram
{: #creational-class-diagram}

![Class diagram: Uploader holds a Store interface and calls NewStore, which creates S3Store, GCSStore or LocalStore, all of which implement Store](/images/lld/03-creational-patterns/07-factory-class-diagram.webp)
*`Uploader` depends only on the `Store` interface. `NewStore` is the one place that knows the three concrete types exist: it creates them (`«create»`) and returns them as `Store`.*

#### Code
{: #creational-code}

```go
package storage

import (
    "context"
    "fmt"
)

// Store is all the caller depends on.
type Store interface {
    Put(ctx context.Context, key string, data []byte) error
    Get(ctx context.Context, key string) ([]byte, error)
}

type S3Store struct{ bucket string }
type GCSStore struct{ bucket string }
type LocalStore struct{ root string }

// (each type implements Put and Get; omitted here)

// NewStore is the factory. The caller names what it wants;
// this function decides which concrete type that means.
func NewStore(kind, target string) (Store, error) {
    switch kind {
    case "s3":
        return &S3Store{bucket: target}, nil
    case "gcs":
        return &GCSStore{bucket: target}, nil
    case "local":
        return &LocalStore{root: target}, nil
    default:
        return nil, fmt.Errorf("unknown store kind %q", kind)
    }
}
```
{: file="storage/storage.go"}

```go
// kind comes from config, so switching backends is a config change.
store, err := storage.NewStore(cfg.Storage.Kind, cfg.Storage.Target)
if err != nil {
    log.Fatalf("storage: %v", err) // fail at startup, not on the first upload
}
uploader := NewUploader(store) // Uploader only knows the Store interface
```
{: file="Go · Using it"}

```python
from typing import Callable, Protocol

class Store(Protocol):
    def put(self, key: str, data: bytes) -> None: ...
    def get(self, key: str) -> bytes: ...

_REGISTRY: dict[str, Callable[[str], Store]] = {}

def register(kind: str):
    """Class decorator: adds the class to the factory under `kind`."""
    def wrap(cls):
        _REGISTRY[kind] = cls
        return cls
    return wrap

@register("s3")
class S3Store:
    def __init__(self, bucket: str):
        self.bucket = bucket
    def put(self, key, data): ...
    def get(self, key): ...

def new_store(kind: str, target: str) -> Store:
    try:
        return _REGISTRY[kind](target)
    except KeyError:
        raise ValueError(f"unknown store kind {kind!r}") from None

store = new_store("s3", "logs-bucket")   # an S3Store, typed as Store
```
{: file="Python · storage.py: a registry filled by a decorator"}

A Go detail worth remembering: the usual advice is "accept interfaces, return structs", so a plain constructor like `NewS3Store()` returns `*S3Store`. A factory is the exception. Its whole job is that the caller doesn't know which struct it gets, so it has to return the interface.

#### Making it open: the registry factory
{: #making-it-open-the-registry-factory}

A `switch` has to be edited for every new backend. In the registry version each backend adds itself, so the factory never changes. `database/sql` works exactly this way.

```go
package storage

import (
    "fmt"
    "sync"
)

type Constructor func(target string) (Store, error)

var (
    mu        sync.RWMutex
    factories = map[string]Constructor{}
)

// Register is called from each backend's init().
func Register(kind string, c Constructor) {
    mu.Lock()
    defer mu.Unlock()
    if _, dup := factories[kind]; dup {
        panic("storage: Register called twice for " + kind)
    }
    factories[kind] = c
}

func NewStore(kind, target string) (Store, error) {
    mu.RLock()
    c, ok := factories[kind]
    mu.RUnlock()
    if !ok {
        return nil, fmt.Errorf("unknown store kind %q (missing import?)", kind)
    }
    return c(target)
}
```
{: file="storage/registry.go"}

```go
package s3store

import "example.com/app/storage"

type S3Store struct{ bucket string }

// (S3Store implements Put and Get; omitted here)

// Adds itself to the factory when the package is imported.
func init() {
    storage.Register("s3", func(bucket string) (storage.Store, error) {
        return &S3Store{bucket: bucket}, nil
    })
}

// main.go
import _ "example.com/app/storage/s3store" // imported only to run its init()
```
{: file="Go · Each backend registers itself"}

That's why `import _ "github.com/lib/pq"` exists: the blank import runs pq's `init()`, which registers the "postgres" driver before `main` starts. `sql.Open` only looks the name up, and no connection opens until the first query. In Python, importing the module that carries the `@register` decorator does the same.

#### Three things called "factory"
{: #three-things-called-factory}

People say "factory" for three different things. All three answer "which type?", but they put the decision in different places.

|  | Simple factory | Factory Method | Abstract Factory |
| --- | --- | --- | --- |
| What it is | A function with a switch | A method that subclasses override | An object that makes a whole family |
| Decides | One type per call | One type per subclass | A matching set of types |
| Go shape | `NewStore(kind)` | A `func` field you inject | An interface with several `New…` methods |

#### Factory Method
{: #factory-method}

In a Factory Method, a base type writes the whole algorithm once and leaves one step, "create the thing I'll work with", to subclasses. Below, `Exporter` owns the batching; each subclass only decides which sink the batches go to.

![Class diagram: abstract Exporter defines export and an abstract create_sink; S3Exporter and CloudWatchExporter override create_sink to create S3Sink or CloudWatchSink](/images/lld/03-creational-patterns/09-factory-method-class-diagram.webp)
*Solid line with a hollow triangle means inherits. `Exporter.export()` calls `create_sink()`, which is abstract (italic). Each subclass overrides only that one method, and each creates its own sink.*

```go
// Go has no inheritance, so the "factory method" becomes a function
// field you inject instead of a method you override.
type Sink interface {
    Write(batch []Record) error
}

type Exporter struct {
    newSink func() Sink
}

func (e Exporter) Export(records []Record) error {
    sink := e.newSink() // the factory method
    for i := 0; i < len(records); i += 100 {
        if err := sink.Write(records[i:min(i+100, len(records))]); err != nil {
            return err
        }
    }
    return nil
}

s3 := Exporter{newSink: func() Sink { return &S3Sink{bucket: "logs"} }}
cw := Exporter{newSink: func() Sink { return &CloudWatchSink{group: "/app"} }}
```
{: file="Go · Inject the factory method"}

```python
from abc import ABC, abstractmethod

class Exporter(ABC):
    def export(self, records: list[dict]) -> None:
        sink = self.create_sink()            # the factory method
        for i in range(0, len(records), 100):
            sink.write(records[i:i + 100])   # batching is written once, here

    @abstractmethod
    def create_sink(self) -> "Sink": ...

class S3Exporter(Exporter):
    def create_sink(self) -> "Sink":
        return S3Sink()                      # CloudWatchExporter returns a CloudWatchSink

S3Exporter().export([{"msg": "hi"}] * 250)   # 3 batches to S3
```
{: file="Python · Override the factory method"}

#### Abstract Factory
{: #abstract-factory}

When products come in families that must match, one factory object makes the whole family. A provisioner that works on both clouds is the classic case: a site on AWS needs an EC2 instance, an S3 bucket and an SQS queue, and none of them may come from Azure.

![Abstract factory as a grid: AWSFactory and AzureFactory each implement CloudFactory and create one row of products; each column implements the VM, Bucket or Queue interface](/images/lld/03-creational-patterns/10-abstract-factory-class-diagram.webp)
*Each row is one concrete factory; each column is one product interface. Choosing a factory chooses a whole row, so an EC2 VM writing to an Azure blob container can't happen.*

```go
// One interface per product...
type VM interface{ Start(ctx context.Context) error }
type Bucket interface{ Put(ctx context.Context, key string, b []byte) error }
type Queue interface{ Send(ctx context.Context, msg []byte) error }

// ...and one factory interface that makes a matching family of them.
type CloudFactory interface {
    NewVM(size string) VM
    NewBucket(name string) Bucket
    NewQueue(name string) Queue
}

type AWSFactory struct{ Region string }

func (f AWSFactory) NewVM(size string) VM         { return &EC2Instance{region: f.Region, size: size} }
func (f AWSFactory) NewBucket(name string) Bucket { return &S3Bucket{region: f.Region, name: name} }
func (f AWSFactory) NewQueue(name string) Queue   { return &SQSQueue{region: f.Region, name: name} }

// AzureFactory mirrors it with AzureVM, BlobContainer and ServiceBusQueue.

// provisionSite never names a cloud, and everything it makes matches.
func provisionSite(ctx context.Context, f CloudFactory) error {
    vm := f.NewVM("large")
    logs := f.NewBucket("site-logs")
    jobs := f.NewQueue("site-jobs")
    if err := logs.Put(ctx, "provisioned", nil); err != nil {
        return err
    }
    if err := jobs.Send(ctx, []byte("boot")); err != nil {
        return err
    }
    return vm.Start(ctx)
}
```
{: file="cloud/factory.go"}

The factory itself is picked once at startup, usually by a simple factory that switches on `"aws"` or `"azure"`. Adding a family, a third cloud, is cheap: one new factory. Adding a product, say `NewDatabase`, is the expensive direction: the interface and every concrete factory change.

**Where you'll find it:** `sql.Open("pgx", dsn)` and `image.Decode` (registries filled by `init()`), `boto3.client("s3")`, and SQLAlchemy's `create_engine(url)`, which picks the dialect from the URL scheme.

#### Traps
{: #creational-traps}

**A factory for one type.** That's indirection with no decision in it. Add the factory when the second type shows up.

**Unknown kinds found late.** Build the store in `main` and exit on error, so a typo in config fails the deploy instead of the first request.

**A switch that keeps growing.** Move to a registry so new types add themselves, and the factory stops changing.

**Leaking the concrete type.** If callers write `store.(*S3Store)`, the interface isn't doing its job. Add the method they need to `Store`, or rethink the split.

### Builder
{: #builder}

**How assembled?** Assemble a complex object one named step at a time, and validate it once at the end.

- **Reach for it when:** A constructor needs many parameters, most of them optional, or some combinations are invalid.
- **Go idiom:** A fluent builder for multi-step objects; functional options for constructors with defaults
- **Python idiom:** Keyword arguments cover most cases; builders shine for step-by-step assembly like query builders

#### The problem it removes
{: #the-problem-it-removes}

**Before: telescoping constructor**

```go
p := NewPod("api", "nginx:1.27", 8080,
    nil, 3, true, "", 0)
```

What is `true`? What does `""` turn off? Swap the `3` and the `0` and it still compiles.

**After: builder**

```go
p, err := pod.New("api").
    Image("nginx:1.27").
    Port(8080).
    Replicas(3).
    Build()
```

Every value has a name. Anything you skip keeps its default. `Build()` refuses a Pod with no image.

#### Class diagram
{: #creational-class-diagram-2}

![Class diagram: main calls New, then chains calls on PodBuilder, which holds a draft Pod and a list of errors; each setter returns the builder, and Build validates and creates the Pod](/images/lld/03-creational-patterns/11-builder-class-diagram.webp)
*`PodBuilder` collects settings and errors, and creates the `Pod` only in `Build()`. The textbook version adds a `Director` that runs a fixed recipe over a builder interface; in Go the calling code usually plays that role.*

#### What Build() reports
{: #what-build-reports}

What the builder below prints. `Build()` reports every problem at once with `errors.Join`, and returns a copy, so later builder calls don't reach a Pod already built.

```go
p, err := pod.New("api").Image("nginx:1.27").Port(8080).Build()
// p:   {Name:api Image:nginx:1.27 Ports:[8080] Env:map[] Replicas:1}
// err: <nil>

_, err = pod.New("api").Port(8080).Build()
// err: image is required

_, err = pod.New("api").Port(70000).Build()
// err: port 70000 out of range
//      image is required

b := pod.New("api").Image("nginx:1.27")
first, _ := b.Build()
b.Env("LOG_LEVEL", "debug").Port(9090)
second, _ := b.Build()
// first:  {Name:api Image:nginx:1.27 Ports:[] Env:map[] Replicas:1}
// second: {Name:api Image:nginx:1.27 Ports:[9090] Env:map[LOG_LEVEL:debug] Replicas:1}
```

#### Code
{: #creational-code-2}

```go
package pod

import (
    "errors"
    "fmt"
    "maps"
    "slices"
)

type Pod struct {
    Name     string
    Image    string
    Ports    []int
    Env      map[string]string
    Replicas int
}

type PodBuilder struct {
    pod  Pod
    errs []error
}

func New(name string) *PodBuilder {
    return &PodBuilder{pod: Pod{Name: name, Replicas: 1, Env: map[string]string{}}}
}

func (b *PodBuilder) Image(ref string) *PodBuilder {
    b.pod.Image = ref
    return b // returning b is what lets calls chain
}

func (b *PodBuilder) Port(n int) *PodBuilder {
    if n < 1 || n > 65535 {
        b.errs = append(b.errs, fmt.Errorf("port %d out of range", n))
    }
    b.pod.Ports = append(b.pod.Ports, n)
    return b
}

func (b *PodBuilder) Env(key, value string) *PodBuilder {
    b.pod.Env[key] = value
    return b
}

func (b *PodBuilder) Replicas(n int) *PodBuilder {
    b.pod.Replicas = n
    return b
}

// Build checks everything once and hands back an independent copy.
func (b *PodBuilder) Build() (Pod, error) {
    errs := slices.Clone(b.errs)
    if b.pod.Image == "" {
        errs = append(errs, errors.New("image is required"))
    }
    if err := errors.Join(errs...); err != nil {
        return Pod{}, err
    }
    p := b.pod
    p.Ports = slices.Clone(b.pod.Ports)
    p.Env = maps.Clone(b.pod.Env)
    return p, nil
}
```
{: file="pod/pod.go"}

##### The Go idiom: functional options
{: #the-go-idiom-functional-options}

For constructors that mostly need sensible defaults plus a few overrides, Go code usually reaches for functional options instead of a builder object. Each option is a small function that edits the struct being created.

```go
type Server struct {
    addr    string
    timeout time.Duration
    tls     *tls.Config
}

type Option func(*Server)

func WithTimeout(d time.Duration) Option { return func(s *Server) { s.timeout = d } }
func WithTLS(c *tls.Config) Option       { return func(s *Server) { s.tls = c } }

func NewServer(addr string, opts ...Option) *Server {
    s := &Server{addr: addr, timeout: 30 * time.Second} // defaults first
    for _, opt := range opts {
        opt(s) // then each option edits the struct
    }
    return s
}

srv := NewServer(":8443", WithTimeout(5*time.Second), WithTLS(tlsCfg))
```
{: file="Go · server.go: functional options"}

Pick functional options when the object is ready in one call and each option stands alone. Pick a fluent builder when assembly happens in steps, options depend on each other, or you want to collect several errors and report them together.

**Where you'll find it:** client-go apply configurations (`corev1ac.Pod(…).WithSpec(…)`), `strings.Builder`, SQLAlchemy's `select(…).where(…)`, and functional options in `grpc.NewClient` and the AWS SDK for Go v2.

#### Traps
{: #creational-traps-2}

**A builder for a small object.** Two required fields? A struct literal or a plain constructor is clearer. In Python, a dataclass with defaults and keyword arguments covers most cases.

**A Build() that checks nothing.** Then the builder is setters with extra steps. The promise is "if you got a Pod back, it's valid".

**Shared slices and maps.** Copy them in `Build()` with `slices.Clone` and `maps.Clone`. Otherwise reusing the builder quietly edits the Pod you already returned.

**Sharing a builder between goroutines.** Builders are mutable and unsynchronized. Make one per construction.

### They combine
{: #they-combine}

Real libraries stack them. Spark's session setup is a builder that ends in a singleton:

```python
spark = (SparkSession.builder              # Builder: collect settings
         .appName("etl")
         .config("spark.sql.shuffle.partitions", "64")
         .getOrCreate())                   # Singleton: reuse the active session if there is one
```
{: file="Python · PySpark"}

Likewise, `sql.Open` is a registry factory, and the `*sql.DB` it returns is meant to be opened once and shared: a singleton by convention.

### Check your understanding
{: #creational-check-your-understanding}

{% include quiz.html id="lld-creational" %}

## Part 4: Structural patterns
{: #structural}

**What's standing in the middle?** Most structural patterns put one object between the caller and another. They differ in what that middle object changes: the shape of the call, the behavior around it, whether it gets through, or how much of the system you see. The shape to watch for on a diagram is a type that implements an interface and also holds a field of that same interface.

| Pattern | Changes | In one line |
| --- | --- | --- |
| [Adapter](#adapter) | The shape | Makes one object fit an interface it wasn't built for. |
| [Decorator](#decorator) | The behavior | Same interface, extra work before or after each call. |
| [Proxy](#proxy) | The access | Same interface, decides whether and when calls get through. |
| [Facade](#facade) | The surface | One simple front door to a whole subsystem. |
| [Composite](#composite) | The count | One item or a whole tree, same call. |
| [Bridge](#bridge) | The axes | A type that varies two ways becomes two hierarchies joined by a field. |
| [Flyweight](#flyweight) | The memory | Many objects share one copy of identical state. |

![Four wrappers compared: Adapter changes the call, Decorator keeps the call and adds behavior, Proxy keeps the call but may answer itself, Facade turns one call into calls on four subsystems](/images/lld/04-structural-patterns/01-overview.webp)
*Read each row left to right. Adapter: the call leaving the middle is a different call. Decorator: the same call, maybe several times. Proxy: the same call, or none at all when it can answer itself. Facade: one call in, four out.*

### Adapter
{: #adapter}

**Changes the shape.** Make an existing object usable through an interface it wasn't written for, without changing either side.

- **Reach for it when:** You integrate a vendor SDK, legacy code or a second provider, and you don't want their API spread through your code.
- **Go idiom:** A small struct that holds the foreign type and implements your interface
- **Python idiom:** A class that wraps the foreign object and exposes your method names

#### Class diagram
{: #structural-class-diagram}

![Class diagram: AlertService holds a Notifier; SlackNotifier and TeamsNotifier implement Notifier and each hold a different vendor client](/images/lld/04-structural-patterns/04-adapter-class-diagram.webp)
*This is the object adapter: it holds the vendor client in a field. The class adapter variant inherits from the adaptee instead; Go can't do that, and in Python it's rarely worth it.*

#### Code
{: #structural-code}

```go
package alert

import (
    "context"
    "fmt"

    "github.com/slack-go/slack"
)

type Severity int

const (
    Info Severity = iota
    Critical
)

type Alert struct {
    Title    string
    Body     string
    Severity Severity
}

// Notifier is our interface, defined by the code that uses it.
type Notifier interface {
    Notify(ctx context.Context, a Alert) error
}

// SlackNotifier adapts *slack.Client to Notifier.
type SlackNotifier struct {
    client  *slack.Client
    channel string
}

func (s *SlackNotifier) Notify(ctx context.Context, a Alert) error {
    text := a.Title + "\n" + a.Body
    if a.Severity == Critical {
        text = ":rotating_light: " + text
    }
    _, _, err := s.client.PostMessageContext(ctx, s.channel, slack.MsgOptionText(text, false))
    if err != nil {
        return fmt.Errorf("slack notify: %w", err) // don't leak the vendor's error types
    }
    return nil
}

// Compile-time check that SlackNotifier implements Notifier.
var _ Notifier = (*SlackNotifier)(nil)
```
{: file="alert/slack.go"}

```go
// The standard library ships an adapter you use every day:
//
//   type HandlerFunc func(ResponseWriter, *Request)
//   func (f HandlerFunc) ServeHTTP(w ResponseWriter, r *Request) { f(w, r) }
//
// It turns a plain function into an http.Handler.
func health(w http.ResponseWriter, r *http.Request) {
    w.Write([]byte("ok"))
}

http.Handle("/healthz", http.HandlerFunc(health))
```
{: file="Go · The adapter in net/http"}

In Go, define the interface where it's used, with only the methods that code needs. Then the adapter stays tiny, and tests can swap in a fake `Notifier` without touching Slack.

**Where you'll find it:** `http.HandlerFunc` (Go's docs call it an adapter), `strings.NewReader`, Python's `io.TextIOWrapper`, dockershim (CRI to Docker, until Kubernetes 1.24), and any MCP server in front of a REST API.

#### Traps
{: #structural-traps}

**Business logic creeping in.** Keep the adapter to translation. If it starts deciding who gets paged, move that rule into your service, where every vendor benefits.

**Vendor types leaking out.** Return your own errors and types. Wrap with `%w` so callers can still inspect the cause if they must.

**An interface shaped like the first vendor.** If `Notifier` mirrors Slack's options, the PagerDuty adapter gets awkward. Design the interface from what your code needs.

**Wrapping the whole SDK.** Adapt only the calls you use. A three-method interface is easy to adapt and easy to fake.

### Decorator
{: #decorator}

**Adds behavior.** Wrap an object in another with the same interface, adding behavior before or after each call. Stack as many as you like.

- **Reach for it when:** You need logging, retries, metrics, caching, timeouts or compression around existing code, in combinations that change.
- **Go idiom:** Middleware: `func(http.Handler) http.Handler`; or a struct with a `next` field
- **Python idiom:** The `@decorator` syntax, which is this pattern applied to functions

#### Class diagram
{: #structural-class-diagram-2}

The shape to remember: a decorator **is** a `Sender` (it implements the interface) and **has** a `Sender` (its `next` field). Because the wrapped thing has the same type as the wrapper, wrappers nest without limit.

![Class diagram: EmailSender and SenderDecorator implement Sender; SenderDecorator also holds a next Sender; RetrySender and LoggingSender extend SenderDecorator](/images/lld/04-structural-patterns/07-decorator-class-diagram.webp)
*Dashed line with a hollow triangle: implements. Solid line with a hollow triangle: extends. The accent arrow is the `next` field, pointing back at the interface.*

#### Order is part of the design
{: #order-is-part-of-the-design}

The same three layers in two orders, with the first SMTP attempt failing. Indentation shows nesting.

**Retry inside Logging:** `Logging(Metrics(Retry(email)))`

```text
logging → Send(order-1042)
    retry: attempt 1
      email: SMTP timeout
    retry: wait 100ms
    retry: attempt 2
      email: 250 OK
  metrics: send_total{result="ok"} +1
logging ← nil
```

1 log line, 1 metric increment, 2 SMTP attempts.

**Retry outside Logging:** `Retry(Logging(Metrics(email)))`

```text
retry: attempt 1
  logging → Send(order-1042)
      email: SMTP timeout
    metrics: send_total{result="error"} +1
  logging ← err: SMTP timeout
retry: wait 100ms
retry: attempt 2
  logging → Send(order-1042)
      email: 250 OK
    metrics: send_total{result="ok"} +1
  logging ← nil
```

2 log lines, 2 metric increments, 2 SMTP attempts. With Retry inside Logging you get one log line per call; with Retry outside, one per attempt. Order matters elsewhere too: with Auth outside Logging, rejected requests never get logged.

#### Code
{: #structural-code-2}

In Go the same shape is usually HTTP middleware: a function that takes an `http.Handler` and returns one.

```go
package web

import (
    "log/slog"
    "net/http"
    "time"
)

// Logging is a decorator: it is an http.Handler, and it wraps one.
func Logging(log *slog.Logger) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            start := time.Now()
            next.ServeHTTP(w, r) // the wrapped handler does the real work
            log.Info("request", "method", r.Method, "path", r.URL.Path, "took", time.Since(start))
        })
    }
}

// Wrappers stack, and the outermost runs first:
//   http.Handle("/orders", Logging(logger)(Auth(orders)))
```
{: file="web/middleware.go"}

```python
import functools
import logging
import time

from tenacity import retry, stop_after_attempt

def logged(fn):
    @functools.wraps(fn)                 # keep fn's name and docstring
    def inner(*args, **kwargs):
        start = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            logging.info("%s took %.1f ms", fn.__name__, (time.perf_counter() - start) * 1000)
    return inner

@logged                                  # outer layer: listed first, runs first
@retry(stop=stop_after_attempt(3))       # inner layer
def send_email(to: str, body: str) -> None:
    ...
```
{: file="decorators.py"}

**Where you'll find it:** HTTP middleware and `http.TimeoutHandler`, `gzip.NewReader` and `bufio.NewReader`, `otelhttp.NewTransport`, gRPC interceptors, and Python's `@functools.lru_cache`.

#### Traps
{: #structural-traps-2}

**Optional interfaces disappear.** Wrapping `http.ResponseWriter` hides `http.Flusher` and `http.Hijacker`, so streaming and websockets quietly break behind your middleware. Give the wrapper an `Unwrap() http.ResponseWriter` method so `http.ResponseController` can reach the original.

**Identity checks break.** A wrapped value is a different value. `==` comparisons and type assertions against the concrete type fail.

**Forgetting functools.wraps.** Without it the wrapper replaces the function's name and docstring, which confuses logs, debuggers and frameworks that register things by name.

### Proxy
{: #proxy}

**Controls access.** Stand in for another object behind the same interface, and decide whether, when and how calls reach it.

- **Reach for it when:** The real object is expensive to create, lives on another machine, needs protecting, or keeps getting asked the same question.
- **Go idiom:** A struct with the same interface that holds, or lazily builds, the real one; `httputil.ReverseProxy`
- **Python idiom:** A class with the same methods; Django's `SimpleLazyObject`

Proxies are named for what they do with a call. A **virtual** proxy builds the real object on first use, a **caching** proxy answers repeats itself, a **protection** proxy refuses unauthorized calls, and a **remote** proxy forwards over the network. One proxy can be several; the one below is virtual and caching.

#### Class diagram
{: #structural-class-diagram-3}

![Class diagram: CachingCatalog and RemoteCatalog both implement Catalog; the proxy holds the real catalog, created lazily, plus a cache](/images/lld/04-structural-patterns/10-proxy-class-diagram.webp)
*Structurally the same as a decorator: implements `Catalog` and holds a `Catalog`. The difference is that this one owns its target and may not forward at all.*

#### Code
{: #structural-code-3}

```go
package catalog

import (
    "context"
    "sync"
)

type Item struct {
    ID    string
    Price int
}

type Catalog interface {
    Get(ctx context.Context, id string) (Item, error)
}

// CachingCatalog is a proxy: the same interface as the real catalog,
// but it decides whether a call reaches the real one at all.
type CachingCatalog struct {
    newReal func() (Catalog, error) // virtual proxy: build the real one on first use

    once    sync.Once
    real    Catalog
    realErr error

    mu    sync.Mutex
    cache map[string]Item
}

func NewCachingCatalog(newReal func() (Catalog, error)) *CachingCatalog {
    return &CachingCatalog{newReal: newReal, cache: map[string]Item{}}
}

func (p *CachingCatalog) Get(ctx context.Context, id string) (Item, error) {
    p.mu.Lock()
    it, ok := p.cache[id]
    p.mu.Unlock()
    if ok {
        return it, nil // answered without touching the real catalog
    }

    backend, err := p.backend()
    if err != nil {
        return Item{}, err
    }
    it, err = backend.Get(ctx, id) // the slow network call happens outside the lock
    if err != nil {
        return Item{}, err
    }

    p.mu.Lock()
    p.cache[id] = it
    p.mu.Unlock()
    return it, nil
}

func (p *CachingCatalog) backend() (Catalog, error) {
    p.once.Do(func() { p.real, p.realErr = p.newReal() })
    return p.real, p.realErr
}
```
{: file="catalog/proxy.go"}

The rest of the diagram is the real catalog, and the `Checkout` that can't tell it from the proxy:

```go
// catalog/remote.go
// RemoteCatalog is the real object: every Get is a network call.
type RemoteCatalog struct {
    conn *grpc.ClientConn
}

func NewRemoteCatalog(conn *grpc.ClientConn) *RemoteCatalog {
    return &RemoteCatalog{conn: conn}
}

// (RemoteCatalog implements Get with an RPC over conn; omitted here)

// checkout/checkout.go
// Checkout depends only on the Catalog interface.
type Checkout struct {
    catalog catalog.Catalog
}

func New(c catalog.Catalog) *Checkout {
    return &Checkout{catalog: c}
}

func (c *Checkout) Price(ctx context.Context, id string) (int, error) {
    it, err := c.catalog.Get(ctx, id)
    return it.Price, err
}

// main.go: Checkout gets the proxy; the remote catalog is created on first use.
proxy := catalog.NewCachingCatalog(func() (catalog.Catalog, error) {
    conn, err := grpc.NewClient("catalog:443",
        grpc.WithTransportCredentials(insecure.NewCredentials()))
    if err != nil {
        return nil, err
    }
    return catalog.NewRemoteCatalog(conn), nil
})
co := checkout.New(proxy)
```
{: file="Go · The real catalog and its client"}

**Where you'll find it:** `httputil.ReverseProxy`, Envoy and NGINX (remote), gRPC client stubs (remote), and Django's `request.user` or SQLAlchemy lazy relationships (virtual).

#### Traps
{: #structural-traps-3}

**Holding a lock across the remote call.** Every caller then waits behind the slowest request. Check the cache under the lock, call outside it, and store under the lock again, as the code does.

**A stampede on a cold cache.** A hundred concurrent misses for one key make a hundred backend calls. `golang.org/x/sync/singleflight` collapses them into one.

**Stale answers.** A cache needs a TTL or an invalidation rule. Decide which before you ship.

**A failed lazy init stays failed.** `sync.Once` never retries, as in the [Singleton traps](#traps). If creating the real object can fail transiently, use a mutex and retry.

### Facade
{: #facade}

**Shrinks the surface.** Give a complicated subsystem one simple front door, so most callers never have to learn the parts behind it.

- **Reach for it when:** Several callers repeat the same multi-step sequence across subsystems, or using a module means learning too many of its parts.
- **Go idiom:** A struct with a few high-level methods that holds the subsystem clients
- **Python idiom:** A class or module-level function; a package's `__init__.py` re-exporting the simple path

#### Class diagram
{: #structural-class-diagram-4}

![Class diagram: SitesHandler calls the SiteProvisioner facade, which holds the Network, Compute, DNS and Registry subsystems; callers can still reach a subsystem directly](/images/lld/04-structural-patterns/13-facade-class-diagram.webp)
*The facade holds the subsystems and offers two methods. It doesn't hide them: the dashed path shows an advanced caller going straight to `Registry`.*

#### Code
{: #structural-code-4}

An infrastructure facade has a job a textbook one doesn't: when step three fails, steps one and two have already changed the world. This one records an undo for each finished step and runs them in reverse on failure.

```go
package sites

import (
    "context"
    "fmt"
)

type Spec struct {
    Name, VPC, CIDR, Size string
    Nodes                 int
}

type Site struct {
    Name   string
    Subnet string
    Nodes  []string
}

// The subsystems, each with its own detailed API.
type Network interface {
    CreateSubnet(ctx context.Context, vpcID, cidr string) (string, error)
    DeleteSubnet(ctx context.Context, subnetID string) error
}
type Compute interface {
    LaunchNodes(ctx context.Context, subnetID, size string, n int) ([]string, error)
    TerminateNodes(ctx context.Context, ids []string) error
}
type DNS interface {
    UpsertRecord(ctx context.Context, name string, targets []string) error
}
type Registry interface {
    Save(ctx context.Context, s Site) error
}

// SiteProvisioner is the facade: one call instead of four services.
type SiteProvisioner struct {
    net Network
    vm  Compute
    dns DNS
    reg Registry
}

func (p *SiteProvisioner) Provision(ctx context.Context, spec Spec) (site Site, err error) {
    var undo []func() // compensating steps, run in reverse if a later step fails
    defer func() {
        if err != nil {
            for i := len(undo) - 1; i >= 0; i-- {
                undo[i]()
            }
        }
    }()

    subnet, err := p.net.CreateSubnet(ctx, spec.VPC, spec.CIDR)
    if err != nil {
        return Site{}, fmt.Errorf("create subnet: %w", err)
    }
    undo = append(undo, func() { _ = p.net.DeleteSubnet(context.WithoutCancel(ctx), subnet) })

    nodes, err := p.vm.LaunchNodes(ctx, subnet, spec.Size, spec.Nodes)
    if err != nil {
        return Site{}, fmt.Errorf("launch nodes: %w", err)
    }
    undo = append(undo, func() { _ = p.vm.TerminateNodes(context.WithoutCancel(ctx), nodes) })

    site = Site{Name: spec.Name + ".sites.example.com", Subnet: subnet, Nodes: nodes}
    if err = p.dns.UpsertRecord(ctx, site.Name, nodes); err != nil {
        return Site{}, fmt.Errorf("dns record: %w", err)
    }
    if err = p.reg.Save(ctx, site); err != nil {
        return Site{}, fmt.Errorf("register: %w", err)
    }
    return site, nil
}
```
{: file="sites/provisioner.go"}

The undo steps use `context.WithoutCancel(ctx)`, so cleanup still runs when the original request was cancelled, which is often the very reason a step failed.

**Where you'll find it:** `os.ReadFile`, `requests.get`, boto3's `upload_file` (multipart upload, parallel parts and per-part retries behind one call), `kubectl apply`, and Terraform modules.

#### Traps
{: #structural-traps-4}

**The god facade.** Sixty methods means it has become a second copy of the subsystem. Split facades by use case.

**Partial failure.** Decide what happens when step three fails: undo in reverse, as above, or make every step idempotent so a retry is safe.

**Blocking the escape hatch.** Most callers want the simple path; a few need the details. Leave the subsystems reachable.

### Composite
{: #composite}

**Hides the count.** Arrange objects in a tree and let callers treat a single item and a whole group exactly the same way.

- **Reach for it when:** The data is naturally a tree (resources, UI widgets, org charts, rule sets) and you keep writing "if it's a group, loop; otherwise…".
- **Go idiom:** One interface implemented by the leaf and by a group that holds `[]Interface`
- **Python idiom:** The same, with a `children` list; duck typing means no shared base is required

#### Class diagram
{: #structural-class-diagram-5}

The giveaway shape: `Group` implements `Resource` and holds many `Resource`s. That one aggregation arrow pointing back at the interface is what makes the structure recursive.

![Class diagram: Pod and Group both implement Resource; Group also holds many Resources as children, which is what makes the tree recursive](/images/lld/04-structural-patterns/16-composite-class-diagram.webp)
*`*` on the aggregation means a group holds any number of children, and each child may itself be a group. The hollow diamond fits the convention from [Part 1](#relationships): a pod can outlive any cost group it's counted in.*

#### Code
{: #structural-code-5}

```go
package capacity

type Resource interface {
    Name() string
    CPU() int // millicores requested
}

// Pod is a leaf.
type Pod struct {
    name     string
    millicpu int
}

func (p Pod) Name() string { return p.name }
func (p Pod) CPU() int     { return p.millicpu }

// Group is the composite: it is a Resource, and it holds Resources.
type Group struct {
    name     string
    children []Resource
}

func (g *Group) Name() string { return g.name }

func (g *Group) CPU() int {
    total := 0
    for _, c := range g.children {
        total += c.CPU() // a child may be a Pod or another Group; no type switch
    }
    return total
}

func (g *Group) Add(rs ...Resource) *Group {
    g.children = append(g.children, rs...)
    return g
}
```
{: file="capacity/resource.go"}

```go
payments := (&Group{name: "payments"}).Add(Pod{"api-1", 250}, Pod{"api-2", 250}, Pod{"worker", 300})
search := (&Group{name: "search"}).Add(Pod{"indexer", 1000}, Pod{"query", 200})
prod := (&Group{name: "prod"}).Add(payments, search)

fmt.Println(prod.CPU(), payments.CPU(), Pod{"query", 200}.CPU()) // 2000 800 200
```
{: file="Go · Using it"}

**Where you'll find it:** `io.MultiWriter`, `errors.Join` (`errors.Is` walks the whole tree), Kubernetes owner references, scikit-learn's `Pipeline`, and Python's `ExceptionGroup`.

#### Traps
{: #structural-traps-5}

**Cycles.** Adding a group to itself, or to its own descendant, makes `CPU()` recurse forever. Check in `Add`.

**Add on the shared interface.** The "transparent" variant puts `Add` on `Resource` so callers never check types, but then `Pod` must implement `Add` and fail at runtime. The "safe" variant above keeps it on `Group`.

**Shared children.** If one pod sits under two groups, totals count it twice. A composite assumes a tree, not a graph.

**Recomputing big trees.** Summing 100,000 nodes on every request adds up. Cache totals on groups and invalidate on change.

### Bridge
{: #bridge}

**Splits two dimensions.** When a type varies along two independent axes, give each axis its own hierarchy and connect them with a field instead of multiplying subclasses.

- **Reach for it when:** You catch yourself naming types like `IncidentSlack` and `DigestEmail`: two ideas glued into one name. Three message kinds times three channels is nine such types; as a bridge it's three plus three.
- **Where you'll find it:** `log/slog`: a `Logger` holds a `Handler`. `database/sql`: a `DB` holds a `driver.Driver`.

```go
// Implementation side: how a message gets delivered.
type Sender interface {
    Deliver(ctx context.Context, to, subject, body string) error
}

// Abstraction side: what kind of message it is.
// Each kind holds a Sender. That field is the bridge.
type Incident struct {
    sender Sender
    id     string
    sev    int
}

func (m Incident) Send(ctx context.Context, oncall string) error {
    subject := fmt.Sprintf("[SEV%d] incident %s", m.sev, m.id)
    return m.sender.Deliver(ctx, oncall, subject, "See the runbook.")
}

type Digest struct {
    sender Sender
    items  []string
}

func (m Digest) Send(ctx context.Context, team string) error {
    return m.sender.Deliver(ctx, team, "Daily digest", strings.Join(m.items, "\n"))
}

// Any kind × any channel, picked at runtime. Adding Teams means one new Sender.
err := Incident{sender: SlackSender{}, id: "INC-311", sev: 1}.Send(ctx, "#oncall")
```
{: file="notify/bridge.go"}

### Flyweight
{: #flyweight}

**Shares identical state.** When you have huge numbers of similar objects, share the parts that are identical and store only the differences per object.

- **Vocabulary:** Intrinsic state is shared and immutable (the label set). Extrinsic state is per object (time and value).
- **Where you'll find it:** Prometheus keeps each series' label set once and appends only (timestamp, value) pairs. CPython caches small ints and interns many strings. Go 1.23 added `unique.Make`.
- **Python idiom:** An `@lru_cache` factory that returns frozen dataclasses; `sys.intern` for strings

```go
type Labels struct {
    Service, Region, Host string
}

// LabelPool is the flyweight factory: one shared *Labels per distinct value.
type LabelPool struct {
    mu   sync.Mutex
    sets map[Labels]*Labels
}

func (p *LabelPool) Get(l Labels) *Labels {
    p.mu.Lock()
    defer p.mu.Unlock()
    if shared, ok := p.sets[l]; ok {
        return shared
    }
    if p.sets == nil {
        p.sets = map[Labels]*Labels{}
    }
    shared := &l
    p.sets[l] = shared
    return shared
}

// Each sample stores only what differs, plus a pointer to the shared part.
type Sample struct {
    labels *Labels // shared: treat as read-only
    ts     int64
    value  float64
}
```
{: file="metrics/labels.go"}

```go
// Go 1.23+: package unique interns comparable values for you,
// and frees them once nothing refers to them any more.
a := unique.Make(Labels{Service: "api", Region: "us-east-1", Host: "ip-10-0-1-7"})
b := unique.Make(Labels{Service: "api", Region: "us-east-1", Host: "ip-10-0-1-7"})
fmt.Println(a == b) // true: one shared copy, compared by pointer
labels := a.Value() // read the shared value
```
{: file="Go · package unique, Go 1.23+"}

#### Traps
{: #structural-traps-6}

**Mutable shared state.** If one sample edits its labels, every sample sharing them changes. The shared part must be immutable.

**A pool that never forgets.** An interning map that only grows is a memory leak. `unique.Make` frees values nothing refers to; a plain map doesn't.

### They combine
{: #structural-they-combine}

A few lines of ordinary Go server code hold three of these patterns:

```go
backend, err := url.Parse("http://orders.internal:8080")
if err != nil {
    log.Fatal(err)
}
rp := httputil.NewSingleHostReverseProxy(backend) // Proxy: the real handler is on another machine
http.Handle("/orders/", Logging(logger)(rp))      // Decorator: same http.Handler, more behavior
// ...and inside Logging, http.HandlerFunc is an Adapter.
```
{: file="main.go"}

### Check your understanding
{: #structural-check-your-understanding}

{% include quiz.html id="lld-structural" %}

## Part 5: Behavioral patterns
{: #behavioral}

**Who decides what happens next?** Each behavioral pattern takes one decision away from code that would otherwise hard-wire it. Find the decision being moved and you've found the pattern.

| Pattern | Decides | In one line |
| --- | --- | --- |
| [Strategy](#strategy) | How the work is done | Pick the algorithm at runtime; the caller stays the same. |
| [Observer](#observer) | Who reacts | Everyone who subscribed hears it; the source doesn't know who they are. |
| [State](#state) | What a call means now | Same call, different behavior per mode; the object switches itself. |
| [Command](#command) | When it runs | A call becomes a value you can queue, log, retry or undo. |
| [Chain](#chain-of-responsibility) | Who handles it | Each handler takes the request or hands it to the next. |

Five [specialists](#five-specialists) follow: Template Method, Iterator, Mediator, Memento and Visitor.

### Strategy
{: #strategy}

**Swap the how.** Define a family of interchangeable ways to do one job, and let the caller pick one, even while running.

- **Reach for it when:** There are several ways to do one job (scaling policies, backoff schedules, compression, pricing rules) and the choice comes from config or changes at runtime.
- **Go idiom:** A one-method interface, or simply a `func` value
- **Python idiom:** A callable passed in (`key=`), or a small class per strategy

#### Three policies, three situations
{: #three-policies-three-situations}

Three scaling policies answer the same question: how many replicas should run? The autoscaler clamps every answer to 2–20.

| Situation | `TargetTracking{Target: 60}` | `StepScaling{}` | `Scheduled{Peak: 8, OffPeak: 2}` |
| --- | --- | --- | --- |
| CPU 84%, 4 replicas, 22:00 | 6 | 6 | 2 |
| CPU 45%, 4 replicas, 11:00 | 3 | 4 | 8 |
| CPU 20%, 6 replicas, 02:00 | 2 | 5 | 2 |

Same inputs, three answers. Which one runs is a single `SetPolicy` call; the autoscaler's own code never changes.

#### Class diagram
{: #behavioral-class-diagram}

![Class diagram: Autoscaler holds a ScalePolicy; TargetTracking, StepScaling and Scheduled implement it](/images/lld/05-behavioral-patterns/03-strategy-class-diagram.webp)
*The autoscaler depends only on the `ScalePolicy` interface. Adding a fourth policy means writing one type; the autoscaler doesn't change.*

#### Code
{: #behavioral-code}

```go
package scaling

import "math"

type Metrics struct {
    CPU  float64 // average utilization, 0–100
    Hour int     // local hour, 0–23
}

// ScalePolicy is the strategy: given the current size and the metrics,
// how many replicas should run?
type ScalePolicy interface {
    Desired(current int, m Metrics) int
}

type TargetTracking struct{ Target float64 }

func (p TargetTracking) Desired(current int, m Metrics) int {
    return int(math.Ceil(float64(current) * m.CPU / p.Target))
}

type StepScaling struct{}

func (StepScaling) Desired(current int, m Metrics) int {
    switch {
    case m.CPU > 80:
        return current + 2
    case m.CPU > 60:
        return current + 1
    case m.CPU < 30:
        return current - 1
    }
    return current
}

type Scheduled struct{ Peak, OffPeak int }

func (p Scheduled) Desired(_ int, m Metrics) int {
    if m.Hour >= 9 && m.Hour < 18 {
        return p.Peak
    }
    return p.OffPeak
}

// Autoscaler is the context: it uses a policy without knowing which one.
type Autoscaler struct {
    policy   ScalePolicy
    min, max int
}

func (a *Autoscaler) SetPolicy(p ScalePolicy) { a.policy = p } // swap at runtime

func (a *Autoscaler) Decide(current int, m Metrics) int {
    return max(a.min, min(a.max, a.policy.Desired(current, m)))
}
```
{: file="scaling/policy.go"}

```go
// A strategy doesn't have to be a type. Often it's just a function value.
slices.SortFunc(pods, func(a, b Pod) int {
    return cmp.Compare(b.CPU, a.CPU) // the comparison strategy: busiest first
})
```
{: file="Go · A func is a strategy too"}

**Where you'll find it:** `slices.SortFunc` (the comparison func is the strategy), `http.Client.CheckRedirect`, kube-scheduler plugins, Python's `sorted(key=…)`, and scikit-learn estimators.

#### Traps
{: #behavioral-traps}

**Choosing in every caller.** The `switch` that picks a strategy belongs in one place, typically a factory at startup, not spread through the code.

**Swapping while running.** `SetPolicy` on one goroutine while another calls `Decide` is a data race. Guard the field with a mutex or keep it in an `atomic.Pointer`.

**A strategy for two branches that never change.** An `if` is fine. Reach for the pattern when the options grow or come from config.

### Observer
{: #observer}

**Broadcast a change.** Let any number of objects subscribe to changes in another, and notify all of them when it changes, without the source knowing who they are.

- **Reach for it when:** One change should trigger several independent reactions (metering, alerts, audit), and you want to add reactions without editing the source.
- **Go idiom:** A registry of callbacks, or one buffered channel per subscriber
- **Python idiom:** A list of callables; `logging` handlers; libraries such as blinker

Delivery mode matters when one subscriber is slow. With synchronous callbacks, `Publish` returns only after the slowest one finishes, so the publisher waits. With one buffered channel per subscriber, `Publish` returns at once and each subscriber catches up from its buffer.

#### Class diagram
{: #behavioral-class-diagram-2}

![Class diagram: StatusFeed holds any number of Subscribers; Metering, Alerter and AuditLog implement Subscriber; CEController publishes to the feed](/images/lld/05-behavioral-patterns/06-observer-class-diagram.webp)
*The hollow diamond with `*` is the Gang of Four book's way of saying the feed holds any number of subscribers it doesn't own. Under the convention from [Part 1](#relationships), that's a plain association: a feed isn't made of its subscribers. The arrow points from the subject to the interface, never to a concrete subscriber.*

#### Code
{: #behavioral-code-2}

```go
package events

import "sync"

type Event struct {
    Engine string
    Status string // "Starting", "Running", "Degraded", ...
}

// StatusFeed is the subject. It knows its subscribers only as functions.
type StatusFeed struct {
    mu     sync.Mutex
    nextID int
    subs   map[int]func(Event)
}

// Subscribe registers fn and returns a function that unsubscribes it.
func (f *StatusFeed) Subscribe(fn func(Event)) (unsubscribe func()) {
    f.mu.Lock()
    defer f.mu.Unlock()
    if f.subs == nil {
        f.subs = map[int]func(Event){}
    }
    id := f.nextID
    f.nextID++
    f.subs[id] = fn
    return func() {
        f.mu.Lock()
        defer f.mu.Unlock()
        delete(f.subs, id)
    }
}

// Publish calls every subscriber. It copies the list first and calls the
// callbacks outside the lock, so a callback may subscribe or unsubscribe
// without deadlocking.
func (f *StatusFeed) Publish(e Event) {
    f.mu.Lock()
    subs := make([]func(Event), 0, len(f.subs))
    for _, fn := range f.subs {
        subs = append(subs, fn)
    }
    f.mu.Unlock()
    for _, fn := range subs {
        fn(e)
    }
}
```
{: file="events/feed.go"}

```go
// The channel version: each subscriber gets its own buffered channel,
// so one slow subscriber can't stall the publisher.
type Broadcaster struct {
    mu   sync.Mutex
    subs []chan Event
}

func (b *Broadcaster) Subscribe(buffer int) <-chan Event {
    ch := make(chan Event, buffer)
    b.mu.Lock()
    b.subs = append(b.subs, ch)
    b.mu.Unlock()
    return ch
}

func (b *Broadcaster) Publish(e Event) (dropped int) {
    b.mu.Lock()
    defer b.mu.Unlock()
    for _, ch := range b.subs {
        select {
        case ch <- e:
        default:
            dropped++ // buffer full: drop instead of blocking (a deliberate policy)
        }
    }
    return dropped
}
```
{: file="Go · The channel version"}

**Where you'll find it:** client-go informers' `AddEventHandler`, `signal.Notify`, SNS, EventBridge and Kafka consumer groups across processes, Python `logging` handlers, and Django signals.

#### Traps
{: #behavioral-traps-2}

**A full buffer needs a policy.** When a channel subscriber falls behind, decide whether `Publish` blocks, drops the event (as `Broadcaster` does), or drops the oldest.

**Lapsed listeners.** A subscriber that never unsubscribes stays alive forever, along with everything it references. Return an unsubscribe function and `defer` it.

**Relying on order.** Go map iteration is random, so subscribers run in a different order each time. If B must run after A, that's a workflow, not an observer.

**Calling back under a lock.** If `Publish` holds the mutex while calling subscribers, one that calls `Subscribe` deadlocks. Copy the list, unlock, then call, as the code does.

### State
{: #state}

**Behave by mode.** Let an object change its behavior when its internal mode changes, by giving each mode its own object.

- **Reach for it when:** Every method starts with `switch status`, and adding a mode means editing all of them.
- **Go idiom:** One type per state behind an interface, or a transition table for simple machines
- **Python idiom:** A class per state with refusing defaults; or the `transitions` library

#### The state machine
{: #the-state-machine}

`Start()` and `Stop()` are calls your code makes; done, timeout and crash are events from outside.

![UML state machine: Stopped goes to Starting on Start; Starting goes to Running when done or to Failed on timeout; Running goes to Stopping on Stop or Failed on crash; Stopping returns to Stopped when drained; Failed goes back to Starting on Start](/images/lld/05-behavioral-patterns/08-state-state-machine.webp)
*Rounded boxes are states, arrows are transitions labeled with what triggers them, and the black dot is where a new instance starts.*

| State | Start() | Stop() | Done() | timeout | crash |
| --- | --- | --- | --- | --- | --- |
| Stopped | → Starting | no-op | error: nothing in flight | – | – |
| Starting | no-op | error: cannot stop while starting | → Running | → Failed | – |
| Running | no-op | → Stopping | error: nothing in flight | – | → Failed |
| Stopping | error: wait until stopped | no-op | → Stopped | – | – |
| Failed | → Starting | no-op | error: nothing in flight | – | – |

A dash means the state doesn't listen for that event.

#### Class diagram
{: #behavioral-class-diagram-3}

![Class diagram: Instance holds a current State; Stopped, Starting, Running and Stopping implement State and call back into Instance to set the next state](/images/lld/05-behavioral-patterns/09-state-class-diagram.webp)
*Same shape as Strategy: the context holds an interface. The difference is the accent arrow. States call back into the instance to choose the next state.*

#### Code
{: #behavioral-code-3}

```go
package lifecycle

import "fmt"

// State is one mode of an Instance. Each method decides what that call
// means in this mode, and which state comes next.
type State interface {
    Name() string
    Start(i *Instance) error
    Stop(i *Instance) error
    Done(i *Instance) error // the in-flight operation finished
}

type Instance struct{ state State }

func NewInstance() *Instance { return &Instance{state: Stopped{}} }

func (i *Instance) Start() error     { return i.state.Start(i) }
func (i *Instance) Stop() error      { return i.state.Stop(i) }
func (i *Instance) Done() error      { return i.state.Done(i) }
func (i *Instance) State() string    { return i.state.Name() }
func (i *Instance) setState(s State) { i.state = s }

type Stopped struct{}

func (Stopped) Name() string            { return "Stopped" }
func (Stopped) Start(i *Instance) error { i.setState(Starting{}); return nil }
func (Stopped) Stop(*Instance) error    { return nil } // already stopped
func (Stopped) Done(*Instance) error    { return fmt.Errorf("nothing in flight") }

type Starting struct{}

func (Starting) Name() string           { return "Starting" }
func (Starting) Start(*Instance) error  { return nil } // already on its way
func (Starting) Stop(*Instance) error   { return fmt.Errorf("cannot stop while starting") }
func (Starting) Done(i *Instance) error { i.setState(Running{}); return nil }

type Running struct{}

func (Running) Name() string           { return "Running" }
func (Running) Start(*Instance) error  { return nil } // no-op: already running
func (Running) Stop(i *Instance) error { i.setState(Stopping{}); return nil }
func (Running) Done(*Instance) error   { return fmt.Errorf("nothing in flight") }

type Stopping struct{}

func (Stopping) Name() string           { return "Stopping" }
func (Stopping) Start(*Instance) error  { return fmt.Errorf("wait until stopped") }
func (Stopping) Stop(*Instance) error   { return nil } // already on its way
func (Stopping) Done(i *Instance) error { i.setState(Stopped{}); return nil }
```
{: file="lifecycle/state.go"}

```go
i := NewInstance()
_ = i.Start()          // Stopped → Starting
_ = i.Done()           // Starting → Running
_ = i.Start()          // Running: no-op
fmt.Println(i.State()) // Running
fmt.Println(i.Stop(), i.Stop(), i.Start()) // <nil> <nil> wait until stopped
```
{: file="Go · Using it"}

##### Or a transition table
{: #or-a-transition-table}

When states carry no data and no logic of their own, a table is shorter and easier to review. It also includes `Failed`, which the interface version leaves out for brevity.

```go
// Table-driven alternative: clearer when states carry no data or logic.
type state string
type event string

var transitions = map[state]map[event]state{
    "Stopped":  {"start": "Starting"},
    "Starting": {"done": "Running", "timeout": "Failed"},
    "Running":  {"stop": "Stopping", "crash": "Failed"},
    "Stopping": {"done": "Stopped"},
    "Failed":   {"start": "Starting"},
}

func next(s state, e event) (state, error) {
    if to, ok := transitions[s][e]; ok {
        return to, nil
    }
    return s, fmt.Errorf("%s: event %q not allowed", s, e)
}
```
{: file="lifecycle/table.go"}

**Where you'll find it:** EC2 instance and Kubernetes Pod lifecycles, TCP connection states, `http.Server.ConnState`, and AWS Step Functions.

#### Traps
{: #behavioral-traps-3}

**Transitions scattered everywhere.** If any code can set `status = "Running"`, the machine is only a suggestion. Only states call `setState`.

**A state with no way out.** Every in-progress state needs an exit, including a timeout. A Starting that never hears back must move to Failed, or it waits forever.

**Racing events.** Two goroutines calling Start and Stop at once can both see Running. Lock the instance, or let one goroutine own it and feed it events through a channel.

**Silently ignored calls.** Decide per state whether an unexpected call is a no-op or an error, and log it. A swallowed Stop() becomes a support ticket.

### Command
{: #command}

**Package the request.** Turn a request into an object that carries everything needed to run it, so it can be queued, logged, retried, sent elsewhere or undone.

- **Reach for it when:** You need to queue, schedule, retry, audit or undo operations, or hand them to another process.
- **Go idiom:** An interface with `Execute` (and `Undo`); a `func()` closure for the simplest case
- **Python idiom:** A dataclass per command; `functools.partial` for lightweight ones

#### Class diagram
{: #behavioral-class-diagram-4}

![Class diagram: Runner holds queued and executed Commands; Scale and RotateCert implement Command and act on the Cluster receiver](/images/lld/05-behavioral-patterns/12-command-class-diagram.webp)
*The runner holds commands only through the interface. Both commands act on the same receiver, which is the code that actually changes the cluster.*

#### Code
{: #behavioral-code-4}

```go
package ops

import (
    "context"
    "fmt"
)

// Cluster is the receiver: it knows how to do the actual work.
type Cluster struct {
    replicas int
    cert     string
}

func (c *Cluster) Replicas() int        { return c.replicas }
func (c *Cluster) SetReplicas(n int)    { c.replicas = n }
func (c *Cluster) InstallCert(p string) { c.cert = p }

// Command is a request turned into a value: it can wait in a queue,
// be logged, be retried, or be undone.
type Command interface {
    Name() string
    Execute(ctx context.Context) error
    Undo(ctx context.Context) error
}

type Scale struct {
    C    *Cluster
    To   int
    from int // remembered by Execute so Undo can put it back
}

func (s *Scale) Name() string { return fmt.Sprintf("scale to %d", s.To) }

func (s *Scale) Execute(context.Context) error {
    s.from = s.C.Replicas()
    s.C.SetReplicas(s.To)
    return nil
}

func (s *Scale) Undo(context.Context) error {
    s.C.SetReplicas(s.from)
    return nil
}

// Runner is the invoker: it decides when commands run, and keeps history.
type Runner struct {
    queue   []Command
    history []Command
}

func (r *Runner) Submit(c Command) { r.queue = append(r.queue, c) }

func (r *Runner) RunNext(ctx context.Context) error {
    if len(r.queue) == 0 {
        return nil
    }
    c := r.queue[0]
    r.queue = r.queue[1:]
    if err := c.Execute(ctx); err != nil {
        return fmt.Errorf("%s: %w", c.Name(), err)
    }
    r.history = append(r.history, c)
    return nil
}

func (r *Runner) Undo(ctx context.Context) error {
    if len(r.history) == 0 {
        return fmt.Errorf("nothing to undo")
    }
    c := r.history[len(r.history)-1]
    r.history = r.history[:len(r.history)-1]
    return c.Undo(ctx)
}
```
{: file="ops/command.go"}

```go
c := &Cluster{replicas: 3}
var r Runner
r.Submit(&Scale{C: c, To: 5})
r.Submit(&Scale{C: c, To: 8})

_ = r.RunNext(ctx) // 3 → 5
_ = r.RunNext(ctx) // 5 → 8
_ = r.Undo(ctx)    // back to 5

fmt.Println(c.Replicas()) // 5
```
{: file="Go · Using it"}

**Where you'll find it:** `exec.Cmd` (configure now, `Run` later), database migrations (up and down), `terraform plan -out` then `apply`, and SQS messages or Celery tasks run by another process.

#### Traps
{: #behavioral-traps-4}

**Undo that can't undo.** An email can't be unsent and a deleted volume can't be undeleted. Mark those commands irreversible, or give them a compensating action.

**Capturing references, not values.** A command holding a pointer to a mutable request sees later edits. Copy what it needs when it's created.

**Retries without idempotency.** A worker that crashes after Execute but before acknowledging runs the command twice. Give each command an ID and make Execute safe to repeat.

**Undo after someone else's change.** Restoring 3 replicas after another operator scaled to 10 silently clobbers their change. Check the current value first, or refuse.

### Chain of Responsibility
{: #chain-of-responsibility}

**Pass it along.** Give a request to a line of handlers. Each one either handles it or passes it to the next, so the sender doesn't need to know who will take it.

- **Reach for it when:** Several handlers might apply, in a known order of preference: authentication methods, credential sources, routing rules, approval levels.
- **Go idiom:** A slice of handlers tried in order; or a `next` field on each link
- **Python idiom:** A list of callables, each returning `None` to pass

#### Where each credential stops
{: #where-each-credential-stops}

Different credentials sent through an API gateway's authentication chain of client certificate, then service account token, then OIDC:

| Credential | Where it stops | Result |
| --- | --- | --- |
| client certificate | x509, the first link | `ci-runner` |
| service account token | ServiceAccount, after x509 passes | `system:serviceaccount:ci:deployer` |
| OIDC id_token | OIDC, after two passes | `alice@example.com` |
| expired service account token | ServiceAccount: mine, but expired | 401; the chain stops here |
| no credentials | falls off the end | 401, `ErrUnauthorized` |

#### Class diagram
{: #behavioral-class-diagram-5}

![Class diagram: CertAuth, TokenAuth and OIDCAuth implement Authenticator and each hold the next Authenticator; the Gateway holds the first link](/images/lld/05-behavioral-patterns/15-chain-class-diagram.webp)
*The classic shape: every link implements the interface and holds the next one. The accent arrow is that `next` field, pointing back at the interface.*

#### Code
{: #behavioral-code-5}

```go
package auth

import (
    "errors"
    "net/http"
    "strings"
)

type User struct{ Name string }

// Authenticator is one link. ok=false means "not mine, ask the next one".
// An error means "mine, but invalid".
type Authenticator interface {
    Authenticate(r *http.Request) (u User, ok bool, err error)
}

// Chain tries each link in order; the first that says ok wins.
// Note that Chain is itself an Authenticator, so chains nest.
type Chain []Authenticator

var ErrUnauthorized = errors.New("unauthorized")

func (c Chain) Authenticate(r *http.Request) (User, bool, error) {
    for _, a := range c {
        u, ok, err := a.Authenticate(r)
        if err != nil {
            return User{}, false, err // recognized but invalid: stop here
        }
        if ok {
            return u, true, nil
        }
    }
    return User{}, false, ErrUnauthorized // fell off the end
}

type ClientCert struct{}

func (ClientCert) Authenticate(r *http.Request) (User, bool, error) {
    if r.TLS == nil || len(r.TLS.PeerCertificates) == 0 {
        return User{}, false, nil // not mine
    }
    return User{Name: r.TLS.PeerCertificates[0].Subject.CommonName}, true, nil
}

type BearerToken struct {
    // Verify reports ok=false for tokens it doesn't recognize (another issuer)
    // and an error for tokens it recognizes but rejects (expired, bad signature).
    Verify func(token string) (u User, ok bool, err error)
}

func (b BearerToken) Authenticate(r *http.Request) (User, bool, error) {
    token, found := strings.CutPrefix(r.Header.Get("Authorization"), "Bearer ")
    if !found {
        return User{}, false, nil // no bearer token: not mine
    }
    return b.Verify(token)
}
```
{: file="auth/chain.go"}

```go
authn := Chain{
    ClientCert{},
    BearerToken{Verify: serviceAccounts.Verify},
    BearerToken{Verify: oidcIssuer.Verify},
}

u, ok, err := authn.Authenticate(r)
if err != nil || !ok {
    http.Error(w, "unauthorized", http.StatusUnauthorized)
    return
}
```
{: file="Go · Using it"}

**Where you'll find it:** the AWS SDK default credential chain (environment, config files, web identity, container, then instance metadata; boto3 works the same way), kube-apiserver authentication, exceptions climbing the call stack, and Python logging propagation.

#### Traps
{: #behavioral-traps-5}

**Falling off the end.** Always end the chain with a decision, a rejection or an anonymous user, so nothing is silently dropped.

**Order is policy.** Put cheap and specific handlers first. Moving OIDC ahead of client certificates changes who gets authenticated as what.

**What "mine, but invalid" means.** This chain stops with 401 on an expired token. kube-apiserver's union authenticator keeps trying the remaining authenticators by default and reports the combined errors. Both are reasonable; choose on purpose.

**Who handled it?** Log the handler's name with the result, or debugging means reading every link.

### Five specialists
{: #five-specialists}

You'll mostly use these rather than write them. Each gets the code and the one thing to know.

#### Template Method
{: #template-method}

Write the algorithm once, in a fixed order, and let subclasses (or, in Go, the type you pass in) fill in the steps.

- **Where you'll find it:** `sort.Sort` and `heap.Init` with their interfaces; `unittest.TestCase` (`setUp`, the test, `tearDown`); `threading.Thread.run`.

```go
// sort.Sort is a template method: the algorithm is fixed inside the
// standard library, and you supply the three steps it calls.
type byCPU []Pod

func (p byCPU) Len() int           { return len(p) }
func (p byCPU) Less(i, j int) bool { return p[i].CPU > p[j].CPU }
func (p byCPU) Swap(i, j int)      { p[i], p[j] = p[j], p[i] }

sort.Sort(byCPU(pods)) // busiest first
```
{: file="Go · sort.Sort: the template method in Go"}

```python
from abc import ABC, abstractmethod

class Reconciler(ABC):
    def run(self) -> None:                   # the template method: a fixed order
        want, have = self.desired(), self.actual()
        for change in self.diff(want, have):
            self.apply(change)
        self.report(len(want))

    @abstractmethod
    def desired(self) -> set: ...            # steps each subclass must fill in

    @abstractmethod
    def actual(self) -> set: ...

    @abstractmethod
    def apply(self, change) -> None: ...

    def diff(self, want: set, have: set):    # a default step, overridable
        return [("create", x) for x in sorted(want - have)] + \
               [("delete", x) for x in sorted(have - want)]

    def report(self, n: int) -> None:        # a hook: does nothing unless overridden
        pass
```
{: file="reconcile.py"}

**Template Method or Strategy?** Template Method varies one step inside a fixed skeleton, usually through inheritance. Strategy swaps the whole algorithm through composition. In Go you'll mostly write the Strategy shape, because there's no inheritance to lean on.

#### Iterator
{: #iterator}

Walk through a collection one item at a time without knowing how it's stored or fetched.

- **Where you'll find it:** Go 1.23 range-over-func with `iter.Seq`; `bufio.Scanner`; `sql.Rows.Next`; AWS SDK paginators; every Python `for` loop and generator.

```go
// AllPods hides pagination behind an iterator (Go 1.23 range-over-func).
func AllPods(ctx context.Context, api PodLister) iter.Seq2[Pod, error] {
    return func(yield func(Pod, error) bool) {
        token := ""
        for {
            page, next, err := api.ListPods(ctx, token)
            if err != nil {
                yield(Pod{}, err)
                return
            }
            for _, p := range page {
                if !yield(p, nil) {
                    return // the caller broke out of the loop
                }
            }
            if next == "" {
                return
            }
            token = next
        }
    }
}

for pod, err := range AllPods(ctx, api) {
    if err != nil {
        return err
    }
    fmt.Println(pod.Name)
}
```
{: file="Go · pods.go (Go 1.23+)"}

```python
def all_pods(api):
    """A generator hides pagination: callers just loop."""
    token = None
    while True:
        page, token = api.list_pods(token)
        yield from page
        if token is None:
            return

for pod in all_pods(api):
    print(pod["name"])
```
{: file="pods.py"}

**Stopping early must clean up.** In Go, return as soon as `yield` returns false so pages, rows or connections are released. In Python, put cleanup in a `finally` block; it runs when the generator is closed.

#### Mediator
{: #mediator}

Stop components from talking to each other directly. They report to one object, and it decides what happens next.

- **Where you'll find it:** Kubernetes controllers never call each other; they coordinate through objects in the API server. A CI pipeline definition decides that tests run after the build, so the build step doesn't have to.

```go
// Pipeline is the mediator: components report to it, and only it
// decides what happens next. Components never call each other.
type Pipeline struct {
    test   *Tester
    deploy *Deployer
    notify *Notifier
}

func (p *Pipeline) Notify(from, event string) {
    switch {
    case event == "failed":
        p.notify.Send(from + " failed")
    case from == "build":
        p.test.Run()
    case from == "test":
        p.deploy.Rollout()
    case from == "deploy":
        p.notify.Send("released")
    }
}

// A component only knows the mediator:
func (b *Builder) Finish(ok bool) {
    if ok {
        b.pipeline.Notify("build", "ok")
    } else {
        b.pipeline.Notify("build", "failed")
    }
}
```
{: file="pipeline.go"}

Changing the order of steps now means editing one object instead of four. **The mediator can become a god object**, so keep only coordination in it; the real work stays in the components.

#### Memento
{: #memento}

Capture an object's state as an opaque snapshot, so it can be restored later without exposing its internals.

- **Where you'll find it:** `SAVEPOINT` and `ROLLBACK TO SAVEPOINT` in SQL; `etcdctl snapshot save` and `snapshot restore`; EBS and VM snapshots; editor undo history.

```go
package config

// Snapshot is the memento. Its fields are unexported, so code outside this
// package can store and hand back a Snapshot but can't read or change it.
type Snapshot struct {
    replicas int
    image    string
}

type Config struct {
    replicas int
    image    string
}

func (c *Config) Save() Snapshot      { return Snapshot{c.replicas, c.image} }
func (c *Config) Restore(s Snapshot)  { c.replicas, c.image = s.replicas, s.image }
func (c *Config) SetImage(img string) { c.image = img }
```
{: file="config/snapshot.go"}

```go
history := []config.Snapshot{cfg.Save()} // the caretaker holds snapshots, never looks inside
cfg.SetImage("api:v3")                   // a risky change
cfg.Restore(history[len(history)-1])     // roll back
```
{: file="Go · The caretaker"}

**Snapshots cost memory, and shallow copies share data.** Keep a bounded history or store diffs, and copy maps, slices and pointers deeply, or the snapshot changes along with the live object.

#### Visitor
{: #visitor}

Add new operations over a fixed set of types without changing those types.

- **Where you'll find it:** `go/ast.Walk` with an `ast.Visitor` (and `ast.Inspect`, its function form); Python's `ast.NodeVisitor`; linters and formatters walking syntax trees.

```go
type Visitor interface {
    VisitPod(*Pod)
    VisitService(*Service)
}

type Resource interface{ Accept(Visitor) }

type Pod struct {
    Name string
    CPU  int // millicores
}

type Service struct {
    Name         string
    LoadBalancer bool
}

func (p *Pod) Accept(v Visitor)     { v.VisitPod(p) }     // double dispatch: the element
func (s *Service) Accept(v Visitor) { v.VisitService(s) } // picks the visitor method

// A new operation is a new visitor; Pod and Service don't change.
type CostVisitor struct{ Monthly float64 }

func (c *CostVisitor) VisitPod(p *Pod) { c.Monthly += float64(p.CPU) / 1000 * 25 } // illustrative rate
func (c *CostVisitor) VisitService(s *Service) {
    if s.LoadBalancer {
        c.Monthly += 18 // illustrative rate
    }
}
```
{: file="resources.go"}

**A type switch is often simpler.** Visitor makes adding an operation cheap (one new visitor) and adding a type expensive (every visitor changes). A type switch is the opposite, so reach for Visitor only when the types are fixed and the operations keep growing.

### Check your understanding
{: #behavioral-check-your-understanding}

{% include quiz.html id="lld-behavioral" %}

## Part 6: Field guide: which pattern, and when?
{: #field-guide}

Everything from Parts 3 to 5, arranged for the moment you have a real problem: find the problem, get a pattern, rule out its lookalike, and check whether something simpler would do. All 23 Gang of Four patterns are here, plus the simple factory.

### The map
{: #the-map}

| Bucket | The question | Write often | Use sometimes | Rarely build |
|---|---|---|---|---|
| **Creational** · how objects are born | Who gets to call new? | [Singleton](#singleton), [Factory](#factory), [Builder](#builder) | [Factory Method](#factory-method), [Abstract Factory](#abstract-factory), [Prototype](#prototype) | – |
| **Structural** · how objects are wired | What's standing in the middle? | [Adapter](#adapter), [Decorator](#decorator), [Proxy](#proxy), [Facade](#facade), [Composite](#composite) | [Bridge](#bridge) | [Flyweight](#flyweight) |
| **Behavioral** · how objects decide | Who decides what happens next? | [Strategy](#strategy), [Observer](#observer), [State](#state), [Command](#command), [Chain of Responsibility](#chain-of-responsibility) | [Template Method](#template-method), [Iterator](#iterator), [Mediator](#mediator) | [Memento](#memento), [Visitor](#visitor), [Interpreter](#interpreter) |

### Pattern finder
{: #pattern-finder}

Find the situation closest to yours.

#### Creating objects
{: #creating-objects}

| Situation | Pattern | Why |
|---|---|---|
| Every handler opens its own database pool or client | [Singleton](#singleton) | You need one shared instance per process. Create it once, in main or behind `sync.Once`, and share it. |
| The concrete type depends on config: s3, gcs or local | [Factory](#factory) | One function maps the config value to a type and returns the interface. Callers never name the concrete type. |
| The same switch on type is copied into several places | [Factory](#factory) | Move the switch into one function. A registry lets new types add themselves. |
| A constructor takes eight arguments, most of them optional | [Builder](#builder) | Name each setting and default the rest. In Go, functional options are the usual form. |
| Some field combinations are invalid and must be rejected | [Builder](#builder) | `Build()` is the one place to validate across fields before the object exists. |
| Several resources must all come from the same cloud or backend | [Abstract Factory](#abstract-factory) | Choosing one factory chooses a whole matching family, so mixed providers can't happen. |
| A shared workflow differs only in what it creates | [Factory Method](#factory-method) | Keep the workflow in one place and inject, or override, only the creation step. |
| I must change an object that came from a shared cache | [Prototype](#prototype) | Clone it first (`DeepCopy()`, `copy.deepcopy`) so other readers of the cache aren't affected. |

#### Connecting and wrapping
{: #connecting-and-wrapping}

| Situation | Pattern | Why |
|---|---|---|
| A vendor SDK doesn't match the interface my code uses | [Adapter](#adapter) | A thin type translates your calls into the SDK's and keeps vendor types out of your code. |
| Add logging, metrics or retries around existing calls | [Decorator](#decorator) | A wrapper with the same interface adds the behavior and stacks with other wrappers. |
| Run the same code around every HTTP handler or RPC | [Decorator](#decorator) | That's middleware: `func(http.Handler) http.Handler`, or gRPC interceptors. |
| A dependency is slow or remote and asked the same thing repeatedly | [Proxy](#proxy) | A caching proxy answers repeats itself and calls through only on a miss. |
| Don't create or connect until something is actually needed | [Proxy](#proxy) | A virtual proxy builds the real object on first use, with `sync.Once` inside. |
| Check permissions before calls reach the real object | [Proxy](#proxy) | A protection proxy refuses the call before forwarding anything. |
| Callers repeat the same multi-step sequence across several services | [Facade](#facade) | Write the sequence once behind one method, including what happens when a step fails. |
| The same call must work on one item or a whole tree of them | [Composite](#composite) | Groups implement the item's interface and forward to their children. |
| Type names glue two ideas together: `IncidentSlack`, `DigestEmail` | [Bridge](#bridge) | Split the two axes into two hierarchies and join them with a field. |
| Millions of objects carry the same data | [Flyweight](#flyweight) | Share one immutable copy per distinct value and keep only the differences per object. |

#### Deciding and reacting
{: #deciding-and-reacting}

| Situation | Pattern | Why |
|---|---|---|
| Several algorithms for one job, picked by config | [Strategy](#strategy) | Put each algorithm behind one small interface or func, and let config choose. |
| Several parts of the system must react when something changes | [Observer](#observer) | Publish the change. Each part subscribes and decides what it means for it. |
| Every method starts with `switch status` | [State](#state) | Give each status its own type, or table row, so the behavior for each mode lives together. |
| Some calls are only legal in some lifecycle states | [State](#state) | Each state decides what a call means and which state comes next. Illegal calls get a clear error. |
| Operations should wait in a queue and run on a worker | [Command](#command) | Make each operation a value with Execute. The queue and the worker don't need to know what it does. |
| Undo the last operation | [Command](#command) | Each command records what it needs to reverse itself. Also consider [Memento](#memento) if you need to restore a whole object's state rather than reverse one step. |
| Audit or replay every change | [Command](#command) | Commands are values you can log, store and run again. |
| Try several handlers in order; the first that can, does | [Chain of Responsibility](#chain-of-responsibility) | Each handler takes the request or passes it on, and the order is explicit. |
| Fall back across credential sources or auth methods | [Chain of Responsibility](#chain-of-responsibility) | This is how the AWS credential chain and kube-apiserver authentication work. |
| Variants share the order of steps and differ in a few of them | [Template Method](#template-method) | Fix the skeleton once. Let each variant supply its own steps. |
| Callers shouldn't have to deal with pagination or streaming | [Iterator](#iterator) | Hide the paging behind an iterator or generator. Callers just loop. |
| Components call each other in a tangle | [Mediator](#mediator) | They report to one hub, and the hub owns the who-does-what-next logic. |
| Snapshot state before a risky change and roll back if needed | [Memento](#memento) | Save an opaque snapshot, and restore it if the change goes wrong. |
| Add new operations over a fixed set of types | [Visitor](#visitor) | Each operation becomes a visitor. The types only accept it. |
| Users write small rules or filters that must be evaluated | [Interpreter](#interpreter) | Parse them into a tree of nodes that evaluate themselves. Better still, embed CEL or JSONPath. |

### Choosing in a bucket
{: #choosing-in-a-bucket}

Pick the bucket, and its tree narrows it to one pattern in one or two questions. An editable version of all three is in [design-patterns-decision-map.drawio](/images/lld/06-field-guide/design-patterns-decision-map.drawio), which opens in [draw.io](https://app.diagrams.net/).

#### Creating objects
{: #fg-creating-objects}

![Creational decision tree: how many leads to Singleton; which concrete type leads to Factory, Factory Method or Abstract Factory; how it's put together leads to Builder or Prototype](/images/lld/06-field-guide/01-choose-creational-decision-tree.webp)
*Factory, Factory Method and Abstract Factory all answer "which type?". They differ in who decides: the input, the subclass, or the family.*

#### Connecting objects
{: #connecting-objects}

![Decision tree: if the middle object has a different interface, it's an Adapter for one object or a Facade for many; if the same interface and it holds children, Composite; otherwise Decorator if it adds behavior, Proxy if it controls access](/images/lld/06-field-guide/02-choose-structural-decision-tree.webp)
*Two questions sort the five common wrappers. Bridge and Flyweight aren't wrappers, so they sit outside the tree.*

#### Deciding behavior
{: #deciding-behavior}

![Decision tree: how the work is done leads to Strategy or Template Method; what each mode does leads to State; who reacts leads to Observer, Chain or Mediator; when it runs leads to Command](/images/lld/06-field-guide/03-choose-behavioral-decision-tree.webp)
*Four kinds of decision, seven patterns. Interpreter belongs with the specialists: it evaluates a small language users write.*

### Spot it in UML
{: #spot-it-in-uml}

Most patterns leave a recognizable shape in a class diagram or in Go struct definitions, so you can name them in an unfamiliar codebase from the types alone.

#### Implements I and holds one I
{: #implements-i-and-holds-one-i}

Pattern: [Decorator](#decorator), [Proxy](#proxy)

![Class shape: a type implements an interface and also holds one value of that same interface](/images/lld/06-field-guide/04-uml-shape-decorator-proxy.webp){: w="420"}
*Decorator if it always forwards and adds behavior. Proxy if it may answer, refuse or delay. Chain of Responsibility has this shape too, when the field is next and a link may stop.*

#### Implements I and holds many I
{: #implements-i-and-holds-many-i}

Pattern: [Composite](#composite)

![Class shape: a type implements an interface and also holds many values of that same interface](/images/lld/06-field-guide/05-uml-shape-composite.webp){: w="420"}
*The aggregation arrow back to its own interface, with `*`, is the giveaway.*

#### Holds an interface the caller can swap
{: #holds-an-interface-the-caller-can-swap}

Pattern: [Strategy](#strategy)

![Class shape: a context holds an interface and delegates to whichever implementation is plugged in](/images/lld/06-field-guide/06-uml-shape-strategy.webp){: w="420"}
*The context only delegates. The implementations never mention each other.*

#### Same shape, but implementations set the next one
{: #same-shape-but-implementations-set-the-next-one}

Pattern: [State](#state)

![Class shape: like Strategy, but each implementation calls back into the context to set the next one](/images/lld/06-field-guide/07-uml-shape-state.webp){: w="420"}
*The back-arrow from a state to the context is what separates State from Strategy.*

#### Implements your interface, holds a foreign type
{: #implements-your-interface-holds-a-foreign-type}

Pattern: [Adapter](#adapter)

![Class shape: a type implements your interface and holds a different, foreign type](/images/lld/06-field-guide/08-uml-shape-adapter.webp){: w="420"}
*Two different types on either side. If both sides share an interface, it's not an adapter.*

#### Holds several different types, offers fewer methods
{: #holds-several-different-types-offers-fewer-methods}

Pattern: [Facade](#facade)

![Class shape: one type holds several different subsystem types and offers a few high-level methods](/images/lld/06-field-guide/09-uml-shape-facade.webp){: w="420"}
*Callers depend on one type instead of four. The subsystems stay reachable.*

#### A function returns an interface and creates concrete types
{: #a-function-returns-an-interface-and-creates-concrete-types}

Pattern: [Factory](#factory)

![Class shape: a function creates one of several concrete types and returns them as one interface](/images/lld/06-field-guide/10-uml-shape-factory.webp){: w="420"}
*The «create» arrows fan out from one place. Callers see only the interface.*

#### Holds a list of listeners and loops over them
{: #holds-a-list-of-listeners-and-loops-over-them}

Pattern: [Observer](#observer)

![Class shape: a subject holds a list of listeners of one interface and calls each on change](/images/lld/06-field-guide/11-uml-shape-observer.webp){: w="420"}
*The subject points at the interface, never at a concrete subscriber.*

#### Package-level instance behind a once
{: #package-level-instance-behind-a-once}

Pattern: [Singleton](#singleton)

![Class shape: a package-level instance and a once guard, reached through one accessor](/images/lld/06-field-guide/12-uml-shape-singleton.webp){: w="420"}
*In Go there's no static keyword. Underlined members are package-level variables.*

### Where they live in one service
{: #where-they-live-in-one-service}

A control-plane service that provisions and scales compute for customers, with the pattern at each component:

| Where | Pattern | Why it fits there |
|---|---|---|
| API gateway | [Chain of Responsibility](#chain-of-responsibility) | Authenticators tried in order: client certificate, service account token, OIDC. |
| API gateway | [Decorator](#decorator) | Logging, recovery and tracing wrapped around every handler. |
| Handlers | [Builder](#builder) | Turn a request into a validated Spec before anything runs. |
| Handlers → job queue | [Command](#command) | The operation becomes a value that can wait, be retried, audited and undone. |
| Worker | [State](#state) | The engine lifecycle allows only legal transitions. |
| Worker | [Strategy](#strategy) | The scaling policy comes from config and can change at runtime. |
| Catalog client | [Proxy](#proxy) | Caches lookups and dials the backend only on first use. |
| Status feed | [Observer](#observer) | Metering, alerts and the audit log react to status changes independently. |
| Notifier | [Adapter](#adapter) | Slack or PagerDuty behind one Notify call. |
| Site provisioner | [Facade](#facade) | One Provision call over network, compute, DNS and registry, with rollback. |
| Cloud factory | [Abstract Factory](#abstract-factory) | AWS or Azure for the whole site, never mixed. |
| Cloud SDK clients | [Adapter](#adapter) | Each product hides its SDK behind your own interface. |
| main() | [Singleton](#singleton) | One config and one database pool, created once and passed down. |
| main() | [Factory](#factory) | NewStore(kind) picks the storage backend from config. |
| main() | [Bridge](#bridge) | slog.New(handler): the logging API and the output format vary independently. |
| Paged API reads | [Iterator](#iterator) | Callers range over all pods; the pages stay hidden. |

### Lookalikes
{: #lookalikes}

Most wrong picks come from a lookalike with the same shape. Each pair is separated by one question.

| Pair | Ask | If yes | If no |
|---|---|---|---|
| [Factory](#factory) vs [Strategy](#strategy) | Is it choosing what to create, once? | [Factory](#factory): picks what to create | [Strategy](#strategy): picks how to do a job, and can be swapped later |
| [Factory Method](#factory-method) vs [Template Method](#template-method) | Is the step that varies the creation of an object? | [Factory Method](#factory-method): the varying step creates the product | [Template Method](#template-method): the varying steps do work |
| [Abstract Factory](#abstract-factory) vs [Builder](#builder) | Are several different objects made that must match? | [Abstract Factory](#abstract-factory): a matching set, all at once | [Builder](#builder): one complex object, step by step |
| [Prototype](#prototype) vs [Memento](#memento) | Will the copy be used as a new object? | [Prototype](#prototype): the copy becomes a new object | [Memento](#memento): the copy restores the original later |
| [Singleton](#singleton) vs [Flyweight](#flyweight) | Is there exactly one instance of the type? | [Singleton](#singleton): one instance, process-wide | [Flyweight](#flyweight): one shared instance per distinct value |
| [Adapter](#adapter) vs [Facade](#facade) | Does it wrap one object to fit an interface that already exists? | [Adapter](#adapter): one object, existing interface | [Facade](#facade): many objects, a new smaller interface |
| [Adapter](#adapter) vs [Bridge](#bridge) | Are you retrofitting two pieces that already exist? | [Adapter](#adapter): retrofitted after the fact | [Bridge](#bridge): designed up front for two axes |
| [Decorator](#decorator) vs [Proxy](#proxy) | Does it always forward the call and add behavior? | [Decorator](#decorator): always forwards, adds behavior | [Proxy](#proxy): may answer, refuse or delay |
| [Decorator](#decorator) vs [Chain of Responsibility](#chain-of-responsibility) | Does every call reach the wrapped object? | [Decorator](#decorator): always forwards | [Chain of Responsibility](#chain-of-responsibility): a link may handle it and stop |
| [Decorator](#decorator) vs [Composite](#composite) | Does it wrap exactly one object of its interface? | [Decorator](#decorator): wraps one | [Composite](#composite): holds many children |
| [Strategy](#strategy) vs [State](#state) | Does the caller pick the implementation? | [Strategy](#strategy): the caller picks | [State](#state): the states pick the next state |
| [Observer](#observer) vs [Mediator](#mediator) | Does each listener decide for itself how to react? | [Observer](#observer): listeners decide | [Mediator](#mediator): the hub decides who does what |
| [Observer](#observer) vs [Chain of Responsibility](#chain-of-responsibility) | Should every receiver get it? | [Observer](#observer): everyone hears it | [Chain of Responsibility](#chain-of-responsibility): the first able handler takes it |
| [Command](#command) vs [Strategy](#strategy) | Is it what to do, to run later or undo? | [Command](#command): what to do, possibly later | [Strategy](#strategy): how to do it, now |
| [Facade](#facade) vs [Mediator](#mediator) | Do calls only flow inward, from callers to subsystems? | [Facade](#facade): callers call it | [Mediator](#mediator): components report to it, and it calls them |

### Rules of thumb
{: #rules-of-thumb}

- **Name the decision before the pattern.** Ask which bucket question you're answering: who creates it, what sits in the middle, or who decides. The pattern follows from the decision.
- **Wait for the second case.** A pattern with one implementation is indirection without a payoff. Add the factory, strategy or adapter when the second type, policy or vendor shows up.
- **In Go, reach for the smallest shape.** A func before a one-method interface, a small interface before a type hierarchy, and define interfaces where they're used. Most Go patterns are a few lines.
- **Concurrency changes the details.** Singletons need `sync.Once`, observers need a policy for slow subscribers, strategies swapped at runtime need atomic access, and state machines need one owner or a lock.

### Cheat sheet
{: #cheat-sheet}

"Try first" is what to write before reaching for the pattern; reach for it only when that stops being enough.

| Pattern | Question it answers | Try first | Go shape |
|---|---|---|---|
| [Singleton](#singleton) | How many? | Create it once in `main` and pass it down | `var getConfig = sync.OnceValue(loadConfig)` |
| [Factory](#factory) | Which type? | The constructor, until a second implementation exists | `func NewStore(kind, target string) (Store, error)` |
| [Factory Method](#factory-method) | Which type, per variant? | A constructor `func` field, which is the whole pattern in Go | `type Exporter struct{ newSink func() Sink }` |
| [Abstract Factory](#abstract-factory) | Which family? | A simple factory, if there's only one kind of product | `type CloudFactory interface{ NewVM(size string) VM; NewBucket(name string) Bucket }` |
| [Builder](#builder) | How assembled? | A struct literal, keyword arguments or functional options | `pod.New("api").Image("nginx:1.27").Port(8080).Build()` |
| [Prototype](#prototype) | Copy an existing one? | Building a fresh one, if that's cheap | `p := cached.DeepCopy(); p.Labels["team"] = "infra"` |
| [Adapter](#adapter) | The calls don't fit? | Changing one side, if you own both | `type SlackNotifier struct{ client *slack.Client } // implements Notifier` |
| [Decorator](#decorator) | Add behavior around calls? | Inline code, if one call site needs it | `func Logging(next http.Handler) http.Handler` |
| [Proxy](#proxy) | Should the call get through? | A direct call, if it's cheap, local and unrestricted | `type CachingCatalog struct{ real Catalog; cache map[string]Item } // implements Catalog` |
| [Facade](#facade) | Too many parts to learn? | Leaving the sequence with its one caller until it repeats | `func (p *SiteProvisioner) Provision(ctx context.Context, s Spec) (Site, error)` |
| [Composite](#composite) | One thing or many? | A slice and a loop, if nesting is one level deep | `type Group struct{ children []Resource } // implements Resource` |
| [Bridge](#bridge) | Two things varying at once? | One hierarchy, until the second axis really varies | `type Incident struct{ sender Sender }` |
| [Flyweight](#flyweight) | Millions of near-identical objects? | Plain values, until a profile shows the duplication | `h := unique.Make(labels) // Go 1.23+` |
| [Strategy](#strategy) | How should the work be done? | An `if`, for two options that never change | `type ScalePolicy interface{ Desired(cur int, m Metrics) int }` |
| [Observer](#observer) | Who needs to know? | A direct call, for one reaction you own | `unsubscribe := feed.Subscribe(func(e Event) { ... })` |
| [State](#state) | What does this call mean right now? | An enum and a `switch`, for a few states with little logic | `func (Running) Stop(i *Instance) error { i.setState(Stopping{}); return nil }` |
| [Command](#command) | When, and how many times? | A plain call or closure, if it runs once, now | `type Command interface{ Execute(ctx context.Context) error; Undo(ctx context.Context) error }` |
| [Chain of Responsibility](#chain-of-responsibility) | Who handles this? | An `if`/`else`, for two fixed checks | `type Chain []Authenticator // tries each in order until one says ok` |
| [Template Method](#template-method) | Same steps, different details? | Steps as `func` parameters or a small interface | `sort.Sort(byCPU(pods)) // you supply Len, Less, Swap` |
| [Iterator](#iterator) | Walk it without knowing its insides? | Returning a slice, if it's small and in memory | `for pod, err := range AllPods(ctx, api) { ... } // iter.Seq2` |
| [Mediator](#mediator) | Who talks to whom? | Direct calls, for a few components with a simple flow | `func (p *Pipeline) Notify(from, event string)` |
| [Memento](#memento) | Can I roll back? | Re-reading the source of truth, such as the database or API server | `snap := cfg.Save(); /* risky change */; cfg.Restore(snap)` |
| [Visitor](#visitor) | New operations over the same types? | A type switch, if types change more often than operations | `ast.Walk(v, file) // calls v.Visit(node) for every node` |
| [Interpreter](#interpreter) | Do users write little rules? | Embedding CEL, JSONPath or Rego, or a config struct | `sel, _ := labels.Parse("app=api,tier!=db"); sel.Matches(labels.Set(pod.Labels))` |

### Prototype and Interpreter
{: #prototype-and-interpreter}

The two patterns not covered earlier.

#### Prototype
{: #prototype}

**Copy an existing one.** Create new objects by cloning a configured original, then change only what differs. Use it when configuring from scratch is costly, or when you must not mutate a shared original, such as an object from a Kubernetes informer cache.

```go
p := cached.DeepCopy() // edit a copy, never the object other cache readers share
p.Labels["team"] = "infra"
```

Also `http.Request.Clone(ctx)` and `tls.Config.Clone()`; in Python, `copy.deepcopy` or `dataclasses.replace`. The trap is a shallow copy, which shares maps, slices and pointers with the original.

#### Interpreter
{: #interpreter}

**Evaluate a little language.** Represent a small language as a tree of objects that evaluate themselves. Regular expressions, `text/template`, Kubernetes label selectors, CEL and PromQL are all interpreters.

```go
sel, _ := labels.Parse("app=api,tier!=db") // parse once into a tree
sel.Matches(labels.Set(pod.Labels))        // evaluate it per object
```

Before building one, embed an existing language (CEL, JSONPath, Rego) or use a config struct.

### Check your understanding
{: #fg-check-your-understanding}

{% include quiz.html id="lld-field-guide" %}
