from dataclasses import dataclass

@dataclass
class Declaration:
    name: str
    dtype: str

    def expand(self):
        return f'{self.dtype} {self.name}'

@dataclass
class Method:
    decl: Declaration
    args: list[Declaration]
    const: bool = False

    def func_ptr_decl(self) -> str:
        name, dtype = self.decl.name, self.decl.dtype
        args = ', '.join((map(lambda a: a.expand(), self.args)))
        if len(args) == 0:
            args = 'void'
        decl = f'{dtype} (*{name})({args});'
        return decl

    def vtable_entries(self): return

    def implement(self): return

@dataclass
class Interface:
    name: str
    methods: list[Method]
    template: list[Declaration]|None= None

    def generate_struct(self) -> str:
        msrc = list(map(lambda m: m.func_ptr_decl(), self.methods))
        struct = [f'struct {self.name} {{']
        vtable = ['struct VTable {'] + msrc + ['};']
        members = ['void * _impl;', 'const VTable * const _vtable;']

        # TODO: Constructor
        src = '\n'.join(struct + vtable + members + ['};'])
        return src

def extract_decl(s: str) -> Declaration:
    p = s.split(':', 1)
    assert len(p) == 2, f"Invalid Declaration string '{s}'"

    d = Declaration(
        name=p[0].strip(),
        dtype=p[1].strip(),
    )

    return d

def extract_decls(l: list[str]) -> list[Declaration]:
    args = list(map(extract_decl, l))
    return args

def extract_template(d: dict) -> list[Declaration] | None:
    try:
        args = d.pop('@template')
        return extract_decls(args)
    except KeyError:
        return None

# TODO CONST

def extract_methods(d: dict) -> list[Method]:
    methods = []
    for decl_str, args in d.items():
        methods.append(Method(
            decl=extract_decl(decl_str),
            args=extract_decls(args),
        ))
    d.clear()
    return methods

def extract_interface(name, d) -> Interface:
    t = extract_template(d)
    m = extract_methods(d)
    iface = Interface(
        name=name,
        template=t,
        methods=m,
    )

    return iface

def interface(d: dict) -> list[Interface]:
    ifaces = []
    for iname, idata in d.items():
        ifaces.append(extract_interface(iname, idata))
    return ifaces

i = interface({
    'Allocator':{
        'alloc:void*':['nbytes:int'],
        'free:void':['ptr:void*'],
        'realloc:void*':['ptr:void*', 'new_size:int'],
        'free_all:void':[],
    },
    'List':{
        '@template':['T:typename'],
        'at:T&':['idx:int'],
        'len:int':[],
    }
})

from pprint import pprint
# pprint(i)

print(i[0].generate_struct())
