# Script used to inspect differences between objectbox/lib/objectbox.h and c.py (e.g. missing function declarations)
# Usage:
#   python inspect_c_bindings.py
# Requirements:
# - pycparser
# - pycparser-fake-libc
# - objectbox or project root in PYTHONPATH

from os import path
from pycparser import c_ast, parse_file
import pycparser_fake_libc
import objectbox.c

script_dir = path.dirname(path.realpath(__file__))


class FuncDeclVisitor(c_ast.NodeVisitor):
    def __init__(self):
        self.func_decls = set()

    def visit_FuncDecl(self, node: c_ast.FuncDecl):
        # TODO declname is set in the return type (i.e. type field)?
        func_name = None
        if isinstance(node.type, c_ast.TypeDecl):
            func_name = node.type.declname
        elif isinstance(node.type, c_ast.PtrDecl):
            func_name = node.type.type.declname
        else:
            raise Exception(f"Unknown node type: {node.type}")
        self.func_decls.add(func_name)


def _parse_header_file(filename):
    fake_libc_arg = "-I" + pycparser_fake_libc.directory

    ast = parse_file(filename, use_cpp=True, cpp_args=fake_libc_arg)  # use_cpp = Use C Pre Processor

    visitor = FuncDeclVisitor()
    visitor.visit(ast)

    num_missing = 0
    for func_decl in visitor.func_decls:
        if not hasattr(objectbox.c, func_decl):
            print(f"Missing function: {func_decl}")
            num_missing += 1

    print(f"Missing {num_missing}/{len(visitor.func_decls)} function declarations in c.py")


def _main():
    objectbox_h = path.join(script_dir, "../objectbox/lib/objectbox.h")
    if not path.exists(objectbox_h):
        raise Exception("File not found: objectbox/lib/objectbox.h")
    _parse_header_file(objectbox_h)


if __name__ == "__main__":
    _main()
