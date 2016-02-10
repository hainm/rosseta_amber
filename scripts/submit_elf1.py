#!/usr/bin/env python

description = '''
Run all minimizations (with and without restraining) for all proteins:
    # supposed you're in ./DecoyDiscrimination folder
    # submit all jobs to cluster
    python scripts/elf1/submit_elf1.py --over-write --submit

    # only write submit.sh script in each folder
    python scripts/elf1/submit_elf1.py --over-write

To run specific code:
    python scripts/elf1/submit_elf1.py --code 1ez3 --over-write --submit

Please use -h to see more options


Notes
-----
- no_restraint files are in decoys.set{1,2}.init/{pdbcode}/no_restraint/
- If you are not using slurm, please updateS SLURM_TEMPLATE


'''

import os
import sys
import time
import subprocess
from glob import glob, iglob
import argparse
from argparse import RawTextHelpFormatter
from contextlib import contextmanager

SLURM_TEMPLATE = '''#!/bin/sh
#SBATCH -J {job_name}
#SBATCH -o {job_name}.%J.stdout
#SBATCH -e {job_name}.%J.stderr
#SBATCH -p {job_type}
#SBATCH -N {n_nodes}
#SBATCH -t {time}:00:00

cd {pwd}
run_script={run_script}
minfile={minfile}
prmtop={prmtop}

mpirun -n {total_cores} $run_script {overwrite} -p $prmtop -c "{rst7_pattern}" -i $minfile {only_unfinished}
'''


@contextmanager
def temp_change_dir(new_dir):
    cwd = os.getcwd()
    os.chdir(new_dir)
    yield
    os.chdir(cwd)


def parse_args():
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=RawTextHelpFormatter)
    parser.add_argument(
        '-n',
        '--n-nodes',
        help='number of nodes, default 1',
        default=1, type=int)
    parser.add_argument(
        '-e',
        '--engine',
        help='using MPI or multiprocessing',
        default='mpi', type=str)
    parser.add_argument(
        '-j',
        '--job-type',
        help='type of job (main, development, short)', 
        default='main', type=str)
    parser.add_argument(
        '-d',
        '--decoy_dir',
        help='root folder of decoy, default ./',
        type=str)
    parser.add_argument(
        '-cn',
        '--core-per-node',
        help='number of cores per node, default 24',
        default=24, type=int)
    parser.add_argument(
        '-id',
        '--code',
        required=True,
        help='pdb code or "all" (run all codes)',
        type=str)
    parser.add_argument(
        '-t',
        dest='time',
        help='total time to run (hours), default 24 hours',
        default='24', type=int)
    parser.add_argument(
        '-sleep',
        '--sleep',
        help='time between each submission',
        default='0.5', type=float)
    parser.add_argument(
        '-rst7_pattern',
        '--rst7-pattern',
        default='NoH*.rst7',
        help='pattern to search for rst7 files, default *.rst7', type=str)
    parser.add_argument('-u', '--only-unfinished', action='store_true')
    parser.add_argument(
        '-m',
        '--min-type',
        default=0,
        help='minimization type:\n\t0: with and without restraint;\n\t1: with restraint;\n\t2: no restraint',
        type=int)
    parser.add_argument(
        '-rs',
        '--run-script',
        default=os.path.abspath('scripts/elf1/run_min.py'),
        help='script to run minimization for each protein; if not given, using scripts/elf1/run_min.py',
        type=str)
    parser.add_argument(
        '-O',
        '--over-write',
        help='Similiar to -O flag in sander: use it if you want to overwrite',
        action='store_true')
    parser.add_argument(
        '-s',
        '--submit',
        help='if given, jobs will be submitted to cluster, else only submit.sh files will be created',
        action='store_true')
    parser.add_argument(
        '-p',
        '--prmtop-ext',
        default='parm7',
        help='extension to search for prmtop file, default parm7', type=str)
    parser.add_argument(
        '-rmin',
        '--root-min-dir',
        default=os.path.abspath('scripts/min/'),
        help='extension to search for folder having minimization input (min.in, min_norestraint.in), ./scripts/min/',
        type=str)
    parser.add_argument(
        '-cmd',
        '--cmd',
        default='sbatch',
        help="submit job command, default 'sbatch'", type=str)

    args = parser.parse_args(sys.argv[1:])
    return args


def get_dir_from_code(code, root='./'):
    dirs = glob('decoys.set*.init')

    for code_dir in dirs:
        supposed_dir = os.path.join(root, code_dir, code)
        if os.path.exists(supposed_dir):
            return supposed_dir


def get_all_pdb_codes(root='./',
                      pattern='decoys.set*.init'):
    '''need to provide root folder and pattern for folders having pdb codes

    '''
    dir_pattern = root + pattern + '/*.out'
    return [fn.split('/')[-1].split('.')[0] for fn in glob(dir_pattern)
            if fn.endswith('.out') and os.path.isfile(fn)]


def run_min_each_folder(code_dir, job_name, args):
    '''

    Parameters
    ----------
    code_dir : absolute code dir for each pdb
    job_name : name of job
    args : argparse object
    '''
    minus_o = '-O' if args.over_write else ''
    min_type = args.min_type

    idir = iglob(code_dir + '/*' + args.prmtop_ext)
    try:
        first_prmtop = os.path.abspath(next(idir))
        total_cores=args.n_nodes * args.core_per_node
        mpi_words = 'mpirun -n {total_cores} '.format(total_cores=total_cores)
        only_unfinished = '--only-unfinished' if args.only_unfinished else ''

        with temp_change_dir(code_dir):
            # run minimization without restraint
            option_dict = dict(
                job_name=job_name,
                job_type=args.job_type,
                n_nodes=args.n_nodes,
                time=args.time,
                overwrite=minus_o,
                total_cores=total_cores,
                only_unfinished=only_unfinished,
                run_script=args.run_script,
                prmtop=first_prmtop,
                pwd=os.getcwd(),
                rst7_pattern=args.rst7_pattern)

            if min_type in [0, 1]:
                with open('submit.sh', 'w') as fh:
                    minfile = args.root_min_dir + '/min.in'
                    option_dict['minfile'] = minfile
                    sbatch_content = SLURM_TEMPLATE.format(**option_dict)

                    if args.engine != 'mpi':
                        # use multiprocessing
                        sbatch_content = sbatch_content.replace(mpi_words, '')
                    fh.write(sbatch_content)

                if args.submit:
                    cm = args.cmd + ' submit.sh'
                    time.sleep(args.sleep)
                    os.system(cm)

            # run minimization with restraint
            if min_type in [0, 2]:
                try:
                    os.mkdir('no_restraint')
                except OSError:
                    pass
                with temp_change_dir(os.path.abspath('./no_restraint/')):
                    with open('submit.sh', 'w') as fh:
                        minfile = args.root_min_dir + '/min_norestraint.in'
                        option_dict['minfile'] = minfile
                        option_dict['pwd'] = os.getcwd()
                        option_dict['job_name'] = job_name + '.2'
                        option_dict['rst7_pattern'] = '../' + args.rst7_pattern
                        sbatch_content = SLURM_TEMPLATE.format(**option_dict)

                        if args.engine != 'mpi':
                            # use multiprocessing
                            sbatch_content = sbatch_content.replace(mpi_words, '')
                        fh.write(sbatch_content)

                    if args.submit:
                        cm = args.cmd + ' submit.sh'
                        time.sleep(args.sleep)
                        os.system(cm)
    except StopIteration:
        first_prmtop = ''
        print(code_dir)


def get_pdbcodes(args):
    '''

    Parameters
    ----------
    args : argparse object
        check args.code

    Examples
    --------
    >>> args.code = 'all'
    >>> # get all pdb codes
    >>> pdbcodes = get_pdbcodes(args)

    >>> args.code = '1l8r'
    >>> get_pdbcodes(args)
    ['1l8r']
    '''
    return get_all_pdb_codes() if args.code.lower() == 'all' else args.code.split(',')


def submit(pdbcodes):
    for code in pdbcodes:
        print(code)
        code_dir = get_dir_from_code(code)
        if code_dir is not None:
            run_min_each_folder(code_dir, code, args)

if __name__ == '__main__':
    args = parse_args()
    print('submit', args.submit)
    pdbcodes = get_pdbcodes(args)
    submit(pdbcodes)
