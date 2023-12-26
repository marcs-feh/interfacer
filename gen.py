from interfacer import interface

interface('Allocator', {
    '@include': ['<cstddef>', 'types.hpp'],
    '@namespace': ['mem'],
    'alloc: void*': ['nbytes: usize'],
    'alloc_undef: void*': ['nbytes: usize'],
    'realloc: void*': ['p: void*', 'nbytes: usize'],
    'free: void': ['p: void*'],
    'free_all: void': [],
    'has_address: bool': ['p: void*'],
}).generate_file('examples/allocator.hpp', indent_src=True, guard='custom', custom_str='_include_writer_hpp_')

interface('List', {
    '@template':['T: typename'],
    'at: T&':['idx: int'],
    'len: int':['@const'],
}).generate_file('examples/list.hpp', indent_src=True)
# A tabsize of None means use regular tabs instead of spaces
