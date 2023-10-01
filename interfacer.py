import yaml
from textwrap import indent
from dataclasses import dataclass

VTBL_ID = 'vtbl'
IMPL_ID = 'impl'

assert len(VTBL_ID) > 2
IMPL_TYPE = IMPL_ID[0].upper() + IMPL_ID[1:].lower()

@dataclass
class Param:
    dtype: str
    identifier: str

@dataclass
class Procedure:
    identifier: str
    ret_type: str
    params: list[Param]
    const: bool

@dataclass
class Template:
    params: list[Param]

@dataclass
class Interface:
    name: str
    template_info: Template|None
    procedures: list[Procedure]


def expand_small_dict(d: dict) -> tuple[str, str]:
    k, v = list(d.items())[0]
    return k, v

def proc_from_dict(name: str, proc: list) -> Procedure:
    constness = False
    if name[0] == '+':
        name = name[1:]
        constness = True

    ret_type = proc[0]
    params = [ Param(dtype=f'void {const_str(constness)}*', identifier=IMPL_ID) ]
    for p in proc[1:]:
        id, dt = expand_small_dict(p)
        params.append(Param(identifier=id, dtype=dt))

    out = Procedure(ret_type=ret_type, params=params, identifier=name, const=constness)
    return out

def param_from_dict(d: dict) -> Param:
    id, dt = expand_small_dict(d)
    return Param(identifier=id, dtype=dt)

def interface_from_yaml(data: str) -> list[Interface]:
    d = yaml.safe_load(data)

    ifaces = []
    for name, methods in d.items():
        try:
            template_params = [param_from_dict(p) for p in  (methods.pop('template'))]
            itemplate = Template(params=template_params)
        except KeyError:
            itemplate = None
        procs = [proc_from_dict(n,l) for n,l in methods.items()]
        ifaces.append(Interface(name=name, procedures=procs, template_info=itemplate))
    return ifaces

def cdecl_from_param(p: Param):
    return f'{p.dtype} {p.identifier}'

def func_ptr_from_proc(proc: Procedure):
    params = ', '.join(map(cdecl_from_param, proc.params))
    return f'{proc.ret_type} (*{proc.identifier})({params});'

def iface_method_from_proc(proc: Procedure):
    params = ', '.join(map(cdecl_from_param, proc.params[1:]))
    plist = ', '.join(map(lambda p: p.identifier, proc.params))
    func = (
       f'{proc.ret_type} {proc.identifier}({params}){" const " if proc.const else ""}{{\n'
       f'\treturn {VTBL_ID}->{proc.identifier}({plist});\n'
       f'}}'
    )
    return func

def const_str(p: bool) -> str:
    return 'const' * int(p)

def impl_method_from_proc(proc: Procedure):
    params = ', '.join(map(cdecl_from_param, proc.params[1:]))
    func = (
       f'{proc.ret_type} {proc.identifier}({params}){const_str(proc.const)};'
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
       f'    auto obj = reinterpret_cast<{const_str(proc.const)} {IMPL_TYPE}*>({IMPL_ID});\n'
       f'    return obj->{proc.identifier}({args});\n'
       f'}}'
    )
    return func


def vtable_type_from_procs(procs: list[Procedure]):
    vtbl_decls = []
    for method in procs:
        ptr = func_ptr_from_proc(method);
        vtbl_decls.append(ptr)

    vtbl_decls = indent("\n".join(vtbl_decls), '\t')

    out = (
        f'struct VTable{{\n'
        f'{vtbl_decls}\n'
        f'}};'
    )
    return out

def generate_sugar(methods: list):
    out = '\n'.join(map(iface_method_from_proc, methods))
    return out

def template_info_from_iface(iface: Interface) -> str:
    if iface.template_info is None: return ''
    p = ', '.join(map(cdecl_from_param, iface.template_info.params))
    return p

def struct_from_interface(iface: Interface):
    procs = iface.procedures
    vtable_decl = indent(vtable_type_from_procs(procs), '\t')
    methods_sugar = indent(generate_sugar(procs), '\t')
    template_info = template_info_from_iface(iface)
    if len(template_info) > 0:
        template_info = f'template<{template_info}>\n'

    out = (
        f'{template_info}'
        f'struct {iface.name}{{\n'
        f'{vtable_decl}\n\n'
        f'\tvoid* {IMPL_ID} = nullptr;\n'
        f'\tconst VTable *const {VTBL_ID} = nullptr;\n\n'
        f'{methods_sugar}\n'
        f'}};'
    )
    return out

def vtable_from_iterface(iface: Interface):
    funcs = indent(',\n'.join(map(vtable_entry_from_proc, iface.procedures)), '\t');

    template_decl = f'{template_info_from_iface(iface)}'
    if len(template_decl) > 0: template_decl += ', '
    template_decl += f'typename {IMPL_TYPE}'

    template_args = ''
    dependent_type = ''
    if iface.template_info is not None:
        template_args = ', '.join(map(lambda p: p.identifier, iface.template_info.params))
        template_args = f'<{template_args}>'
        dependent_type = 'typename'

    out = (
        f'template<{template_decl}>\n'
        f'constexpr {dependent_type}\n'
        f'{iface.name}{template_args}::VTable {iface.name}_vtable = {{\n'
        f'{funcs}\n'
        f'}};\n'
    )
    return out

def generate_interface(iface: Interface):
    struct = struct_from_interface(iface) 
    vtbl = vtable_from_iterface(iface)
    info_args = ''
    if iface.template_info is not None:
        info_args = ', '.join(map(lambda p: p.identifier, iface.template_info.params))

    template_decl = f'{template_info_from_iface(iface)}'
    if len(template_decl) > 0: template_decl += ', '
    template_decl += f'typename {IMPL_TYPE}'

    iface_template_args = ''
    if len(info_args) > 0:
        iface_template_args = f'<{info_args}>'

    vtable_template_args = info_args 
    if len(info_args) > 0:
        vtable_template_args = f'<{info_args}, {IMPL_TYPE}>'
    else:
        vtable_template_args = f'<{IMPL_TYPE}>'

    helper = (
        f'template<{template_decl}>\n'
        f'{iface.name}{iface_template_args} make_{iface.name.lower()}({IMPL_TYPE}* impl){{\n'
        f'static constexpr auto vt = {iface.name}_vtable{vtable_template_args};\n'
        f'\treturn {iface.name}{iface_template_args}{{\n'
        f'\t\t.impl = impl,\n'
        f'\t\t.vtbl = &vt,\n'
        f'\t}};\n'
        f'}}\n'
    )

    implement = f'/* IMPLEMENTATION\n{implementation_methods(iface)}\n*/'

    full_impl = '\n'.join([struct, vtbl, helper, implement])
    return full_impl
    

def main():
    data = ''

    with open('list.yaml', 'r') as f:
        data = f.read()

    # pprint(al)
    ifaces = interface_from_yaml(data)
    # pprint(yaml.safe_load(data))

    for iface in ifaces:
        code = generate_interface(iface)
        print(code)
    # pprint(interface_from_yaml(data))


if __name__ == '__main__': main()
