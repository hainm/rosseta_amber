import os
from contextlib import contextmanager

@contextmanager
def temp_change_dir(new_dir):
    cwd = os.getcwd()
    os.chdir(new_dir)
    yield
    os.chdir(cwd)

def split_range(n_chunks, start, stop):
    '''split a given range to n_chunks

    Examples
    --------
    >>> split_range(3, 0, 10)
    [(0, 3), (3, 6), (6, 10)]
    '''
    list_of_tuple = []
    chunksize = (stop - start) // n_chunks

    if chunksize == 0:
        effective_n_chunk = stop - start
        chunksize = 1
    else:
        effective_n_chunk = n_chunks
        chunksize = chunksize
    
    for i in range(n_chunks):
        if i < n_chunks - 1:
            _stop = start + (i + 1) * chunksize
        else:
            _stop = stop
        list_of_tuple.append((start + i * chunksize, _stop))
    return list_of_tuple

def force_mkdir(my_dir):
    try:
        os.mkdir(my_dir)
    except OSError:
        pass
