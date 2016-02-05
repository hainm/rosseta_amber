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
        run_sander = (command_template
                      .strip()
                      .format(**kwd)
                      )

        subprocess.call(' '.join(run_sander.split('\n')), shell=True)


def get_codes_for_my_rank(pdbs, rank):
    n_ligands = len(pdbs)
    start, stop = split_range(n_cores, 0, n_ligands)[rank]
    return pdbs[start: stop]


if __name__ == '__main__':
    import sys
    from glob import glob
    import argparse

    try:
        sys.argv.remove('-O')
        overwrite = '-O'
    except ValueError:
        overwrite = ''

    description = '''
    Example: mpirun -n 8 python {my_program} -p prmtop -c *.rst7 -i min.in
    '''.strip().format(my_program=sys.argv[0])

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-p', dest='prmtop', help='prmtop', required=True)
    parser.add_argument('-c', dest='restart_pattern',
                        required=True, help='pattern to search for rst7 files')
    parser.add_argument('-i', dest='mdin', required=True, help='min.in file')

    args = parser.parse_args()

    rst7_files = glob(args.restart_pattern)

    try:
        os.mkdir('out')
    except OSError:
        pass

    command_template = '{sander} {overwrite} -i {minin} -p {prmtop} -c {rst7} -r min.{rst7} -o out/out.{rst7}'

    for rst7 in rst7_files:
        command = command_template.format(
            sander='sander',
            overwrite=overwrite,
            minin=args.mdin,
            prmtop=args.prmtop,
            rst7=rst7)
        print(command)
        os.system(command)
    #
    # cwd = os.getcwd()
    # amber_library = os.path.join(cwd, 'amber_library')
    # ligand_list = os.environ.get('LIGAND_CODES', amber_library + '/source/casegroup/pdbs.dat')
    #
    # with open(ligand_list, 'r') as fh:
    #     pdbs = [line.split()[-1] for line in fh.readlines()]

    # partial_codes = get_codes_for_my_rank(pdbs, rank)
    # run_each_core(partial_codes)
