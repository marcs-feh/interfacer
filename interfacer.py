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
        args = ', '.join(map(lambda a: a.expand(),
                              [Declaration('impl', 'void *')] + self.args))
        if len(args) == 0:
            args = 'void'
        decl = f'{dtype} (*{name})({args});'
        return decl

    def vtable_lambda_impl(self) -> str:
        name, dtype = self.decl.name, self.decl.dtype
        args_decl = ', '.join(map(lambda a: a.expand(),
                              [Declaration('impl', 'void *')] + self.args))
        args_use = ', '.join(map(lambda a: a.name, self.args))

        # TODO: const on reinterpret_cast
        lamb = [f'.{name} = []({args_decl}) -> {dtype} {{',
                'auto obj = reinterpret_cast<_Impl*>(impl);',
                f'return obj->{name}({args_use});',
                '}']
        return '\n'.join(lamb)

    def implementation(self) -> str:
        name, dtype = self.decl.name, self.decl.dtype
        args_decl = ', '.join(map(lambda a: a.expand(), self.args))
        args_use = ', '.join(['_impl'] + list(map(lambda a: a.name, self.args)))

        impl = [f'{dtype} {name}({args_decl}){{',
                f'return _vtable->{name}({args_use});',
                '}']

        return '\n'.join(impl)


@dataclass
class Interface:
    name: str
    methods: list[Method]
    template: list[Declaration]|None = None
    includes: list[str]|None = None

    def generate_vtable_helper(self) -> str:
        methods = ',\n'.join(map(lambda m: m.vtable_lambda_impl(), self.methods))
        helper = ['template<typename _Impl>',
                  'static constexpr',
                  f'VTable vtable_helper = {{',
                  methods,
                  '};']

        return '\n'.join(helper)

    def generate_struct(self) -> str:
        func_ptrs = list(map(lambda m: m.func_ptr_decl(), self.methods))
        struct = [f'struct {self.name} {{']
        templ_decl = []
        if self.template is not None:
            templ_decl = ', '.join(map(lambda d: d.expand(), self.template))
            templ_decl = [f'template<{templ_decl}>']

        vtable = ['struct VTable {'] + func_ptrs + ['};']
        m_data = ['void * _impl;', 'const VTable * const _vtable;']
        m_funcs = list(map(lambda m: m.implementation(), self.methods))
        vtable_helper = self.generate_vtable_helper()

        # TODO: Constructor
        src = '\n'.join(templ_decl + struct + vtable + m_data + m_funcs + [vtable_helper] + ['};'])

        return src


    def generate_func_helper(self):
        ret_type = f'{self.name}'
        templ_decl = []
        dependant_type = ''
        if self.template is not None:
            templ_decl += list(map(lambda d: d.expand(), self.template))
            templ_usage = ', '.join(map(lambda d: d.name, self.template))
            ret_type += f'<{templ_usage}>'
            dependant_type = 'template '

        templ_decl.append('typename _Impl')
        templ_decl = ', '.join(templ_decl)

        helper = [f'template<{templ_decl}>',
                  f'auto make_{self.name.lower()}(void* impl){{',
                  f'static constexpr const auto vt = {ret_type}::{dependant_type}vtable_helper<_Impl>;',
                  f'return {ret_type}{{',
                  '._vtable = &vt,',
                  '._impl = impl,',
                  '};', '}']

        return '\n'.join(helper)

    def generate(self) -> str:
        code = [self.generate_struct(), self.generate_func_helper()]
        sys_include = lambda s: (s[0] == '<') and (s[-1] == '>')
        if self.includes is not None:
            incs = '\n'.join(map(
                lambda i:f'#include {i}' if sys_include(i) else f'#include "{i}"',
                self.includes
            ))
            code.insert(0, incs + '\n')

        return '\n'.join(code)

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

def extract_includes(d: dict) -> list[str] | None:
    try:
        includes = list( map(lambda s: s.strip(), d.pop('@include')))

        return includes
    except KeyError:
        return

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
    i = extract_includes(d)
    m = extract_methods(d)
    iface = Interface(
        name=name,
        template=t,
        methods=m,
        includes=i,
    )

    return iface

def interfaces(d: dict) -> list[Interface]:
    ifaces = []
    for iname, idata in d.items():
        ifaces.append(extract_interface(iname, idata))
    return ifaces

# TODO: Hoist all interface's #includes to global scope?

i = interfaces({
    'Allocator':{
        '@include':['types.hpp'],
        'alloc:void*':['nbytes:int'],
        'free:void':['ptr:void*'],
        'realloc:void*':['ptr:void*', 'new_size:int'],
        'free_all:void':[],
    },
    'List':{
        '@template':['T:typename'],
        'at:T&':['idx:int'],
        'len:int':[],
    },
    'NArray':{
        '@template':['T:typename', 'N:int'],
        'at:T&':['idx:int'],
        'len:int':[],
    }
})

print(i[0].generate())
print(i[1].generate())
