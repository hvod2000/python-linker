from pathlib import Path


def indent_line(code, level=1):
    if code.strip():
        return " " * (4 * level) + code
    return ""


def is_user_built_module(module_name):
    path = Path(".") / f"{module_name}.py"
    return path.is_file()


def parse_imports(source):
    source = source.split("\n") if isinstance(source, str) else source
    imports = set()
    for line in source:
        if line.startswith("import "):
            imports.add((line.split(" ", 1)[1], None))
        elif line.startswith("from "):
            _, module, _, vrbles = line.split(" ", 3)
            vrbles = map(lambda vrbl: vrbl.split(" as "), vrbles.split(", "))
            vrbles = tuple(v if len(v) == 2 else (v[0], v[0]) for v in vrbles)
            imports.add((module, tuple(map(tuple, vrbles))))
    return imports


def parse_deps(source):
    stack, deps, visited = [m for m, _ in parse_imports(source)], set(), set()
    while stack:
        imprt = stack.pop()
        if not is_user_built_module(imprt):
            continue
        deps.add(imprt)
        for m, _ in parse_imports(Path(imprt + ".py").read_text()):
            if m not in visited:
                visited.add(m)
                stack.append(m)
    return deps


def refactor_imports(source, deps):
    source = source.split("\n") if isinstance(source, str) else source
    for line in source:
        if line.startswith("import "):
            module = line.split(" ", 1)[1]
            if module in deps:
                yield f"{module} = {module}_namespace()"
                continue
        elif line.startswith("from "):
            _, module, _, vrbles = line.split(" ", 3)
            vrbles = map(lambda vrbl: vrbl.split(" as "), vrbles.split(", "))
            vrbles = [v if len(v) == 2 else [v[0], v[0]] for v in vrbles]
            if module in deps:
                for local_vrbl, vrbl in vrbles:
                    yield f"{vrbl} = {module}_namespace().{local_vrbl}"
                continue
        yield line


class Module:
    def __init__(self, name, source, imports, deps):
        self.name = name
        self.source = source
        self.imports = imports
        self.deps = deps - {name}

    @staticmethod
    def from_source(path, source=None):
        path = Path(path)
        name = path.stem
        source = source if source else path.read_text()
        source = source.split("\n") if isinstance(source, str) else source
        return Module(name, source, parse_imports(source), parse_deps(source))

    def to_namespace(self):
        mns = f"{self.name}_namespace"
        code = refactor_imports(self.source, self.deps)
        src = [f"def {mns}():"] + list(map(indent_line, code))
        return src + f"""    if True:
        {mns}_content = list(locals().items())
        global {mns}
        {mns} = CallableSimpleNamespace()
        for variable, value in {mns}_content:
            setattr({mns}, variable, value)
        return {mns}""".split("\n")

    def build(self):
        c = "CallableSimpleNamespace"
        code = [f'class {c}(__import__("types").SimpleNamespace):']
        code.append(indent_line("__call__ = lambda self: self"))
        code += ['']*2
        for dep in self.deps:
            code += Module.from_source(dep + ".py").to_namespace()
            code += ['']*2
        return code + list(refactor_imports(self.source, self.deps))

    def __repr__(self):
        name, source = self.name, self.source
        imports, deps = self.imports, self.deps
        return f"Module({name}, {source}, {imports}, {deps})"


if __name__ == "__main__":
    import sys

    source, target = sys.argv[1], sys.argv[2]
    Path(target).write_text("\n".join(Module.from_source(source).build()))
