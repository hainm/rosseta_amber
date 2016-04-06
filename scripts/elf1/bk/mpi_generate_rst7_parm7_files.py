#!/usr/bin/env python

# NOTE: currently works for serial run.
# Why? if parallel, many tleap programs will try to write log to leap.log
# This slows down the making.

'''mpirun -n 24 python mpi_generate_rst7_parm7_files.py pdb_code

Example: mpirun -n 24 python mpi_generate_rst7_parm7_files.py 1vcc

- strip H
- generate new parm7 and rst7 files by tleap (will add H).
'''

import os
import sys
import parmed as pmd
from glob import glob, iglob
from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.rank

_PDBLIST = sys.argv[1]

if os.path.isfile(_PDBLIST):
    with open(_PDBLIST) as fh:
        PDBLIST = fh.read().split()
else:
    PDBLIST = _PDBLIST.split(',')

script_path = '/project1/dacase-001/haichit/rosseta_amber/DecoyDiscrimination/scripts/elf1'
root = '/project1/dacase-001/haichit/rosseta_amber/DecoyDiscrimination/'

sys.path.append(script_path)

from submit_elf1 import temp_change_dir
from run_min import get_commands_for_my_rank, run_each_core

tleap_template = '''logFile log.{pdbfile_root}
source leaprc.ff14SBonlysc
m = loadpdb NoH_{pdbfile_root}.pdb
set default pbradii mbondi3
saveamberparm m {pdbfile_root}.parm7 NoH_{pdbfile_root}.rst7
quit
'''

pdb_pattern = 'empty*.pdb'

def run_tleap(code, pdbfile_root, tleap_template):
    leap_fn = 'tleap.{}.in'.format(pdbfile_root)
    with open(leap_fn, 'w') as fh:
        cm = tleap_template.format(pdbfile_root=pdbfile_root)
        fh.write(cm)
    os.system('tleap -f {}'.format(leap_fn))
    os.remove(leap_fn)
    os.remove('log.{}'.format(pdbfile_root))

for code in PDBLIST:
    with temp_change_dir(code):
        try:
            # os.system('rm *.parm7')
            # os.system('cp {} ./{}.parm7'.format(parmfile, code))
            # parmfile = glob('*.parm7')[0]
            # os.system('cp {parmfile} {code}.parm7'.format(parmfile=parmfile, code=code))
            pdbfiles = glob(pdb_pattern)
            my_pdbfiles = get_commands_for_my_rank(pdbfiles, rank=rank)
            for pdbfile in my_pdbfiles:
                parm = pmd.load_file(pdbfile)
                pdbfile_root = pdbfile.replace('.pdb', '')
                fn = 'NoH_'  + pdbfile
                new_parm = parm[[index for index, atom in enumerate(parm.atoms) if atom.atomic_number != 1]]
                new_parm.save(fn, overwrite=True)
                run_tleap(code, pdbfile_root, tleap_template)
        except TypeError:
            print('type error: ', code)
        except IndexError:
            print('index error: ', code)
