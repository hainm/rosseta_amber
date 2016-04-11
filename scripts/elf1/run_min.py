#!/usr/bin/env python
'''
Example: mpirun -n 8 python run_min.py -O -p prmtop -c "*.rst7" -i min.in

Make sure to sue quote " " for pattern
'''

import os
import sys
import subprocess
import argparse
from glob import glob
from mpi4py import MPI
comm = MPI.COMM_WORLD

sys.path.append('.')
from utils import split_range

rank, n_cores = comm.rank, comm.size

COMMAND_TEMPLATE = '{sander} {overwrite} -i {minin} -p {prmtop} -c {abspath_rst7} -r min_{rst7} -o out/min_{rst7_no_ext}.out -ref {abspath_rst7}'


def run_each_core(cmlist):
    '''run a chunk of total_commands in each core

    Parameters
    ----------
    cmlist : a list of commands
    '''
    for cm in cmlist:
        os.system(cm)

def get_commands_for_my_rank(total_commands, rank, n_cores):
    import numpy as np
    arr = np.array(total_commands)

    sub_commands = np.array_split(arr, n_cores)[rank]
    if len(sub_commands) > 0:
        return sub_commands
    else:
        return ['echo nothing',]

def get_unfinished_rst7_files(args):
    '''get not-run yet files or file has size of 0. Use absolute path
    
    args : ArgumentParser
    '''
    cwd = os.getcwd()

    all_old_restart_files = glob(args.restart_pattern)
    rst7_files = [os.path.basename(x) for x in all_old_restart_files]
    orgin_rst7_dir = os.path.dirname(all_old_restart_files[0])
    minfiles = glob('min_*rst7')
    
    MINSIZE = 1000 # bytes
    done_files = {x.strip('min_') for x in minfiles if os.path.getsize(x) > 1000}
    return [os.path.join(orgin_rst7_dir, fn) for fn in set(rst7_files) - done_files]

try:
    sys.argv.remove('-O')
    overwrite = '-O'
except ValueError:
    overwrite = ''

def get_total_commands(rst7_files, COMMAND_TEMPLATE=COMMAND_TEMPLATE):
    commands = []
    for rst7_file in rst7_files:
        # make sure rst7 is relative path
        abspath_rst7 = os.path.abspath(rst7_file)
        rst7 = rst7_file.split('/')[-1]
        restart_ext = '.' + rst7.split('.')[-1]
        command = COMMAND_TEMPLATE.format(
            sander='sander',
            overwrite=overwrite,
            minin=args.mdin,
            prmtop=args.prmtop,
            rst7=rst7,
            abspath_rst7=abspath_rst7,
            rst7_no_ext=rst7.strip(restart_ext))

        commands.append(command)
    return commands

def get_args_cmdln():

    description = '''
    Example: mpirun -n 8 python {my_program} -p prmtop -c "*.rst7" -i min.in
    '''.strip().format(my_program=sys.argv[0])

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-p', dest='prmtop', help='prmtop', required=True)
    parser.add_argument('-c', dest='restart_pattern',
                        required=True, help='pattern to search for rst7 files')
    parser.add_argument('-i', dest='mdin', required=True, help='min.in file')
    parser.add_argument('-u', '--only-unfinished', action='store_true')

    args = parser.parse_args(sys.argv[1:])
    return args


if __name__ == '__main__':
    args = get_args_cmdln()

    if args.only_unfinished:
        rst7_files = get_unfinished_rst7_files(args)
    else:
        rst7_files = glob(args.restart_pattern)

    if rank == 0:
        pwd = '/'.join(os.getcwd().split('/')[-4:])
        print('number of runs = {} in {}'.format(len(rst7_files), pwd))

    try:
        os.mkdir('out')
    except OSError:
        pass

    commands = get_total_commands(rst7_files)
    myrank_cmlist = get_commands_for_my_rank(commands, rank, n_cores)

    n_structures = len(myrank_cmlist)
    x = comm.gather(n_structures, root=0)
    if rank == 0:
        print('max structures per node = {}'.format(max(x)))
    run_each_core(myrank_cmlist)

    # debug
    # if len(myrank_cmlist) > 3:
    #     print('rank = {}, n_jobs = {}'.format(rank, len(myrank_cmlist)))

