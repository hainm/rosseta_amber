#!/usr/bin/env python

'''python generate_rst7_and_parm7.py pdblist_file

What does this script do?
    - strip H
    - generate new parm7 and rst7 files by tleap (will add H).

Require: ParmEd
'''

import os
import sys
from glob import glob, iglob
from contextlib import contextmanager
import parmed as pmd

tleap_template = '''source leaprc.ff14SBonlysc
m = loadpdb NoH_{pdbfile_root}.pdb
set default pbradii mbondi3
saveamberparm m {code}_new.parm7 NoH_{pdbfile_root}.rst7
quit
'''

@contextmanager
def temp_change_dir(new_dir):
    cwd = os.getcwd()
    os.chdir(new_dir)
    yield
    os.chdir(cwd)


def run_tleap(code, pdbfile_root, tleap_template):
    with open('tleap.in', 'w') as fh:
        cm = tleap_template.format(code=code, pdbfile_root=pdbfile_root)
        fh.write(cm)
    os.system('tleap -f tleap.in >& leap.log')

def check_parm7():
    for fn in iglob('*'):
        if not os.path.isfile(fn):
            code = fn.split('.')[0]
            if not os.path.exists(fn + '/' + '{}.parm7'.format(code)):
                    print(code)

def get_pdblist(pdblist_fn):
    if os.path.exists(pdblist_fn):
        with open(pdblist_fn) as fh:
            pdblist = fh.read().split()
    else:
        pdblist = pdblist_fn.split(',')
    return pdblist

def generate_rst7_and_parm7(pdblist):
    for code in pdblist:
        print('processing {}'.format(code))
        with temp_change_dir(code):
            # os.system('cp {code}_new.parm7 {code}.parm7'.format(code=code))
            try:
                for i in range(1, 101):
                    pdbfile = '{i}_relaxed_{code}_0001.pdb'.format(i=i, code=code)
                    parm = pmd.load_file(pdbfile)
                    pdbfile_root = pdbfile.replace('.pdb', '')
                    fn = 'NoH_' + pdbfile
                    # remove H atoms
                    new_parm = parm[[index for index, atom in enumerate(
                        parm.atoms) if atom.atomic_number != 1]]
                    new_parm.save(fn, overwrite=True)
                    run_tleap(code, pdbfile_root, tleap_template)
            except TypeError:
                print('type error: ', code)

if __name__ == '__main__':
    # check_parm7()
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit()
    pdblist_fn = sys.argv[1]
    pdblist = get_pdblist(pdblist_fn)
    generate_rst7_and_parm7(pdblist)
