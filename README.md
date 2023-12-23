# Interfacer: Create Interfaces using THICC Pointers in C++

Tired of `virtual` and its gross hidden `__vtable` pointer? Do you want
something more akin to Rust's `as &dyn <trait>`? Need more control of your
vtables? Are you tired of using filthy inheritance to achieve your goals? This
is probably for you. Interfacer is a simple code generation tool that creates
"fat pointer" interfaces from python dicts. It also generates a helper
`as_interfacename` function to make it easy to integrate it to your code, but
you still can specify your own vtables just fine.

![Different Approaches for Dynamic Dispatch](info.png)

## Installation

There's no installation. Copy the `interfacer.py` file to your project and use
it as you wish.

## Usage

> NOTE: Requires C++14 or later, ideally you should use C++17 or later as it
> can take advantage of better `constexpr`

### Simple concrete type (Allocator)

Also look at the `gen.py` file.

```python
from interfacer import interface

# Helper function that creates an Interface object
interface('Allocator', {
    # Use the @include directive to add files
    '@include': ['<cstddef>', 'types.hpp'],
    # All declarations follow ID:TYPE form, spaces are ignored
    'alloc: void*': ['nbytes: usize'],
    'alloc_undef: void*': ['nbytes: usize'],
    'realloc: void*': ['p: void*', 'nbytes: usize'],
    'free: void': ['p: void*'],
    # Empty list means no args
    'free_all: void': [],
    # To mark a procedure as const, just drop a @const in its argument list
    'has_address: bool': ['p: void*', '@const']
}).generate_file('examples/allocator.hpp', guard='pragma')
# When generating to a file, you can choose the header guard style: ifdef, pragma or none(default)
```

### Generic container type (List)
```python
import interfacer as i
interface('List', {
    # Pass template args in the @template field
    '@template':['T: typename'],
    'at: T&':['idx: int'],
    'len: int':['@const']
}).generate_file('examples/list.hpp')
```

## Limitations

Because this is mainly a hack you can expect a bunch of edge cases, as
Interfacer does not parse C++ code, and never will as doing so is insanely
complicated and you're better off just using a better language.

Interfaces are just plain function pointer tables, you cannot add
procedure overloading to interfaces, as that would require Interfacer using its
own name mangling rules that would create even *more* problems. You **can**
however, choose a specific overload of a function to be in the vtable, you can
just copy-paste the wrapper and do a specialization for your datatype where you
change the desired vtable fields.

> NOTE: Vtables must be `static`, as they will live through the whole program,
> you could make some heap-allocated (potentially mutable) vtable if you're
> insane tho.

