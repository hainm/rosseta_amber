#!/usr/bin/env python
'''
Example: python run_min_multiprocessing.py -O -p prmtop -c "*.rst7" -i min.in

Make sure to sue quote " " for pattern
'''

import os
from multiprocessing import Pool, cpu_count

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


def run_each_core(cmlist):
    '''run a chunk of total_commands in each core

    Parameters
    ----------
    cmlist : a list of commands
    '''
    for cm in cmlist:
        os.system(cm)

def get_commands_for_my_rank(total_commands, rank, n_cores):
    n_structures = len(total_commands)
    start, stop = split_range(n_cores, 0, n_structures)[rank]
    return total_commands[start: stop]

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
    Example: mpirun -n 8 python {my_program} -p prmtop -c "*.rst7" -i min.in
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

    command_template = '{sander} {overwrite} -i {minin} -p {prmtop} -c {abspath_rst7} -r min_{rst7} -o out/min_{rst7_no_ext}.out -ref {abspath_rst7}'

    commands = []
    for rst7_file in rst7_files:
        # make sure rst7 is relative path
        abspath_rst7 = os.path.abspath(rst7_file)
        rst7 = rst7_file.split('./')[-1]
        restart_ext = '.' + rst7.split('.')[-1]
        command = command_template.format(
            sander='sander',
            overwrite=overwrite,
            minin=args.mdin,
            prmtop=args.prmtop,
            rst7=rst7,
            abspath_rst7=abspath_rst7,
            rst7_no_ext=rst7.strip(restart_ext))
        commands.append(command)

    n_cores = cpu_count() - 1

    def run(rank):
        myrank_cmlist = get_commands_for_my_rank(commands, rank, n_cores)
        run_each_core(myrank_cmlist)

    pool = Pool(n_cores)
    pool.map(run, list(range(n_cores)))
    pool.close()
