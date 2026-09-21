# Python & Django Interview Preparation — Q&A with Code Examples

Format: **Question** → **Answer** (with code examples where applicable)

---

## 1. PROJECT EXPLANATION IN DEPTH

**Q: Explain the AI Analysis Service project in depth.**

A: 
- **Purpose**: A FastAPI-based service for intelligent PDF analysis and interactive Q&A.
- **Key Features**:
  - Real-time PDF summarization via WebSocket endpoints
  - RAG (Retrieval-Augmented Generation) for Q&A over documents
  - Multi-user chat with Kafka message persistence
  - Embeddings cached locally (Chroma) and synced to S3
  - Asynchronous processing for LLM calls and PDF parsing
- **Tech Stack**: FastAPI, LangChain, OpenAI embeddings, Chroma vector DB, Kafka, S3, Redis caching
- **Flow**: 
  1. Summarize endpoint: Client uploads PDF → system generates summary via LLM chain → cached in DB/Redis
  2. Chat endpoint: Client asks question → system retrieves relevant doc passages (Chroma) → LLM generates answer → message produced to Kafka → consumed and sent back to client over WebSocket
- **Data Flow**: PDFs → local storage → embeddings (Chroma) → S3 backup; Summaries → DB, and Q&A pairs → Kafka topics
- **Scalability**: Async/await for concurrent WebSockets; Kafka for decoupling producers/consumers; S3 for distributed embedding persistence.

---

## 2. DECORATORS IN PYTHON

**Q: What are decorators? What is their use case and provide an example.**

A: 
A decorator is a function that modifies or enhances another function or class without permanently changing its source code. It wraps a function, allowing code to run before and after the wrapped function executes.

**Use Cases**:
- Logging and monitoring function calls
- Authentication/authorization checks
- Caching results (memoization)
- Timing function execution
- Validating inputs
- Registering routes or handlers (as in Flask/FastAPI)

**Basic Example**:
```python
def my_decorator(func):
    """Decorator that prints before and after function execution."""
    def wrapper(*args, **kwargs):
        print(f"Before calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"After calling {func.__name__}")
        return result
    return wrapper

@my_decorator
def greet(name):
    return f"Hello, {name}!"

# Output:
# Before calling greet
# Hello, Alice!
# After calling greet
greet("Alice")
```

**Real Project Use Case** (from this project):
```python
# Timing decorator for monitoring LLM response times
import time
from functools import wraps

def timing_decorator(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"Function {func.__name__} took {elapsed:.2f}s")
        return result
    return async_wrapper

@timing_decorator
async def get_answer(query, product_id):
    # LLM call here
    pass
```

**Decorator with Arguments**:
```python
def log_level_decorator(level="INFO"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(f"[{level}] Executing {func.__name__}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

@log_level_decorator(level="DEBUG")
def critical_function():
    return "Done"
```

---

## 3. MULTIPLE INHERITANCE IN PYTHON

**Q: Does Python support multiple inheritance? What is multiple inheritance?**

A: 
**Yes**, Python supports multiple inheritance. A class can inherit from more than one parent class.

**Definition**: Multiple inheritance is when a child class inherits attributes and methods from two or more parent classes.

**Syntax**:
```python
class Parent1:
    def method1(self):
        return "Parent1 method"

class Parent2:
    def method2(self):
        return "Parent2 method"

class Child(Parent1, Parent2):
    pass

child = Child()
print(child.method1())  # Parent1 method
print(child.method2())  # Parent2 method
```

---

## 4. METHOD RESOLUTION ORDER (MRO) IN PYTHON

**Q: In Python multiple inheritance, what is the order of inheritance? Example with three classes sharing a common function.**

A: 
Python uses **C3 Linearization (MRO — Method Resolution Order)** to determine which parent class method is called. It follows a **Left-to-Right, Depth-First** approach but ensures each class appears before its parents.

**Example**:
```python
class A:
    def common_function(self):
        return "A's version"

class B(A):
    def common_function(self):
        return "B's version"

class C(A):
    def common_function(self):
        return "C's version"

class D(B, C):  # Multiple inheritance: B first, then C
    pass

d = D()
print(d.common_function())  # Output: "B's version"
print(D.mro())  # Output: [<class 'D'>, <class 'B'>, <class 'C'>, <class 'A'>, <class 'object'>]
```

**Explanation**:
- `D` inherits from `B` first, then `C`. Both `B` and `C` inherit from `A`.
- MRO: `D → B → C → A → object`
- When `d.common_function()` is called, Python searches in order: `D`, `B` (found!), so returns "B's version".
- `B`'s definition is used because `B` appears first in the inheritance list of `D`.

**Diamond Problem Example**:
```python
class Animal:
    def speak(self):
        return "Sound"

class Dog(Animal):
    def speak(self):
        return "Woof"

class Cat(Animal):
    def speak(self):
        return "Meow"

class DogCat(Dog, Cat):  # Diamond: inherits from Dog and Cat
    pass

dc = DogCat()
print(dc.speak())  # Output: "Woof" (Dog's method is called)
print(DogCat.mro())  # [DogCat, Dog, Cat, Animal, object]
```

---

## 5. STATIC METHODS VS CLASS METHODS

**Q: What is a static method and what is a class method? What's the difference?**

A: 

| Feature | Static Method | Class Method |
|---------|---------------|--------------|
| Decorator | `@staticmethod` | `@classmethod` |
| First Parameter | None | `cls` (class itself) |
| Access Instance? | No | No (but accesses class) |
| Access Class Variables? | No (unless called via class) | Yes |
| Use Case | Utility functions, math ops | Factory methods, alternative constructors |

**Static Method Example**:
```python
class MathUtils:
    @staticmethod
    def add(a, b):
        return a + b

# Called on class or instance; doesn't receive self or cls
result = MathUtils.add(5, 3)  # 8
print(result)
```

**Class Method Example**:
```python
class Counter:
    count = 0
    
    def __init__(self, name):
        self.name = name
        Counter.count += 1
    
    @classmethod
    def get_count(cls):
        return cls.count
    
    @classmethod
    def create_default(cls):  # Factory method
        return cls("Default")

c1 = Counter("Alice")
c2 = Counter("Bob")
print(Counter.get_count())  # 2

c3 = Counter.create_default()
print(c3.name)  # "Default"
```

**Comparison in One Example**:
```python
class Example:
    class_var = "shared"
    
    def __init__(self, value):
        self.value = value
    
    def instance_method(self):
        return f"Instance: {self.value}"
    
    @staticmethod
    def static_method(x):
        return x * 2  # No access to instance or class
    
    @classmethod
    def class_method(cls):
        return f"Class: {cls.class_var}"

e = Example(10)
print(e.instance_method())  # Instance: 10
print(Example.static_method(5))  # 10
print(Example.class_method())  # Class: shared
```

---

## 6. CACHING AND PERFORMANCE

**Q: What is caching and how does it make a process or program fast?**

A: 
**Caching** is storing the results of expensive operations so they can be reused without recomputation.

**How It Makes Programs Fast**:
1. **Reduces Computation**: Avoids repeating the same calculations.
2. **Faster Access**: Cached data is typically in faster storage (RAM vs disk/network).
3. **Reduces I/O**: Eliminates repeated database or API calls.
4. **Lower Latency**: Immediate retrieval instead of computation time.

**Example in the Project**:
```python
# Without caching: Every query triggers a DB lookup + LLM call
async def get_answer_no_cache(query, product_id):
    db_summary = get_db_summary(product_id)  # DB call
    if not db_summary:
        pdf_path = get_pdf_file(product_id)
        db_summary = await get_summary(pdf_path)  # Expensive LLM call
        insert_db_summary(product_id, db_summary)
    return db_summary

# With caching: Use Redis to cache summaries in memory
from utils.redis_utils import get_redis_summary, update_redis_summary

async def get_answer_with_cache(query, product_id):
    # Try Redis cache first (fast, in-memory)
    cached_summary = get_redis_summary(product_id)
    if cached_summary:
        return cached_summary  # Instant return
    
    # Fall back to DB
    db_summary = get_db_summary(product_id)
    if db_summary:
        update_redis_summary(product_id, db_summary)  # Cache it
        return db_summary
    
    # Only compute if necessary
    pdf_path = get_pdf_file(product_id)
    summary = await get_summary(pdf_path)
    insert_db_summary(product_id, summary)
    update_redis_summary(product_id, summary)
    return summary
```

**Caching Levels**:
- **L1 Cache**: In-memory (Redis) — fastest
- **L2 Cache**: Database — medium speed
- **L3 Cache**: Disk/S3 — slowest but persistent

---

## 7. SHALLOW COPY VS DEEP COPY

**Q: Difference between shallow copy and deep copy? Examples where each is suitable.**

A: 

| Aspect | Shallow Copy | Deep Copy |
|--------|--------------|-----------|
| Behavior | Copies only top-level object; nested objects are referenced | Recursively copies all nested objects |
| Memory | Less memory use | More memory use |
| Changes | Changes to nested objects affect both copies | Changes don't affect original |

**Shallow Copy Example**:
```python
import copy

original = {
    "name": "Alice",
    "skills": ["Python", "JavaScript"]
}

shallow = copy.copy(original)

# Modify top level
shallow["name"] = "Bob"
print(original["name"])  # "Alice" (not affected)

# Modify nested object
shallow["skills"].append("Go")
print(original["skills"])  # ["Python", "JavaScript", "Go"] (affected!)
```

**Deep Copy Example**:
```python
import copy

original = {
    "name": "Alice",
    "skills": ["Python", "JavaScript"]
}

deep = copy.deepcopy(original)

# Modify nested object
deep["skills"].append("Go")
print(original["skills"])  # ["Python", "JavaScript"] (not affected!)
```

**When to Use Each**:
- **Shallow Copy**: 
  - Simple flat data structures (lists/dicts with primitives only)
  - Performance-critical code where you don't modify nested objects
  - Example: `my_list = list1.copy()` for a list of integers
  
- **Deep Copy**:
  - Complex nested structures (lists of dicts, objects containing objects)
  - When you need complete independence from the original
  - Example: Configuration objects, document models

**Project Example** (copying PDF metadata):
```python
original_metadata = {
    "product_id": 123,
    "embeddings": {
        "model": "openai",
        "version": "1.0"
    }
}

# Shallow copy — don't do this if you'll modify embeddings config
shallow_copy = original_metadata.copy()
shallow_copy["embeddings"]["version"] = "2.0"
print(original_metadata["embeddings"]["version"])  # "2.0" (oops!)

# Deep copy — safe
import copy
deep_copy = copy.deepcopy(original_metadata)
deep_copy["embeddings"]["version"] = "2.0"
print(original_metadata["embeddings"]["version"])  # "1.0" (correct!)
```

---

## 8. ASYNCHRONOUS VS SYNCHRONOUS APIs

**Q: How will you choose between asynchronous and synchronous APIs?**

A: 

| Aspect | Synchronous | Asynchronous |
|--------|------------|----------------|
| Blocking | Blocks until response | Non-blocking; returns immediately |
| Concurrency | Sequential; handles one request at a time | Concurrent; handles many requests |
| Complexity | Simpler, easier to debug | Complex state management |
| Latency | Stalls if I/O is slow | Minimal stalls |
| Resource Use | Needs threads per request (memory heavy) | Single thread, event loop (lightweight) |

**Choose Synchronous When**:
- Simple CRUD operations with low concurrency
- CPU-bound operations (not I/O-bound)
- Legacy systems or team expertise constraint

**Choose Asynchronous When**:
- High concurrency (many simultaneous users)
- I/O-heavy (network, DB, file operations)
- Real-time features (WebSocket, streaming)
- Cost-efficiency (fewer resources needed)

**Project Context** (this project is async-heavy):
```python
# Synchronous (slow) — blocks on I/O
def get_summary_sync(filepath):
    pdf_data = read_pdf(filepath)  # Blocks
    summary = call_llm(pdf_data)   # Blocks
    return summary

# If 10 users request summaries simultaneously, each must wait in sequence.
# Total time: 10 * 5s (if each takes 5s) = 50s

# Asynchronous (fast) — doesn't block
async def get_summary_async(filepath):
    pdf_data = await read_pdf_async(filepath)  # Yields control
    summary = await call_llm_async(pdf_data)    # Yields control
    return summary

# If 10 users request summaries simultaneously, all run concurrently.
# Total time: ~5s (only the slowest individual request)
```

**FastAPI Implementation** (from this project):
```python
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/recieve-msg/{user_id}/{product_id}")
async def websocket_endpoint(user_id, product_id, websocket: WebSocket):
    await websocket.accept()
    
    # Non-blocking; can handle thousands of concurrent connections
    for msg in consume_message(TOPIC_NAME, user_id, product_id):
        await websocket.send_json(eval(msg))
    
    while True:
        question = await websocket.receive_text()  # Non-blocking wait
        ai_response = await produce_and_generate_answer(question, user_id, product_id)
        await websocket.send_json(ai_response)
```

---

## 9. CLASSES AND OBJECTS (BASIC PYTHON)

**Q: What is a class and what is an object? How are they correlated?**

A: 
- **Class**: A blueprint or template defining structure and behavior. It's a type.
- **Object**: An instance of a class; a concrete entity with actual data.

**Correlation**:
- A class defines *what* objects will do.
- An object is a *realization* of a class with specific values.

**Analogy**: Class = Recipe; Object = Prepared Dish

**Example**:
```python
# Class definition (blueprint)
class Dog:
    def __init__(self, name, breed):
        self.name = name
        self.breed = breed
    
    def bark(self):
        return f"{self.name} says Woof!"

# Objects (instances)
dog1 = Dog("Buddy", "Golden Retriever")
dog2 = Dog("Max", "Bulldog")

# Each object has its own data but shares methods
print(dog1.bark())  # Buddy says Woof!
print(dog2.bark())  # Max says Woof!

# They are different objects (different memory locations)
print(dog1 == dog2)  # False
print(type(dog1))    # <class 'Dog'>
```

---

## 10. PYTHON OOP VS TRADITIONAL OOP (JAVA)

**Q: What differs in Python OOP vs traditional OOP like Java? What changes do you notice?**

A: 

| Feature | Python | Java |
|---------|--------|------|
| **Access Control** | Convention-based (`_private`, `__private`) | Strict (`private`, `protected`, `public`) |
| **Methods** | Can add/remove dynamically; no signature binding | Strict method signatures |
| **Typing** | Duck typing; dynamic | Static typing; compile-time checks |
| **Inheritance** | Multiple and dynamic | Single (multiple interfaces) |
| **Properties** | `@property` decorator for getters | Getter/setter methods |
| **Constructor** | `__init__` method | `ClassName()` constructor |
| **Attributes** | No declaration needed; added at runtime | Must declare type upfront |

**Key Differences**:

1. **Access Control** (Python more permissive):
```python
# Python
class Example:
    def __init__(self):
        self.public = "anyone"
        self._protected = "by convention"
        self.__private = "name-mangled"

# Java
public class Example {
    public String publicVar;
    protected String protectedVar;
    private String privateVar;
}
```

2. **Dynamic vs Static**:
```python
# Python: Can add methods dynamically
class Dynamic:
    pass

obj = Dynamic()
obj.new_method = lambda x: x * 2  # Add method at runtime!
print(obj.new_method(5))  # 10

# Java: Requires recompilation and type checks at compile-time
```

3. **Duck Typing vs Type Safety**:
```python
# Python: No type checks; if it quacks, it's a duck
def make_sound(animal):
    print(animal.sound())  # Works if object has sound() method

class Dog:
    def sound(self):
        return "Woof"

class Cat:
    def sound(self):
        return "Meow"

make_sound(Dog())  # Works
make_sound(Cat())  # Works (different type, but same interface)

# Java: Requires explicit interface/inheritance
interface Animal {
    String sound();
}
```

---

## 11. PROTECTED VARIABLES IN PYTHON

**Q: Declare a protected variable in Python.**

A: 
Protected variables are prefixed with a **single underscore** (`_`). They signal "for internal use" but are not enforced by Python.

**Syntax**:
```python
class MyClass:
    def __init__(self):
        self._protected_var = "I'm protected by convention"
```

**Example**:
```python
class BankAccount:
    def __init__(self, balance):
        self._balance = balance  # Protected (by convention)
    
    def withdraw(self, amount):
        if amount <= self._balance:
            self._balance -= amount
            return f"Withdrew {amount}"
        return "Insufficient funds"
    
    def get_balance(self):
        return self._balance

account = BankAccount(1000)
print(account.get_balance())  # 1000
print(account.withdraw(200))  # Withdrew 200

# You CAN access it directly, but it's discouraged
print(account._balance)  # 800 (works, but not recommended)
```

---

## 12. PROTECTED VARIABLE CODE EXAMPLE

**Q: Declare a class A with a protected variable `test` (value 8). Create an object. Can we change this protected variable?**

A: 
**Yes, you can change a protected variable**, but it's not recommended. Python doesn't enforce true protection.

**Code**:
```python
class A:
    def __init__(self):
        self._test = 8  # Protected variable
    
    def get_test(self):
        return self._test
    
    def set_test(self, value):
        self._test = value

# Create object
obj = A()
print(obj.get_test())  # 8

# Method 1: Use provided setter (recommended)
obj.set_test(15)
print(obj.get_test())  # 15

# Method 2: Direct access (possible but not recommended)
obj._test = 20
print(obj.get_test())  # 20

# Python allows this because it's convention-based, not enforced
```

**Truly Private Variable** (Name Mangling):
```python
class A:
    def __init__(self):
        self.__test = 8  # Truly private (name-mangled)
    
    def get_test(self):
        return self.__test

obj = A()
print(obj.get_test())  # 8

# Attempt direct access
try:
    print(obj.__test)  # AttributeError
except AttributeError:
    print("Cannot access __test directly")

# But it's still accessible via name mangling
print(obj._A__test)  # 8 (Python renames to _ClassName__varname)
```

---

## 13. ARGS VS KWARGS

**Q: What's the difference between *args and **kwargs? When do you use each?**

A: 

| Feature | *args | **kwargs |
|---------|-------|----------|
| Syntax | `*args` | `**kwargs` |
| Accepts | Multiple positional arguments | Multiple keyword arguments |
| Type | Tuple | Dictionary |
| Naming | Must be `args` | Can be any name after `**` |
| Use Case | Variable number of positional args | Named/optional parameters |

**args Example**:
```python
def sum_numbers(*args):
    """Accept any number of positional arguments."""
    total = 0
    for num in args:
        total += num
    return total

print(sum_numbers(1, 2, 3))  # 6
print(sum_numbers(1, 2, 3, 4, 5))  # 15
print(sum_numbers())  # 0
```

****kwargs Example**:
```python
def print_info(**kwargs):
    """Accept any number of keyword arguments."""
    for key, value in kwargs.items():
        print(f"{key}: {value}")

print_info(name="Alice", age=25, city="NYC")
# Output:
# name: Alice
# age: 25
# city: NYC
```

**Combined Example**:
```python
def flexible_function(required, *args, **kwargs):
    print(f"Required: {required}")
    print(f"Args (tuple): {args}")
    print(f"Kwargs (dict): {kwargs}")

flexible_function(1, 2, 3, 4, name="Alice", age=25)
# Output:
# Required: 1
# Args (tuple): (2, 3, 4)
# Kwargs (dict): {'name': 'Alice', 'age': 25}
```

**Project Example** (Flask/FastAPI-like routing):
```python
def route_handler(endpoint, *args, **kwargs):
    """Register a route with flexible parameters."""
    print(f"Endpoint: {endpoint}")
    print(f"Args: {args}")
    print(f"Kwargs: {kwargs}")

route_handler("/api/user", "GET", "POST", auth=True, cache=False)
# Output:
# Endpoint: /api/user
# Args: ('GET', 'POST')
# Kwargs: {'auth': True, 'cache': False}
```

---

## 14. CPYTHON

**Q: What is CPython?**

A: 
**CPython** is the default, reference implementation of Python written in C. It's the most widely used Python interpreter.

**Key Points**:
- Compiles Python source code to bytecode (`.pyc` files)
- Bytecode is executed by the CPython virtual machine (PVM)
- Manages memory through reference counting and garbage collection
- The "default Python" when you install from python.org

**How It Works**:
```
Python Code (.py) 
    ↓
Lexer/Parser (C) 
    ↓
AST (Abstract Syntax Tree) 
    ↓
Compiler (C) 
    ↓
Bytecode (.pyc) 
    ↓
CPython VM 
    ↓
Machine Code (executed by CPU)
```

**Other Python Implementations**:
- **Jython**: Python on Java Virtual Machine
- **IronPython**: Python on .NET
- **PyPy**: Written in Python; JIT compiler for speed
- **MicroPython**: Minimal Python for embedded systems

**Why CPython**:
- Most compatible
- Largest ecosystem
- Best performance/compatibility trade-off

---

## 15. METACLASSES IN DJANGO MODELS

**Q: What is a metaclass inside a Django model?**

A: 
A **metaclass** is a "class of a class" — it defines how a class behaves. In Django models, the **`Meta` inner class** configures model-level options (not to be confused with Python metaclasses like `type`).

**Purpose**:
- Configure database table name
- Set ordering, permissions
- Add indexes
- Define verbose names

**Syntax**:
```python
from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    published_date = models.DateField()
    
    class Meta:
        db_table = 'books'  # Custom table name
        ordering = ['-published_date']  # Default ordering
        verbose_name = 'Book'
        verbose_name_plural = 'Books'
        indexes = [
            models.Index(fields=['author', '-published_date']),
        ]
```

**Common Meta Options**:
```python
class Article(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey("User", on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'articles'  # Custom table name
        ordering = ['-created_at']  # Default ordering (- means descending)
        permissions = [('can_publish', 'Can publish articles')]
        verbose_name_plural = 'Articles'
        unique_together = [['title', 'author']]  # Unique constraint
        indexes = [
            models.Index(fields=['author']),
            models.Index(fields=['title'], name='title_idx'),
        ]
```

**Python Metaclass (different concept)**:
```python
# This is a Python metaclass, not Django Meta
class SingletonMeta(type):
    """Metaclass to create singleton classes."""
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Database(metaclass=SingletonMeta):
    def __init__(self):
        self.connection = "Connected to DB"

db1 = Database()
db2 = Database()
print(db1 is db2)  # True (same instance)
```

---

## 16. INDEXES IN DJANGO MODELS

**Q: How do you define indexes in a Django model?**

A: 
Indexes improve query performance by creating database indexes on specific fields.

**Using `class Meta`**:
```python
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),  # Single-field index
            models.Index(fields=['category', 'price']),  # Composite index
            models.Index(fields=['-created_at'], name='created_idx'),  # Named, descending
        ]
```

**Using `db_index=True` on Field**:
```python
class User(models.Model):
    email = models.EmailField(unique=True, db_index=True)  # Single-field index
    username = models.CharField(max_length=50, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Index Types**:
```python
class Order(models.Model):
    customer = models.ForeignKey('User', on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    
    class Meta:
        indexes = [
            models.Index(fields=['customer'], name='customer_idx'),
            models.Index(fields=['status', 'created_date'], name='status_date_idx'),
            models.Index(fields=['-total'], name='total_desc_idx'),  # Descending
        ]
```

---

## 17. RELATED_NAME IN DJANGO

**Q: What is `related_name` in a Django model?**

A: 
`related_name` defines the name for the reverse relation from the related model back to the model that defines the relation.

**Purpose**:
- Allows accessing related objects from the foreign key side
- Makes queries more readable and intuitive
- Without it, Django creates a default relation name (`modelname_set`)

**Basic Example**:
```python
class Author(models.Model):
    name = models.CharField(max_length=100)

class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')

# Reverse query using related_name
author = Author.objects.get(id=1)
books_by_author = author.books.all()  # Uses related_name='books'

# Without related_name, it would be:
# books_by_author = author.book_set.all()  # Default Django naming
```

**Real Project Example**:
```python
class User(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    message_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

# Query all messages from a user
user = User.objects.get(id=1)
user_messages = user.messages.all()  # Instead of user.chatmessage_set.all()

# Or query from the other side
msg = ChatMessage.objects.get(id=1)
msg_user = msg.user  # Direct access to the author
```

**With Reverse Relationships**:
```python
class Product(models.Model):
    name = models.CharField(max_length=100)

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField()
    comment = models.TextField()

# Access reviews from a product
product = Product.objects.get(id=1)
all_reviews = product.reviews.all()  # Readable!
avg_rating = product.reviews.aggregate(Avg('rating'))
```

---

## 18. MANAGERS IN DJANGO MODELS

**Q: What is a Manager in a Django model context?**

A: 
A **Manager** is an interface through which database query operations are provided to Django models. It's the object you use to query the database.

**Default Manager**: Every model has a default manager called `objects`.

```python
class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey('Author', on_delete=models.CASCADE)
    is_published = models.BooleanField(default=False)

# Default manager: objects
Book.objects.all()  # Uses the default manager
Book.objects.filter(is_published=True)
Book.objects.get(id=1)
```

**Custom Manager**:
```python
class PublishedBookManager(models.Manager):
    """Custom manager to fetch only published books."""
    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)

class Book(models.Model):
    title = models.CharField(max_length=100)
    is_published = models.BooleanField(default=False)
    
    objects = models.Manager()  # Default manager
    published_books = PublishedBookManager()  # Custom manager

# Usage
all_books = Book.objects.all()  # All books
published = Book.published_books.all()  # Only published
```

**Custom QuerySet + Manager**:
```python
class BookQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)
    
    def by_author(self, author_name):
        return self.filter(author__name=author_name)

class BookManager(models.Manager):
    def get_queryset(self):
        return BookQuerySet(self.model, using=self._db)
    
    def published(self):
        return self.get_queryset().published()
    
    def by_author(self, author_name):
        return self.get_queryset().by_author(author_name)

class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey('Author', on_delete=models.CASCADE)
    is_published = models.BooleanField(default=False)
    
    objects = BookManager()

# Usage
Book.objects.published()  # Calls custom manager method
Book.objects.by_author('J.K. Rowling')
Book.objects.published().by_author('J.K. Rowling')  # Chainable!
```

**Real Project Example** (for AI summaries):
```python
class SummaryManager(models.Manager):
    def get_or_create_summary(self, product_id):
        """Get existing summary or mark for regeneration."""
        try:
            summary = self.get(product_id=product_id)
            if summary.needs_regeneration():
                summary.mark_for_regeneration()
            return summary
        except self.model.DoesNotExist:
            return None
    
    def active_summaries(self):
        """Get summaries that are not stale."""
        return self.filter(is_active=True, regenerate=False)

class Summary(models.Model):
    product_id = models.IntegerField(unique=True)
    summary_text = models.TextField()
    is_active = models.BooleanField(default=True)
    regenerate = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = SummaryManager()
    
    def needs_regeneration(self):
        return self.regenerate

# Usage
summary = Summary.objects.get_or_create_summary(product_id=123)
active = Summary.objects.active_summaries()
```

---

## Quick Reference Table

| Concept | Definition | Example |
|---------|-----------|---------|
| **Decorator** | Wraps function to modify behavior | `@my_decorator` |
| **MRO** | Order of parent class resolution | D → B → C → A → object |
| **Static Method** | No access to instance/class | `@staticmethod` |
| **Class Method** | Access to class via `cls` | `@classmethod` |
| **Caching** | Store results for reuse | Redis, DB cache |
| **Shallow Copy** | Top-level only | `list.copy()` |
| **Deep Copy** | Recursive copy | `copy.deepcopy()` |
| **Protected Var** | Convention-based | `self._var = 5` |
| **args** | Multiple positional | `def f(*args)` |
| **kwargs** | Multiple keyword | `def f(**kwargs)` |
| **Related Name** | Reverse relation label | `related_name='books'` |
| **Manager** | DB query interface | `Book.objects.all()` |

---

Generated for interview preparation. Review, practice, and adapt answers based on the interviewer's depth questions.
