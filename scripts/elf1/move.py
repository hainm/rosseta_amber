#!/usr/bin/env python

import os, sys
from glob import iglob, glob
from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.rank

sys.path.append('/project1/dacase-001/haichit/rosseta_amber/DecoyDiscrimination/scripts/elf1/')
from submit_elf1 import temp_change_dir
from run_min import get_total_commands, get_commands_for_my_rank, run_each_core

script = "/project1/dacase-001/haichit/rosseta_amber/DecoyDiscrimination/scripts/elf1/move_unqualified_rst7_files.py"

for fn in get_commands_for_my_rank(glob('./*'), rank):
    if not os.path.isfile(fn):
        # folder
        try:
            with temp_change_dir(fn):
                print(fn)
                os.system('python {}'.format(script))

            no_restraint_fn = fn + '/no_restraint/'

            if os.path.exists(no_restraint_fn):
                with temp_change_dir(no_restraint_fn):
                    print(no_restraint_fn)
                    os.system('python {}'.format(script))
        except IndexError:
            pass
