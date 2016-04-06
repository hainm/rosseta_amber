import os
from contextlib import contextmanager

@contextmanager
def temp_change_dir(new_dir):
    cwd = os.getcwd()
    os.chdir(new_dir)
    yield
    os.chdir(cwd)
