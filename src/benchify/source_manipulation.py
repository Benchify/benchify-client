"""
manipulation of the python file
"""
import ast, os, subprocess, sys, pytest
from typing import List, Optional, Set, Dict, Union, Tuple, Any
from stdlib_list import stdlib_list
from pkg_resources import working_set
import importlib.util

def is_system_package(module_name: str) -> bool:
    """
    Determines whether a given module name is part of the Python standard lib.

    Args:
        module_name (str): The name of the module to check.

    Returns:
        bool: True iff the module is part of the Python standard library.
    """
    if " as " in module_name:
        module_name = module_name.split(' as ')[0]
    return module_name in stdlib_list(".".join(map(str, sys.version_info[0:2])))

def is_pip_installed_package(module_name: str) -> bool:
    """
    Determines whether a given module name is pip-installable.

    Args:
        module_name (str): The name of the module to check.

    Returns:
        bool: True iff the module is pip-installable.
    """
    if " as " in module_name:
        module_name = module_name.split(' as ')[0]
    if is_system_package(module_name):
        return False
    if module_name in {pkg.key for pkg in working_set}:
        return True
    return importlib.util.find_spec(module_name) is not None

def find_local_module(module_name: str, file_path: str) -> Optional[str]:
    """
    Finds the path to a locally defined module.

    Args:
        module_name (str): The name of the module to check.
        file_path (str): The path relative to which the module was imported.

    Returns:
        str: The path where the module is defined, or None if it isn't.
    """
    # Split the module name into parts
    module_parts = module_name.split('.')
    
    # Start from the directory of the file being analyzed
    base_dir = os.path.dirname(file_path)
    
    # Recursive function to search for the module
    def search_module(current_dir, remaining_parts):
        if not remaining_parts:
            return None
        
        current_part = remaining_parts[0]
        module_file = os.path.join(current_dir, current_part + '.py')
        module_dir = os.path.join(current_dir, current_part)
        
        if os.path.isfile(module_file):
            if len(remaining_parts) == 1:
                return module_file
            else:
                return None
        elif os.path.isdir(module_dir):
            init_file = os.path.join(module_dir, '__init__.py')
            if os.path.isfile(init_file):
                result = search_module(module_dir, remaining_parts[1:])
                if result:
                    return result
        
        return None
    
    # Search for the module in the current directory and subdirectories
    result = search_module(base_dir, module_parts)
    if result:
        return result
    
    # Search for the module in the parent directories and their subdirectories
    parent_dir = os.path.dirname(base_dir)
    while parent_dir != base_dir:
        result = search_module(parent_dir, module_parts)
        if result:
            return result
        base_dir = parent_dir
        parent_dir = os.path.dirname(parent_dir)
    
    return None

def get_import_info(
    node: Union[ast.Import, ast.ImportFrom], 
    file_path: str) -> Tuple[str, str]:
    """
    Finds the import info for the given import.

    Args:
        node: Either an Import or an ImportFrom in ast.
        file_path (str): The path relative to which the module was imported.

    Returns:
        (str0, str1) where str0 is the type of import (local, pip, or system)
        and str2 is the import description (module name or path to module).
    """

    if isinstance(node, ast.Import):
        for alias in node.names:
            module_name = alias.name.strip()
            local_path = find_local_module(module_name, file_path)
            if local_path is not None:
                return ("local", local_path)
            elif is_pip_installed_package(module_name):
                return ("pip", module_name)
            else:
                return ("system", alias.name)
    
    elif isinstance(node, ast.ImportFrom):
        module_name = node.module
        local_path = find_local_module(module_name, file_path)
        if local_path is not None:
            return ("local", local_path)
        if is_pip_installed_package(module_name):
            return ("pip", module_name)
        return ("system", module_name)

def get_import_info_recursive(
    node: Union[ast.Import, ast.ImportFrom],
    file_path: str) -> Dict[Tuple[str, str], Any]:
    """
    Recursively retrieves import information for a given import node and its dependencies.

    Args:
        node (Union[ast.Import, ast.ImportFrom]): The import node to analyze.
        file_path (str): The path of the file containing the import node.

    Returns:
        Dict[Tuple[str, str], Any]: A dictionary mapping import categories and 
        names to their respective import information. The keys are tuples of 
        (category, name), where category is one of "local", "pip", or "system", 
        and name is the name of the imported module or package, or the file path
        for the module if it's locally defined. The values are dictionaries of 
        the same kind.
    """
    import_info = {}

    # Categorize the node using get_import_info
    category, module_file_path_or_name = get_import_info(node, file_path)
    cur_key = (category, module_file_path_or_name)
    import_info[cur_key] = []

    if category == "system" or category == "pip":
        return import_info

    assert category == "local"
    module_ast = None
    with open(module_file_path_or_name, "r") as fr:
        module_ast = ast.parse(fr.read())

    for sub in ast.walk(module_ast):
        if isinstance(sub, ast.Import) or isinstance(sub, ast.ImportFrom):
            print("Recursing on sub-import ...")
            sub_import_info = get_import_info_recursive(
                sub, module_file_path_or_name)

            import_info[cur_key].append(sub_import_info)

    return import_info

# I-AM-HERE









# INPUT:
#     the_file: The path to the Python file we are analyzing.
# OUTPUT:
#     files: The list of paths to (local) Python files which the_file imports.
def resolve_local_imports(the_file: str) -> List[str]:
    with open(the_file, 'r') as file:
        tree = ast.parse(file.read())
    files = []
    base_dir = os.path.dirname(the_file)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name
                module_path = os.path.join(base_dir, module_name + '.py')
                if os.path.isfile(module_path):
                    files.append(module_path)
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module
            if module_name:
                if module_name.startswith('.'):
                    module_path = os.path.normpath(os.path.join(base_dir, module_name + '.py'))
                else:
                    module_path = os.path.join(base_dir, module_name + '.py')
                if os.path.isfile(module_path):
                    files.append(module_path)
    return files

# INPUT:
#     the_file: The path to the Python file we are analyzing.
# OUTPUT:
#     files: The list of paths to (local) Python files which the_file imports,
#            plus, all the files imported by those files, and so on.
# EXAMPLE:
#     the_file = benchify/benchify/main.py
def resolve_local_imports_recursive(the_file: str) -> List[str]:
    visited = set()
    result = []

    def resolve_imports(file_path):
        if file_path in visited:
            return
        visited.add(file_path)
        
        imports = resolve_local_imports(file_path)
        result.extend(imports)
        
        for imported_file in imports:
            resolve_imports(imported_file)
    
    resolve_imports(the_file)
    return list(dict.fromkeys(result))

# INPUT:
#     the_file: The path to the Python file we are analyzing.
# OUTPUT:
#     pip_imports: The list of packages that must be pip-imported.
def resolve_pip_and_builtin_imports(the_file: str) -> List[str]:
    with open(the_file, 'r') as file:
        tree = ast.parse(file.read())

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name
                imports.append(module_name)
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module
            if module_name:
                imports.append(module_name)

    local_imports = [
        os.path.splitext(os.path.basename(file))[0] 
        for file in resolve_local_imports(the_file)
    ]

    libraries = stdlib_list(".".join(map(str, sys.version_info[0:2])))

    pip_imports, builtin_imports = [], []
    for module in imports:
        if module not in local_imports:
            if module not in libraries:
                pip_imports.append(module)
            else:
                builtin_imports.append(module)

    return list(dict.fromkeys(pip_imports)), list(dict.fromkeys(builtin_imports))

# INPUT:
#     the_file: The path to the Python file we are analyzing.
# OUTPUT:
#     pip_imports: The list of packages that must be pip-imported both for this
#                  file to work and, recursively, for the other files this one
#                  imports to work.
# ------------------------------------------------------------------------------
# NOTE -- It may be useful later to restrict this to just the ones that are
# used by the function under test.  However, this approach also complicates the 
# code by requiring recursive analysis of the function's dependencies.
# ------------------------------------------------------------------------------
def resolve_pip_and_builtin_imports_recursive(the_file: str) -> List[str]:
    visited = set()
    result_pip, result_builtin = [], []

    def resolve_imports(file_path):
        if file_path in visited:
            return
        visited.add(file_path)
        
        pip_imports, builtin_imports = resolve_pip_and_builtin_imports(file_path)
        result_pip.extend(pip_imports)
        result_builtin.extend(builtin_imports)
        
        local_imports = resolve_local_imports_recursive(file_path)
        for imported_file in local_imports:
            resolve_imports(imported_file)
    
    resolve_imports(the_file)
    return list(dict.fromkeys(result_pip)), list(dict.fromkeys(result_builtin))

def get_top_level_lambda_function_names(ast_tree: ast.AST) -> List[str]:
    """
    Extracts the names of all top-level lambda functions assigned to variables
    from the provided Python code.
    """
    lambda_function_names = []
    for node in ast.iter_child_nodes(ast_tree):
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Lambda) and isinstance(node.targets[0], ast.Name):
                lambda_function_names.append(node.targets[0].id)
    return lambda_function_names

def get_all_function_names(function_str: str) -> List[str]:
    """
    Extracts all top-level function names from the provided AST tree.
    """
    ast_tree = ast.parse(function_str)
    function_names = []
    for node in ast.iter_child_nodes(ast_tree):
        if isinstance(node, ast.FunctionDef):
            function_names.append(node.name)
    return function_names + get_top_level_lambda_function_names(ast_tree)

def get_function_source(source_code: str, function_name: str) -> Optional[str]:
    """
    pull out just this single function's source code
    """
    ast_tree = None
    try:
        ast_tree = ast.parse(source_code)
    except SyntaxError as syn_error:
        print(syn_error)
        return None
    
    cur_node = None
    for node in ast.walk(ast_tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            cur_node = node
            break
    if cur_node is None:
        return None
    # Step 1: Find the imported modules and their aliases
    import_aliases = {}
    for node in ast.walk(ast_tree):  # Use ast_tree instead of cur_node
        if isinstance(node, ast.ImportFrom):
            module_name = node.module
            for alias in node.names:
                import_aliases[alias.asname or alias.name] = f"{module_name}.{alias.name}"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                import_aliases[alias.asname or alias.name] = alias.name
    # Step 2: Modify the function to replace aliases with module names
    modified_node = ast.fix_missing_locations(ast.parse(ast.unparse(cur_node))).body[0]
    for node in ast.walk(modified_node):
        if isinstance(node, ast.Name) and node.id in import_aliases:
            node.id = import_aliases[node.id]
    # Step 3: Generate the modified source code
    modified_code = ast.unparse(modified_node)
    # Step 4: Extract the function source code with comments
    start_line = cur_node.lineno - 1
    end_line = cur_node.body[-1].end_lineno
    function_lines = source_code.splitlines()[start_line:end_line]
    # Step 5: Replace the function code with the modified code
    def_line = source_code.splitlines()[start_line:cur_node.body[0].lineno - 1]
    body_lines = modified_code.splitlines()[1:]
    normalized_code = '\n'.join(def_line + body_lines)
    return normalized_code

# --------------------------- BELOW HERE IS UNTESTED ---------------------------
def find_called_functions(source_file: str, function_name: str) -> List[str]:
    called_functions = []

    with open(source_file, 'r') as file:
        tree = ast.parse(file.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            for subnode in ast.walk(node):
                if isinstance(subnode, ast.Call):
                    if isinstance(subnode.func, ast.Name):
                        called_functions.append(subnode.func.id)
                    elif isinstance(subnode.func, ast.Attribute):
                        called_functions.append(subnode.func.attr)

    return list(dict.fromkeys(called_functions))



def get_flattened_function(source_file: str, function_name: str):
    # Get the pip and builtin imports
    pip_imports, builtin_imports = resolve_pip_and_builtin_imports_recursive(source_file)
    
    # Get the local imports
    # dependencies_inside_the_original_file = extract_function_dependencies_recursive(source_file, function_name)

    # Get the function.
    source_code = ""
    with open(source_file, "r") as fr:
        source_code = fr.read()
    normalized_function = get_function_source(source_code, function_name)

    flattened_code = ""
    if len(pip_imports) > 0:
        flattened_code += "import " + ", ".join(pip_imports)
    if len(builtin_imports) > 0:
        if len(pip_imports) > 0:
            flattened_code += "\n"
        flattened_code += "import " + ", ".join(builtin_imports)

    # Add in the local imports.
    # TODO -- normalize these.
    # flattened_code += "\n" + dependencies_inside_the_original_file

    flattened_code += "\n\n" + normalized_function

    return flattened_code


"""
--------------------------------- UNIT TESTS ----------------------------------- 
"""

def clean_string(string):
    lines = string.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    result = '\n'.join(non_empty_lines)
    return result.strip()

def test_resolve_pip_and_builtin_imports():
    pips_lhs, syss_lhs = resolve_pip_and_builtin_imports("src/benchify/main.py")

    pips_rhs = ["appdirs", "auth0.authentication.token_verifier",
        "jwt", "requests", "rich", "rich.console", "typer"]

    syss_rhs = ["os", "pickle", "sys", "time", "typing", "webbrowser"]

    assert sorted(pips_lhs) == sorted(pips_rhs)
    assert sorted(syss_lhs) == sorted(syss_rhs)

    pips_lhs, syss_lhs = resolve_pip_and_builtin_imports_recursive("src/benchify/main.py")

    pips_rhs += ["stdlib_list", "pytest"]
    syss_rhs += ["ast", "subprocess", "platform"]

    assert sorted(pips_lhs) == sorted(pips_rhs)
    assert sorted(syss_lhs) == sorted(syss_rhs)

def test_get_top_level_lambda_function_names():
    code = '''
banana = lambda x : x + 1
hotdog = lambda x : lambda y : y + x
def shoe(y):
    dilbert = lambda i : i * banana(i)
    return dilbert(y)
'''
    lhs = get_top_level_lambda_function_names(ast.parse(code))
    assert lhs == ['banana', 'hotdog']

def test_get_all_function_names():
    code = '''
def blarg():
    def foo():
        return 5
    return blarg()

bar = lambda x: x + 1

def baz():
    pass
'''
    function_names = get_all_function_names(code)
    print("function names: ", set(function_names))
    assert set(function_names) == {'blarg', 'bar', 'baz'}

def test_get_all_function_names_happy():
    """
    names of both defined functions and named lambda functions retrieved
    no funniness with nested functions or repeated names
    """
    my_example = """
banana = lambda x : "banana"

def hotdog(a, b):
    return a + b
"""
    assert sorted(get_all_function_names(my_example)) == sorted(["banana", "hotdog"])

def test_get_all_function_names():
    """
    names of both defined functions and named lambda functions retrieved
    yes funniness with nested functions or repeated names
    """
    _banana_0 = "banana = lambda x : 'banana'"
    banana_1 = """
def banana(x, y):
    return x * y
"""
    hotdog = """
def hotdog(a, b):
    def banana(x, y):
        return x * y
    return a + b
"""

    my_example = """
banana = lambda x : 'banana'

def hotdog(a, b):
    def banana(x, y):
        return x*y
    return a + b
"""
    assert sorted(get_all_function_names(my_example)) == sorted(["banana", "hotdog"])
    hotdog_source = get_function_source(
        my_example, 
        "hotdog")

    assert clean_string(hotdog_source) == clean_string(hotdog)

    _hotdog_parse = ast.parse(hotdog_source)
    banana_source = get_function_source(my_example, "banana")

    did_throw_correct = False
    try:
        _banana_parse = ast.parse(banana_source)
    except SyntaxError as nested_parse_error:
        error_msg = nested_parse_error.msg
        #pylint:disable=no-member
        if error_msg.startswith('unexpected indent'):
            did_throw_correct = True
    finally:
        assert did_throw_correct

def test_function_src():
    """
    1 function present
    """
    my_example = """
def main():
    return None
"""
    assert clean_string(get_function_source(my_example,"main")) == clean_string(my_example)
    assert get_function_source(my_example,"mai") is None

def test_function_src_commented():
    """
    1 function present but has line below
    """
    my_example = """
def main():
# a comment
    return None
"""
    assert clean_string(get_function_source(my_example,"main")) == clean_string(my_example)
    assert get_function_source(my_example,"mai") is None

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
    assert clean_string(get_function_source(my_example,"main")) == clean_string(my_example)
    assert get_function_source(my_example,"mai") is None

def test_two_functions():
    """
    2 functions present
    """
    my_example_1 = """
def main(arg1: int, arg2: str):
# a comment about main
    return None
"""
    my_example_2 = """
def junk(arg1: int, arg2: str):
# a comment about junk
    return None
"""
    my_example = my_example_1 + "\n\n" + my_example_2
    assert clean_string(get_function_source(my_example,"main")) == clean_string(my_example_1)
    assert clean_string(get_function_source(my_example,"junk")) == clean_string(my_example_2)
    assert get_function_source(my_example,"mai") is None



# def test_get_flattened_function():
#     lhs = get_flattened_function("src/benchify/empty.py", "arbitrary_test_function")
#     print("lhs = \n", lhs)
#     flattened_function = """
# import platform, sys, os

# PURPOSE_OF_THIS_FILE = "just for testing"

# def blarg(lst):
#     return (lst, lst)

# def arbitrary_test_function(foo):
#     return (
#         blarg(2 * [PURPOSE_OF_THIS_FILE] + [str(foo)]), 
#         banana_mango.system(),
#         sys.platform(),
#         os.name()
#     )
# """
#     print("rhs = \n", flattened_function)
#     assert lhs == flattened_function
