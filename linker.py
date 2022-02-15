from pathlib import Path


def indent_line(code):
    if code.strip():
        return " " * 4 + code
    return ""


def parse_import(module):
    path = Path(".") / f"{module}.py"
    if not path.is_file():
        return [f"import {module}"]
    src = [f"def {module}():"]
    src += list(map(indent_line, path.read_text().strip().split("\n")))
    src += """
    local_module_namespace = __import__("types").SimpleNamespace()
    for variable, value in list(locals().items()):
        setattr(local_module_namespace, variable, value)
    return local_module_namespace""".split("\n")
    return src + [f"{module} = {module}()"]


def link(source):
    for line in source.split("\n"):
        if line.startswith("import "):
            yield from parse_import(line.split(" ", 1)[1])
        else:
            yield line


if __name__ == "__main__":
    import sys

    src, trgt = sys.argv[1], sys.argv[2]
    Path(trgt).write_text("\n".join(link(Path(src).read_text())))
