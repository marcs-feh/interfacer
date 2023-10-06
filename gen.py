from interfacer import interface

interface('Allocator', {
    '@include': ['<cstddef>'],
    'alloc: void*': ['nbytes: usize'],
    'alloc_undef: void*': ['nbytes: usize'],
    'realloc: void*': ['p: void*', 'nbytes: usize'],
    'free: void': ['p: void*'],
    'free_all: void': [],
    'has_address: bool': ['p: void*']
}).generate_file('examples/allocator.hpp')

interface('List', {
    '@template':['T: typename'],
    'at: T&':['idx: int'],
    'len: int':['@const']
}).generate_file('examples/list.hpp')
