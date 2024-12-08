import os
import sys

def get_main_path():
    return os.path.dirname(os.path.realpath(sys.modules['__main__'].__file__))
