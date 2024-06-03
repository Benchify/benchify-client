"""
Empty file just for testing resolve_local_imports_recursive
(Well, it is not empty, but it's empty of stuff that actually matters ...)
"""
PURPOSE_OF_THIS_FILE = "just for testing"

from .empty2 import blarg as super_duper_important
import platform as banana_mango
from sys import platform
import os

def arbitrary_test_function(foo):
    return (
        super_duper_important(2 * [PURPOSE_OF_THIS_FILE] + [str(foo)]), 
        banana_mango.system(),
        platform(),
        os.name()
    )