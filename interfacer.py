#!/usr/bin/env python

import yaml
from datetime import datetime, timezone
from sys import argv
from hashlib import md5
from textwrap import indent
from dataclasses import dataclass

VTBL_ID = 'vtbl'
IMPL_ID = 'impl'

assert len(VTBL_ID) > 2
IMPL_TYPE = IMPL_ID[0].upper() + IMPL_ID[1:].lower()

# Header guard types
HG_NONE   = 'none'
HG_IFDEF  = 'ifdef'
HG_PRAGMA = 'pragma'

HELP = (
    'Usage: interfacer [OPTIONS] [FILE]\n'
    '    -out:OUT        Write contents to file named OUT\n'
    '    -guard:TYPE     Header guard type, TYPE can be none, ifdef or pragma\n'
    '    -timestamp      Include comment with time and date\n'
)

options = {
    'out': None,
    'guard': HG_NONE,
    'timestamp': False,
}

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
       f'  return {VTBL_ID}->{proc.identifier}({plist});\n'
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

    vtbl_decls = indent("\n".join(vtbl_decls), '  ')

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
    vtable_decl = indent(vtable_type_from_procs(procs), '  ')
    methods_sugar = indent(generate_sugar(procs), '  ')
    template_info = template_info_from_iface(iface)
    if len(template_info) > 0:
        template_info = f'template<{template_info}>\n'

    out = (
        f'{template_info}'
        f'struct {iface.name}{{\n'
        f'{vtable_decl}\n\n'
        f'  void* {IMPL_ID} = nullptr;\n'
        f'  const VTable *const {VTBL_ID} = nullptr;\n\n'
        f'{methods_sugar}\n\n'
        f'  constexpr operator bool(){{\n'
        f'    return (impl != nullptr) && (vtbl != nullptr);\n'
        f'  }}\n'
        f'}};'
    )
    return out

def vtable_from_interface(iface: Interface):
    funcs = indent(',\n'.join(map(vtable_entry_from_proc, iface.procedures)), '  ');

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
        f'INTERFACER_CONSTEXPR {dependent_type}\n'
        f'{iface.name}{template_args}::VTable {iface.name}_vtable = {{\n'
        f'{funcs}\n'
        f'}};\n'
    )
    return out

def generate_interface(iface: Interface, guard = HG_NONE, use_timestamp = False):
    struct = struct_from_interface(iface)
    vtbl = vtable_from_interface(iface)
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

    moment = datetime.now(timezone.utc).strftime("UTC %Y-%m-%d %H:%M")
    stamp = f'/* Generated by Interfacer at {moment} */\n' if use_timestamp else ''

    prelude = (
        f'{stamp}'
        '#if __cplusplus >= 201703L\n'
        '#define INTERFACER_CONSTEXPR constexpr\n'
        '#else\n'
        '#define INTERFACER_CONSTEXPR\n'
        '#endif\n'
    )

    epilogue = '#undef INTERFACER_CONSTEXPR'

    helper = (
        f'template<{template_decl}>\n'
        f'{iface.name}{iface_template_args} make_{iface.name.lower()}({IMPL_TYPE}* impl){{\n'
        f'  static INTERFACER_CONSTEXPR const auto vt = {iface.name}_vtable{vtable_template_args};\n'
        f'  return {iface.name}{iface_template_args}{{\n'
        f'    .impl = impl,\n'
        f'    .vtbl = &vt,\n'
        f'  }};\n'
        f'}}\n'
    )

    implement = f'/* IMPLEMENTATION\n{implementation_methods(iface)}\n*/'

    full_impl = '\n'.join([prelude, struct, vtbl, helper, implement, epilogue])

    if guard == HG_NONE:
        pass
    elif guard == HG_IFDEF:
        hg = '_include_' + md5(full_impl.encode('utf-8')).digest().hex()
        full_impl = (
            f'#ifndef {hg}\n'
            f'#define {hg}\n\n'
            f'{full_impl}\n\n'
            f'#endif /* header guard */\n'
        )
    elif guard == HG_PRAGMA:
        full_impl = f'#pragma once\n\n{full_impl}'
    else:
        print_fatal(f'Unknown guard option: {guard}')

    return full_impl

def cli_parse(args):
  flags = []
  regular = []
  is_flag = lambda s: s[0] == '-' and len(s) > 1

  def split_flag(s : str):
    p = s.find(':')
    if p > -1:
      return (s[1:p], s[p+1:])
    else:
      return (s[1:], True)

  for arg in args:
    if is_flag(arg):
      k, v = split_flag(arg)
      flags.append((k,v))
    else:
      regular.append(arg)
  return flags, regular

def print_fatal(*args):
    for a in args: print(a)
    exit(1)

def main():
    if len(argv) < 2:
        print_fatal(HELP)

    flags, files = cli_parse(argv[1:])

    if len(files) < 1:
        print_fatal(HELP)

    yaml_data = ''
    for file in files:
        with open(file, 'r') as f:
            yaml_data += f.read() + '\n\n'

    for flag in flags:
        k, v = flag
        ok = k in options
        if ok:
            options[k] = v
        else:
            print_fatal(f'Unknown flag: {k}')

    ifaces = interface_from_yaml(yaml_data)

    if options['out'] is None:
        for i in ifaces:
            print(generate_interface(i, options['guard'], options['timestamp']))
    else:
        all_impl = '\n'.join([generate_interface(i, options['guard'], options['timestamp']) for i in ifaces])
        with open(options['out'], 'w') as f:
            f.write(all_impl)

if __name__ == '__main__': main()
