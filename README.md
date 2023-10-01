# Interfacer: Create Interfaces using THICC Pointers in C++

Tired of `virtual` and its gross hidden `__vtable` pointer? Do you want
something more akin to Rust's `as &dyn <trait>`? Need more control of you
vtables? This is probably for you. Interfacer is a simple code generation tool
that creates "fat pointer" interfaces from YAML files. It also generates a
helper to make it easy to integrate it to your code, but you still can specify
your own vtables just fine.

![](info.png)


## Usage

> NOTE: Requires C++14 or later, ideally you should use C++17 or later as it
> can take advantage of better `constexpr`

### Simple concrete type (Allocator)

```yaml
# Interface name
Allocator:
  # List of Methods, first element of each method must be its return type,
  # followed by key-value pairs of identifier and type
  - alloc:
    - void*
    - nbytes: int
  
  - free:
    - void
    - ptr: void*
  
  # Start a method name with + to mark it const
  - +full:
    - bool
```

## Limitations


