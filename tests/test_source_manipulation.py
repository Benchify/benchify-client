from src.benchify.source_manipulation import is_system_package, is_pip_installed_package, get_import_info
import ast

def test_is_system_package():
    assert not is_system_package("auth0-python")
    assert not is_system_package("appdirs")
    assert not is_system_package("pyjwt")
    assert not is_system_package("requests")
    assert not is_system_package("rich")
    assert not is_system_package("typer")
    assert not is_system_package("urllib3")
    assert not is_system_package("stdlib_list")
    assert not is_system_package("pytest")
    assert not is_system_package("pytest")

    assert is_system_package("os")
    assert is_system_package("sys")
    assert is_system_package("re")

    assert not is_system_package("banana hotdog mango !!!")
    assert not is_system_package("")

    exceptions = 0
    try:
        _ = is_system_package(None)
    except Exception as e:
        exceptions = 1
    assert exceptions == 1

def test_is_pip_installed_package():
    assert is_pip_installed_package("auth0-python")
    assert is_pip_installed_package("appdirs")
    assert is_pip_installed_package("pyjwt")
    assert is_pip_installed_package("requests")
    assert is_pip_installed_package("rich")
    assert is_pip_installed_package("typer")
    assert is_pip_installed_package("urllib3")
    assert is_pip_installed_package("stdlib_list")
    assert is_pip_installed_package("pytest")
    assert is_pip_installed_package("pytest")

    assert not is_pip_installed_package("os")
    assert not is_pip_installed_package("sys")
    assert not is_pip_installed_package("re")
    assert not is_pip_installed_package("banana hotdog mango !!!")
    
    exceptions = 0
    try:
        _ = is_pip_installed_package("")
    except Exception as e:
        exceptions += 1
        pass
    
    try:
        _ = is_pip_installed_package(None)
    except Exception as e:
        exceptions += 1
        pass

    assert exceptions == 2

def test_import_pip_installed_package():
    file_path1 = 'tests/fixtures/demo1.py'
    file_path2 = 'tests/fixtures/demo2.py'

    node = ast.Import(names=[ast.alias(name='numpy', asname=None)])
    assert get_import_info(node, file_path1) == ('pip', 'numpy')
    
    node = ast.Import(names=[ast.alias(name='platform', asname='banana_mango')])
    assert get_import_info(node, file_path1) == ('system', 'platform')

    node = ast.ImportFrom(
        module='demo2', 
        names=[ast.alias(name='blarg', asname='super_duper_important')], 
        level=1)
    assert get_import_info(node, file_path1) == ('local', file_path2)

    

# def test_get_all_function_names():
#     lhs = find_called_functions("src/benchify/main.py", "validate_token")
#     rhs = ["AsymmetricSignatureVerifier", "TokenVerifier", "verify"]
#     assert lhs == rhs

#     lhs = find_called_functions(
#         "src/benchify/source_manipulation.py", "resolve_local_imports")
#     rhs = ["walk", "open", "parse", "isinstance", "read", "join", "isfile", 
#         "dirname", "append", "startswith"]
#     assert lhs == rhs

# def test_resolve_local_imports():
#     lhs = resolve_local_imports("src/benchify/main.py")
#     rhs = ["src/benchify/source_manipulation.py"] 
#     assert lhs == rhs
#     lhs = resolve_local_imports_recursive("tests/fixtures/demo1.py")
#     assert lhs != rhs
#     rhs = ["tests/fixtures/demo2.py"]
#     assert resolve_local_imports("tests/fixtures/demo1.py") == rhs
#     rhs += ["tests/fixtures/demo3.py"]
#     assert lhs == rhs