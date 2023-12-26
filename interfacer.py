# See end of file for licensing information.

import datetime
import uuid
from dataclasses import dataclass
from copy import deepcopy
from sys import stderr
from textwrap import dedent, indent

VERSION = 'dev'

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
                             [Declaration('impl', f'{"const " if self.const else ""}void *')] + self.args))
        if len(args) == 0:
            args = 'void'
        decl = f'{dtype} (*{name})({args});'
        return decl

    def vtable_lambda_impl(self) -> str:
        name, dtype = self.decl.name, self.decl.dtype
        args_decl = ', '.join(map(lambda a: a.expand(),
                                  [Declaration('impl', f'{"const " if self.const else ""}void *')] + self.args))
        args_use = ', '.join(map(lambda a: a.name, self.args))

        lamb = [f'.{name} = []({args_decl}) -> {dtype} {{',
                f'auto obj = reinterpret_cast<{"const " if self.const else ""}_Impl *>(impl);',
                f'return obj->{name}({args_use});',
                '}']
        return '\n'.join(lamb)

    def implementation(self) -> str:
        name, dtype = self.decl.name, self.decl.dtype
        args_decl = ', '.join(map(lambda a: a.expand(), self.args))
        args_use = ', '.join(['_impl'] + list(map(lambda a: a.name, self.args)))

        impl = [f'{dtype} {name}({args_decl}){" const " if self.const else ""}{{',
                f'return _vtable->{name}({args_use});',
                '}']

        return '\n'.join(impl)


@dataclass
class Interface:
    name: str
    methods: list[Method]
    template: list[Declaration]|None = None
    includes: list[str]|None = None
    aliases: list[Declaration]|None = None
    namespace: str|None = None

    def generate_vtable_helper(self) -> str:
        methods = ',\n'.join(map(lambda m: m.vtable_lambda_impl(), self.methods))
        helper = ['template<typename _Impl>',
                  'static constexpr',
                  f'VTable vtable_helper = {{',
                  methods,
                  '};']

        return '\n'.join(helper)

    def generate_namespace(self) -> tuple[str, str]:
        left, right = '', ''
        if self.namespace is not None:
            ids = self.namespace
            left = [f'namespace {i} {{' for i in ids]
            right = '}' * len(left)
        left = '\n'.join(left)
        return left, right


    def generate_struct(self) -> str:
        func_ptrs = list(map(lambda m: m.func_ptr_decl(), self.methods))
        struct = [f'struct {self.name} {{']
        templ_decl = []
        if self.template is not None:
            templ_decl = ', '.join(map(lambda d: d.expand(), self.template))
            templ_decl = [f'template<{templ_decl}>']

        vtable = ['struct VTable {'] + func_ptrs + ['};']
        m_data = ['void * _impl;', 'const VTable * _vtable;']
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
                  f'auto as_{self.name.lower()}(_Impl* impl){{',
                  f'static constexpr const auto vt = {ret_type}::{dependant_type}vtable_helper<_Impl>;',
                  f'return {ret_type}{{',
                  '._impl = impl,',
                  '._vtable = &vt,',
                  '};', '}']

        return '\n'.join(helper)

    def generate(self, guard_type: str = 'none', custom_str: str = '', indent_src: bool = True, tabsize: int|None=None) -> str:
        src = self.generate_struct().splitlines()
        src += self.generate_func_helper().splitlines()

        if indent_src:
            src = indent_source_code(src, tabsize)

        ns0, ns1 = self.generate_namespace()
        src.insert(0, ns0)
        src.append(ns1)

        sys_include = lambda s: (s[0] == '<') and (s[-1] == '>')
        if self.includes is not None:
            incs = '\n'.join(map(
                lambda i:f'#include {i}' if sys_include(i) else f'#include "{i}"',
                self.includes
            ))
            src.insert(0, incs + '\n')

        src = add_header_guard(src, guard_type, custom_str)

        now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        comment = f'/* Code generated by interfacer.py at UTC {now} */\n'

        src.insert(0, comment)
        src.append('')

        return '\n'.join(src)

    def generate_file(self, outfile: str,guard: str = 'none', custom_str:str = '', indent_src: bool = True, tabsize: int|None = None):
        src = self.generate(guard_type=guard, indent_src=indent_src, custom_str=custom_str, tabsize=tabsize)

        with open(outfile, 'w') as f:
            n = f.write(src)
            stderr.write(f'Wrote {n}B to {outfile}\n')

def add_header_guard(src: list[str], mode: str, custom_str: str) -> list[str]:
    MODES = ('pragma', 'ifdef', 'none', 'custom')
    assert mode in MODES, f'Invalid mode: {mode}'

    if mode == 'pragma':
        return ['#pragma once\n\n'] + src
    elif mode == 'ifdef':
        g = uuid.uuid4().hex
        src = [ f'#ifndef _include_{g}_', f'#define _include_{g}_\n' ] + src + [f'#endif /* Header Guard */']
    elif mode == 'custom':
        src = [ f'#ifndef {custom_str}', f'#define {custom_str}\n' ] + src + [f'#endif /* Header Guard */']

    return src

def indent_source_code(src: list[str], tabsize:int|None = None) -> list[str]:
    tab = '\t'
    if tabsize is not None:
        tab = ' ' * tabsize

    level = 0
    for i, line in enumerate(src):
        src[i] = indent(line, tab * level)
        l, r = line.count('{'), line.count('}')
        if r > 0:
            dedent(src[i])
            src[i] = indent(line, tab * (level - 1))
        level += l - r

    return src


def extract_decl(s: str) -> Declaration:
    p = s.split(':', 1)
    assert len(p) == 2, f"Invalid Declaration string '{s}'"

    d = Declaration(
        name=p[0].strip(),
        dtype=p[1].strip(),
    )

    return d

def remove_all(l: list, e) -> int:
    n = 0
    try:
        while True:
            l.remove(e)
            n += 1
    except ValueError:
        pass

    return n

def extract_includes(d: dict) -> list[str] | None:
    try:
        includes = list( map(lambda s: s.strip(), d.pop('@include')))

        return includes
    except KeyError:
        return

def extract_template(d: dict) -> list[Declaration] | None:
    try:
        args = d.pop('@template')
        args = list(map(lambda a: extract_decl(a), args))
        return args
    except KeyError:
        return None

def extract_namespace(d: dict) -> str | None:
    try:
        space = d.pop('@namespace')
        return space
    except KeyError:
        return None

def extract_methods(d: dict) -> list[Method]:
    methods = []
    for decl_str, args in d.items():
        const = remove_all(args, '@const') > 0
        methods.append(Method(
            decl=extract_decl(decl_str),
            args=list(map(lambda a: extract_decl(a), args)),
            const=const,
        ))
    d.clear()
    return methods

def extract_interface(name, d) -> Interface:
    templ = extract_template(d)
    incs = extract_includes(d)
    namesp = extract_namespace(d)

    methods = extract_methods(d)

    iface = Interface(
        name=name,
        template=templ,
        methods=methods,
        includes=incs,
        namespace=namesp,
    )

    return iface

def make_interfaces(d: dict) -> list[Interface]:
    dc = deepcopy(d)
    ifaces = []
    for iname, idata in dc.items():
        ifaces.append(extract_interface(iname, idata))
    return ifaces

def interface(name: str, d: dict) -> Interface:
    dc = deepcopy(d)
    return extract_interface(name, dc)


'''
Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED “AS IS” AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
'''
