from dataclasses import dataclass

@dataclass
class Declaration:
    name: str
    dtype: str

    def declaration(self):
        return f'{self.dtype} {self.name}'

@dataclass
class Method:
    decl: Declaration
    args: list[Declaration]|None
    const: bool = False

    def vtable_declare(self): return

    def vtable_entries(self): return

    def implement(self): return

@dataclass
class Interface:
    name: str
    methods: list[Method]
    template: list[Declaration]|None= None

    def generate(self):
        return f'struct {self.name}{{}};'
    


i = Interface(
    name='List',
    methods=[
    ],
    template=None,
)

def make(name, d): return name, d

s, _ = make('List', {
    'append->void': {'e':'int'},
})

print(i)
