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
- If you are not using slurm, please updates SLURM_TEMPLATE


'''

import os
import sys
import time
from copy import deepcopy
import subprocess
from glob import glob, iglob
import argparse
from argparse import RawTextHelpFormatter
from contextlib import contextmanager

sys.path.append('.')
from utils import split_range

THIS_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

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

SLURM_TEMPLATE_HEAD = '''#!/bin/sh
#SBATCH -J {job_name}
#SBATCH -o {job_name}.%J.stdout
#SBATCH -e {job_name}.%J.stderr
#SBATCH -p {job_type}
#SBATCH -N {n_nodes}
#SBATCH -t {time}:00:00'''

SLURM_TEMPLATE_BODY = '''
cd {pwd}
run_script={run_script}
minfile={minfile}
prmtop={prmtop}

mpirun -n {total_cores} $run_script {overwrite} -p $prmtop -c "{rst7_pattern}" -i $minfile {only_unfinished}
'''

def force_mkdir(my_dir):
    try:
        os.mkdir(my_dir)
    except OSError:
        pass

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
        '-jn',
        '--job-name',
        help='job name', 
        default='', type=str)
    parser.add_argument(
        '-d',
        '--root',
        default='./',
        help='root folder having decoy, default ./',
        type=str)
    parser.add_argument(
        '-dp',
        '--decoy-pattern',
        default='decoy*init',
        help='pattern to search for decoy folder, default decoys*init',
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
        help='a single/list of pdb code or "all" (run all codes) or a file having pdblist',
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
        help='pattern to search for rst7 files, default NoH*.rst7', type=str)
    parser.add_argument('-u', '--only-unfinished', action='store_true')
    parser.add_argument(
        '-m',
        '--min-type',
        default=0,
        help='minimization type (default igb=8)\n\t'
             '0: with and without restraint;\n\t'
             '1: with restraint;\n\t'
             '2: no restraint;\n\t'
             '3: with restraint, new min protocol (better);\n\t'
             '4: no restraint, new min protocol (better);\n\t'
             '5: with restraint, new min protocol (better), igb=1 (supposed to have 99sb_igb1 folder);\n\t'
             '6: no restraint, new min protocol (better), igb=1 (supposed to have 99sb_igb1 folder);\n\t'
             '7: restraint all but loop, new min protocol (better); \n\t',
        type=int)
    parser.add_argument(
        '-rs',
        '--run-script',
        default=os.path.join(THIS_SCRIPT_PATH, 'run_min.py'),
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
        default=os.path.join(THIS_SCRIPT_PATH, '../min/'),
        help='extension to search for folder having minimization input (min.in, min_norestraint.in), ./scripts/min/',
        type=str)
    parser.add_argument(
        '-cmd',
        '--cmd',
        default='sbatch',
        help="submit job command, default 'sbatch'", type=str)
    parser.add_argument(
        '-g',
        '--grouping',
        help="group all command to a single script", action='store_true')
    parser.add_argument(
        '-sf',
        '--shuffle',
        help="shuffle commands", action='store_true')
    parser.add_argument(
        '-nc',
        '--n-chunks',
        help='number of nodes, default 1',
        default=1, type=int)

    args = parser.parse_args(sys.argv[1:])
    return args


def get_dir_from_code(code, args):
    dirs = glob(args.root + args.decoy_pattern)
    print('args.root = {}'.format(args.root))
    print('args.decoy_pattern = {}'.format(args.decoy_pattern))
    print('dirs = {}'.format(dirs))

    for code_dir in dirs:
        supposed_dir = os.path.join(args.root, code_dir, code)
        if os.path.exists(supposed_dir):
            return supposed_dir

def get_all_pdb_codes(args):
    '''need to provide root folder and pattern for folders having pdb codes

    '''
    dir_pattern = args.root + args.decoy_pattern + '/*.out'
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

    COMMAND = ''

    if min_type not in [5, 6]:
        idir = iglob(code_dir + '/*' + args.prmtop_ext)
    else:
        idir = iglob(code_dir + '/99sb_igb1/*' + args.prmtop_ext)

    try:
        first_prmtop = os.path.abspath(next(idir))
        print('Using prmtop = {}'.format(first_prmtop))
        total_cores=args.n_nodes * args.core_per_node
        mpi_words = 'mpirun -n {total_cores} '.format(total_cores=total_cores)
        only_unfinished = '--only-unfinished' if args.only_unfinished else ''

        with temp_change_dir(code_dir):
            # run minimization without restraint
            option_dict_head = dict(
                job_name=job_name,
                job_type=args.job_type,
                n_nodes=args.n_nodes,
                time=args.time)
            option_dict_body = dict(
                overwrite=minus_o,
                total_cores=total_cores,
                only_unfinished=only_unfinished,
                run_script=os.path.abspath(args.run_script),
                prmtop=first_prmtop,
                pwd=os.getcwd(),
                rst7_pattern=args.rst7_pattern)

            if min_type in [0, 1]:
                minfile = os.path.abspath(args.root_min_dir) + '/min.in'
                option_dict['minfile'] = minfile
                option_dict = deepcopy(option_dict_head)
                option_dict.update(option_dict_body)

                if not args.grouping:
                    with open('submit.sh', 'w') as fh:
                        sbatch_content = SLURM_TEMPLATE.format(**option_dict)

                        if args.engine != 'mpi':
                            # use multiprocessing
                            sbatch_content = sbatch_content.replace(mpi_words, '')
                        fh.write(sbatch_content)

                    if args.submit:
                        cm = args.cmd + ' submit.sh'
                        time.sleep(args.sleep)
                        os.system(cm)
                else:
                    COMMAND = SLURM_TEMPLATE_BODY.format(option_dict_body)

            extend_min_flags = [0, 2, 3, 4, 5, 6, 7]
            if min_type in extend_min_flags:
                if min_type in [0, 2]:
                    try:
                        os.mkdir('no_restraint')
                    except OSError:
                        pass
                    my_dir = 'no_restraint'
                    minfile = os.path.abspath(args.root_min_dir) + '/min_norestraint.in'
                elif min_type == 3:
                    my_dir = 'restraint_new_protocol'
                    force_mkdir(my_dir)
                    minfile = os.path.abspath(args.root_min_dir) + '/min_new.in'
                elif min_type == 4:
                    my_dir = 'no_restraint_new_protocol'
                    force_mkdir(my_dir)
                    minfile = os.path.abspath(args.root_min_dir) + '/min_norestraint_new.in'
                elif min_type == 5:
                    my_dir = '99sb_igb1/restraint_new_protocol/'
                    force_mkdir(my_dir)
                    minfile = os.path.abspath(args.root_min_dir) + '/min_new_igb1.in'
                elif min_type == 6:
                    my_dir = '99sb_igb1/no_restraint_new_protocol/'
                    force_mkdir(my_dir)
                    minfile = os.path.abspath(args.root_min_dir) + '/min_norestraint_new_igb1.in'
                elif min_type == 7:
                    my_dir = '.'
                    # current folder
                    minfile = os.path.abspath('min.in')
                else:
                    raise ValueError("min_type must be {}".format(str(extend_min_flags)))
                print('Using minfile = {}'.format(minfile))

                option_dict_head['job_name'] = job_name + '.2'
                option_dict_body['minfile'] = minfile
                option_dict_body['pwd'] = os.path.abspath(my_dir)
                if min_type != 7:
                    option_dict_body['rst7_pattern'] = '../' + args.rst7_pattern
                else:
                    option_dict_body['rst7_pattern'] = args.rst7_pattern
                option_dict = deepcopy(option_dict_head)
                option_dict.update(option_dict_body)

                if not args.grouping:
                    with temp_change_dir(os.path.abspath(my_dir)):
                        print('going to {}'.format(my_dir))
                        with open('submit.sh', 'w') as fh:
                            sbatch_content = SLURM_TEMPLATE.format(**option_dict)
                            if args.engine != 'mpi':
                                # use multiprocessing
                                sbatch_content = sbatch_content.replace(mpi_words, '')
                            fh.write(sbatch_content)

                        if args.submit:
                            cm = args.cmd + ' submit.sh'
                            time.sleep(args.sleep)
                            os.system(cm)
                else:
                    COMMAND = SLURM_TEMPLATE_BODY.format(**option_dict_body)
    except StopIteration:
        first_prmtop = ''
        print(code_dir)

    option_dict_tmp = deepcopy(option_dict_head)
    if args.grouping:
        option_dict_tmp['job_name'] = 'rosetta_amber' if not args.job_name else args.job_name
    return COMMAND, SLURM_TEMPLATE_HEAD.format(**option_dict_tmp)


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
    if os.path.isfile(args.code):
        with open(args.code) as fh:
            return fh.read().split()
    else:
        return get_all_pdb_codes(args) if args.code.lower() == 'all' else args.code.split(',')

def write_group_jobs(joblist, SLURM_HEAD, args):
    '''write to ./tmp_submit/ folder

    Parameters
    ----------
    joblist : list of run commands
    SLURM_HEAD : header of slurm sbatch file
    '''

    try:
        os.mkdir('./tmp_submit')
    except OSError:
        pass

    if args.shuffle:
        from random import shuffle
        shuffle(joblist)

    range_tuples = split_range(args.n_chunks, 0, len(joblist))

    for idx, (start, stop) in enumerate(range_tuples):
        slurm_body = '\n'.join(joblist[start:stop])
        fn = './tmp_submit/submit_{}.sh'.format(idx)
        with open(fn, 'w') as fh:
            fh.write(SLURM_HEAD)
            fh.write('\n\n\n')
            fh.write(slurm_body)

def submit(pdbcodes, args):
    joblist = []
    SLURM_HEAD = ''

    for code in pdbcodes:
        print("running code = {}".format(code))
        code_dir = get_dir_from_code(code, args)

        if code_dir is not None:
           slurm_body, SLURM_HEAD = run_min_each_folder(code_dir, code, args)
           joblist.append(slurm_body)
    if args.grouping:
        # not submitting job
        # print(''.join(joblist))
        # print(SLURM_HEAD)
        write_group_jobs(joblist, SLURM_HEAD, args)

if __name__ == '__main__':
    args = parse_args()
    args.run_script = os.path.abspath(args.run_script)
    args.root_min_dir = os.path.abspath(args.root_min_dir)
    print('submit = ', args.submit)
    pdbcodes = get_pdbcodes(args)
    submit(pdbcodes, args)
