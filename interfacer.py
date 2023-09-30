from yaml import SafeLoader, load
from textwrap import dedent,indent
from dataclasses import dataclass

VTBL_ID = 'vtbl'
IMPL_ID = 'impl'

@dataclass
class Param:
    dtype: str
    identifier: str

@dataclass
class Procedure:
    identifier: str
    ret_type: str
    params: list[Param]

def param_to_decl(p: Param):
    return f'{p.dtype} {p.identifier}'

def func_ptr_decl(method: dict):
    proc = parse_to_proc(method)
    params = ', '.join(map(param_to_decl, proc.params))
    return f'{proc.ret_type} (*{proc.identifier})({params});'

def func_sugar_impl(method: dict):
    proc = parse_to_proc(method)
    params = ', '.join(map(param_to_decl, proc.params))
    plist = ', '.join(map(lambda p: p.identifier, proc.params))
    func = (
       f'{proc.ret_type} {proc.identifier}({params}){{\n'
       f'    return {VTBL_ID}->{proc.identifier}({plist});\n'
       f'}}'
    )
    return func

def parse_to_proc(method: dict) -> Procedure:
    for name, proc in method.items():
        ret_type = proc[0]
        params = [ Param(dtype='void*', identifier=IMPL_ID) ]
        for p in proc[1:]:
            params.append(Param(identifier=p[0], dtype=p[1]))
        return Procedure(ret_type=ret_type, params=params, identifier=name)
    return Procedure('','',[])

def vtbl_impl(method: dict):
    proc = parse_to_proc(method)
    params = ', '.join(map(param_to_decl, proc.params))
    args = ', '.join(map(lambda p: p.identifier, proc.params[1:]))
    func = (
       f'.{proc.identifier} = []({params}) -> {proc.ret_type}{{\n'
       f'    auto obj = reinterpret_cast<T*>({IMPL_ID});\n'
       f'    return obj->{proc.identifier}({args});\n'
       f'}}'
    )
    return func


def generate_vtable_type(methods: list):
    vtbl_decls = []
    for method in methods:
        ptr = func_ptr_decl(method);
        vtbl_decls.append(ptr)

    vtbl_decls = indent("\n".join(vtbl_decls), 4*' ')

    out = (
        f'struct VTable{{\n'
        f'{vtbl_decls}\n'
        f'}};'
    )
    return out

def generate_sugar(methods: list):
    out = '\n'.join(map(func_sugar_impl, methods))
    return out

def generate_struct(name: str, methods: list):
    vtable = indent(generate_vtable_type(methods), 4*' ')
    methods_sugar = indent(generate_sugar(methods), 4*' ')

    out = (
        f'struct {name}{{\n'
        f'{vtable}\n\n'
        f'    const VTable *const {VTBL_ID} = nullptr;\n'
        f'    void* {IMPL_ID} = nullptr;\n\n'
        f'{methods_sugar}\n'
        f'{name}(){{\n'
        f'    tem\n'
        f'}}\n'
        f'}};'
    )
    return out

def generate_vtable(name: str, methods: list):
    funcs = indent(',\n'.join(map(vtbl_impl, methods)), 4*' ');
    out = (
        f'template<typename T>\n'
        f'constexpr {name}::VTable {name}_vtable = {{\n'
        f'{funcs}\n'
        f'}};\n'
    )
    return out

def generate_interface(name: str, methods: list):
    struct = generate_struct(name, methods) 
    vtbl = generate_vtable(name, methods)

    helper = (
        f'template<typename T>\n'
        f'{name} make_{name.lower()}(T* impl){{\n'
        f'	constexpr auto vt = {name}_vtable<T>;\n'
        f'	return {name}{{\n'
        f'		.impl = impl,\n'
        f'		.vtbl = &vt,\n'
        f'	}};\n'
        f'}}\n'
    )

    return '\n'.join([struct, vtbl, helper])
    

def main():
    data = ''

    with open('allocator.yaml', 'r') as f:
        data = f.read()

    al = load(data, SafeLoader)
    # pprint(al)

    code = generate_interface('Allocator', al['Allocator'])
    print(code)


if __name__ == '__main__': main()
