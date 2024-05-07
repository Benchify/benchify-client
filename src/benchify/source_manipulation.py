"""
manipulation of the python file
"""

import ast
from typing import Optional

def get_all_function_names(ast_tree: ast.AST) -> list[str]:
    """
    Extracts all function names from the provided AST tree, including named lambda functions.
    """
    function_names = []
    for node in ast.walk(ast_tree):
        if isinstance(node, ast.FunctionDef):
            function_names.append(node.name)
        elif isinstance(node, ast.Assign):
            # Check if the assigned value is a lambda
            if isinstance(node.value, ast.Lambda):
                # Check if the target is a single name (not handling tuple unpacking)
                if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    function_names.append(node.targets[0].id)
    return function_names

def get_function_source_from_source(function_str: str, function_name: str) -> Optional[str]:
    """
    pull out just this single function's source code
    """
    try:
        tree = ast.parse(function_str)
    except SyntaxError as _syn_error:
        print(_syn_error)
        return None
    return get_function_source(
        tree, function_name, function_str)

def get_function_source(ast_tree: ast.AST, function_name: str, code: str) -> Optional[str]:
    """
    pull out just this single function's source code
    """
    for node in ast.walk(ast_tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            start_line = node.lineno
            end_line = node.end_lineno
            function_source = '\n'.join(
                code.splitlines()[start_line - 1:end_line])
            return function_source
    # if the function was not found
    return None

def test_get_all_function_names():
    my_example = """
banana = lambda x : "banana"

def hotdog(a, b):
    return a + b
"""
    assert get_all_function_names(ast.parse(my_example)) == ["banana", "hotdog"]

def test_function_src():
    """
    1 function present
    """
    my_example = """
def main():
    return None
"""
    assert get_function_source_from_source(my_example,"main").strip() == my_example.strip()
    assert get_function_source_from_source(my_example,"mai") is None

def test_function_src_commented():
    """
    1 function present but has line below
    """
    my_example = """
def main():
# a comment
    return None
"""
    assert get_function_source_from_source(my_example,"main").strip() == my_example.strip()
    assert get_function_source_from_source(my_example,"mai") is None

def test_function_src_args():
    """
    1 function present but has inputs
    """
    my_example = """
def main(arg1: int,
    arg2: str):
# a comment
    return None
"""
    assert get_function_source_from_source(my_example,"main").strip() == my_example.strip()
    assert get_function_source_from_source(my_example,"mai") is None

def test_two_functions():
    """
    2 functions present
    """
    my_example_1 = """
def main(arg1: int,
    arg2: str):
# a comment
    return None
"""
    my_example_2 = """
def junk(arg1: int,
    arg2: str):
# a comment
    return None
"""
    my_example = my_example_1 + "\n\n" + my_example_2
    assert get_function_source_from_source(my_example,"main").strip() == my_example_1.strip()
    assert get_function_source_from_source(my_example,"junk").strip() == my_example_2.strip()
    assert get_function_source_from_source(my_example,"mai") is None

if __name__ == "__main__":
    test_function_src()
    test_function_src_commented()
    test_function_src_args()
    test_two_functions()
