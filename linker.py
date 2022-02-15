from pathlib import Path


def indent_line(code):
    if code.strip():
        return " " * 4 + code
    return ""


def import_to_def(module, src_path):
    src = [f"def {module}():"]
    src += list(map(indent_line, src_path.read_text().strip().split("\n")))
    return src + """
    local_module_namespace = __import__("types").SimpleNamespace()
    for variable, value in list(locals().items()):
        setattr(local_module_namespace, variable, value)
    return local_module_namespace""".split("\n")


def parse_import(module):
    path = Path(".") / f"{module}.py"
    if not path.is_file():
        return [f"import {module}"]
    return import_to_def(module, path) + [f"{module} = {module}()"]


def parse_from(module, vrbls):
    path = Path(".") / f"{module}.py"
    if not path.is_file():
        vrbls = ", ".join("{m} as {l}" if m != l else m for m, l in vrbls)
        return [f"from {module} import {vrbls}"]
    mns = f"{module}_namespace"
    src = import_to_def(mns, path)
    src.append(f"{mns} = {mns}()")
    for module_name, local_name in vrbls:
        src.append(f"{local_name} = {mns}.{module_name}")
    return src


def link(source):
    for line in source.split("\n"):
        if line.startswith("import "):
            yield from parse_import(line.split(" ", 1)[1])
        elif line.startswith("from "):
            _, module, _, vrbles = line.split(" ", 3)
            vrbles = map(lambda vrbl: vrbl.split(" as "), vrbles.split(", "))
            vrbles = [v if len(v) == 2 else [v[0], v[0]] for v in vrbles]
            yield from parse_from(module, vrbles)
        else:
            yield line


if __name__ == "__main__":
    import sys

    src, trgt = sys.argv[1], sys.argv[2]
    Path(trgt).write_text("\n".join(link(Path(src).read_text())))
