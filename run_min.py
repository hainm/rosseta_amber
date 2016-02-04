#!/usr/bin/env python
import os
import subprocess
from mpi4py import MPI
comm = MPI.COMM_WORLD

rank, n_cores = comm.rank, comm.size

def split_range(n_chunks, start, stop):
    '''split a given range to n_chunks

    Examples
    --------
    >>> split_range(3, 0, 10)
    [(0, 3), (3, 6), (6, 10)]
    '''
    list_of_tuple = []
    chunksize = (stop - start) // n_chunks
    for i in range(n_chunks):
        if i < n_chunks - 1:
            _stop = start + (i + 1) * chunksize
        else:
            _stop = stop
        list_of_tuple.append((start + i * chunksize, _stop))
    return list_of_tuple

def run_each_core(pdbs, kwd):
    '''run a chunk of pdbs in each core
    '''
    for code in partial_codes:
        run_sander = (run_sander_template
                     .strip()
                     .format(**kwd)
                     )
        
        subprocess.call(' '.join(run_sander.split('\n')), shell=True)

def get_codes_for_my_rank(pdbs, rank):
    n_ligands = len(pdbs)
    start, stop = split_range(n_cores, 0, n_ligands)[rank]
    return pdbs[start: stop]


if __name__ == '__main__':
    run_sander_template = '{sander} -i {minin} -p {prmtop} -c {code}.rst7 -r {code}.min.rst7'
    
    cwd = os.getcwd()
    amber_library = os.path.join(cwd, 'amber_library')
    ligand_list = os.environ.get('LIGAND_CODES', amber_library + '/source/casegroup/pdbs.dat')
    
    with open(ligand_list, 'r') as fh:
        pdbs = [line.split()[-1] for line in fh.readlines()]

   partial_codes = get_codes_for_my_rank(pdbs, rank)
    run_each_core(partial_codes)
