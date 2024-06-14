PURPOSE_OF_THIS_FILE = "just for testing"

from .demo2 import blarg as super_duper_important
import platform as banana_mango
from sys import platform
import os
import numpy

a = 44

def arbitrary_test_function(foo):
    print(a)
    return (
        super_duper_important(2 * [PURPOSE_OF_THIS_FILE] + [str(foo)]), 
        banana_mango.system(),
        platform(),
        os.name()
    )