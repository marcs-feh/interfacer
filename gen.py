from interfacer import interface

interface('Allocator', {
    '@include': ['<cstddef>', 'types.hpp'],
    'alloc: void*': ['nbytes: usize'],
    'alloc_undef: void*': ['nbytes: usize'],
    'realloc: void*': ['p: void*', 'nbytes: usize'],
    'free: void': ['p: void*'],
    'free_all: void': [],
    'has_address: bool': ['p: void*']
}).generate_file('examples/allocator.hpp', indent_src=False, guard='ifdef')

interface('List', {
    '@template':['T: typename'],
    'at: T&':['idx: int'],
    'len: int':['@const']
}).generate_file('examples/list.hpp', indent_src=True, tabsize=2)
# A tabsize of None means use regular tabs instead of spaces
