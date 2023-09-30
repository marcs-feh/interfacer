from typing import Any
from yaml import SafeLoader, load
from pprint import pprint
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
    func = f'''{proc.ret_type} {proc.identifier}({params}){{
        return {VTBL_ID}->{proc.identifier}({plist});
        }}'''
    return func

def parse_to_proc(method: dict) -> Procedure:
    for name, proc in method.items():
        ret_type = proc[0]
        params = [ Param(dtype='void*', identifier=IMPL_ID) ]
        for p in proc[1:]:
            params.append(Param(identifier=p[0], dtype=p[1]))
        return Procedure(ret_type=ret_type, params=params, identifier=name)
    return Procedure('','',[])

def generate_vtable(methods: list):
    vtbl_decls = []
    for method in methods:
        ptr = func_ptr_decl(method);
        vtbl_decls.append(ptr)

    vtbl_decls = "\n".join(vtbl_decls)

    out = f'''
struct VTable{{
{vtbl_decls}
}};
'''
    return out

def generate_struct(name: str, methods: list):
    vtable = generate_vtable(methods)
    methods_sugar = []
    for method in methods:
         methods_sugar.append(func_sugar_impl(method))
    methods_sugar = '\n'.join(methods_sugar)


    out = f'''
struct {name}{{
{vtable}

const VTable *const {VTBL_ID};
void* {IMPL_ID};

{methods_sugar}

/* SYNTAX SUGAR */

}};
'''
    return out

def main():
    data = ''

    with open('allocator.yaml', 'r') as f:
        data = f.read()

    al = load(data, SafeLoader)
    # pprint(al)

    code = generate_struct('Allocator', al['Allocator'])
    print(code)


if __name__ == '__main__': main()
