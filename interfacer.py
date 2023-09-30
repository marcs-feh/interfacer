import yaml
from pprint import pprint
from textwrap import indent
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

@dataclass
class Interface:
    name: str
    procedures: list[Procedure]

def expand_small_dict(d: dict) -> tuple[str, str]:
    k, v = list(d.items())[0]
    return k, v

def proc_from_dict(name: str, proc: list) -> Procedure:
    ret_type = proc[0]
    params = [ Param(dtype='void*', identifier=IMPL_ID) ]
    for p in proc[1:]:
        id, dt = expand_small_dict(p)
        params.append(Param(identifier=id, dtype=dt))
    return Procedure(ret_type=ret_type, params=params, identifier=name)

def interface_from_yaml(data: str) -> list[Interface]:
    d = yaml.safe_load(data)
    ifaces = []
    for name, methods in d.items():
        procs = [proc_from_dict(n,l) for n,l in methods.items()]
        ifaces.append(Interface(name=name, procedures=procs))
    return ifaces

def cdecl_from_param(p: Param):
    return f'{p.dtype} {p.identifier}'

def func_ptr_from_proc(proc: Procedure):
    params = ', '.join(map(cdecl_from_param, proc.params))
    return f'{proc.ret_type} (*{proc.identifier})({params});'

def iface_method_from_proc(proc: Procedure):
    params = ', '.join(map(cdecl_from_param, proc.params))
    plist = ', '.join(map(lambda p: p.identifier, proc.params))
    func = (
       f'{proc.ret_type} {proc.identifier}({params}){{\n'
       f'    return {VTBL_ID}->{proc.identifier}({plist});\n'
       f'}}'
    )
    return func

def impl_method_from_proc(proc: Procedure):
    params = ', '.join(map(cdecl_from_param, proc.params[1:]))
    # plist = ', '.join(map(lambda p: p.identifier, proc.params[1:]))
    func = (
       f'{proc.ret_type} {proc.identifier}({params});'
    )
    return func

def implementation_methods(iface: Interface):
    methods = '\n'.join(map(impl_method_from_proc, iface.procedures))
    return methods

def vtable_entry_from_proc(proc: Procedure):
    params = ', '.join(map(cdecl_from_param, proc.params))
    args = ', '.join(map(lambda p: p.identifier, proc.params[1:]))
    func = (
       f'.{proc.identifier} = []({params}) -> {proc.ret_type}{{\n'
       f'    auto obj = reinterpret_cast<T*>({IMPL_ID});\n'
       f'    return obj->{proc.identifier}({args});\n'
       f'}}'
    )
    return func


def vtable_type_from_procs(procs: list[Procedure]):
    vtbl_decls = []
    for method in procs:
        ptr = func_ptr_from_proc(method);
        vtbl_decls.append(ptr)

    vtbl_decls = indent("\n".join(vtbl_decls), 4*' ')

    out = (
        f'struct VTable{{\n'
        f'{vtbl_decls}\n'
        f'}};'
    )
    return out

def generate_sugar(methods: list):
    out = '\n'.join(map(iface_method_from_proc, methods))
    return out

def struct_from_interface(iface: Interface):
    procs = iface.procedures
    vtable_decl = indent(vtable_type_from_procs(procs), 4*' ')
    methods_sugar = indent(generate_sugar(procs), 4*' ')

    out = (
        f'struct {iface.name}{{\n'
        f'{vtable_decl}\n\n'
        f'    const VTable *const {VTBL_ID} = nullptr;\n'
        f'    void* {IMPL_ID} = nullptr;\n\n'
        f'{methods_sugar}\n'
        f'}};'
    )
    return out

def vtable_from_iterface(iface: Interface):
    funcs = indent(',\n'.join(map(vtable_entry_from_proc, iface.procedures)), 4*' ');
    out = (
        f'template<typename T>\n'
        f'constexpr {iface.name}::VTable {iface.name}_vtable = {{\n'
        f'{funcs}\n'
        f'}};\n'
    )
    return out

def generate_interface(iface: Interface):
    struct = struct_from_interface(iface) 
    vtbl = vtable_from_iterface(iface)

    helper = (
        f'template<typename T>\n'
        f'{iface.name} make_{iface.name.lower()}(T* impl){{\n'
        f'	constexpr auto vt = {iface.name}_vtable<T>;\n'
        f'	return {iface.name}{{\n'
        f'		.impl = impl,\n'
        f'		.vtbl = &vt,\n'
        f'	}};\n'
        f'}}\n'
    )

    implement = f'/* IMPLEMENTATION\n{implementation_methods(iface)}\n*/'

    full_impl = '\n'.join([struct, vtbl, helper, implement])
    return full_impl
    

def main():
    data = ''

    with open('allocator.yaml', 'r') as f:
        data = f.read()

    # pprint(al)
    ifaces = interface_from_yaml(data)
    # pprint(yaml.safe_load(data))

    for iface in ifaces:
        code = generate_interface(iface)
        print(code)
    # pprint(interface_from_yaml(data))


if __name__ == '__main__': main()
