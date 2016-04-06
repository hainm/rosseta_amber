#!/usr/bin/env python

import os
import pandas as pd
import numpy as np
from glob import glob
import pytraj as pt

fn = './bad_energies_rosetta.csv'

df = pd.read_csv(fn, header=None, delim_whitespace=True)
root = '/gpfs/gpfs/project1/dacase-001/haichit/rosseta_amber/DecoyDiscrimination/'
pdb_dirs = [
    root +
    min_fn.replace(
        '../min/',
        '').replace(
            '_score.sc',
        '') for min_fn in df[0]]

# updpate pdb_dirs
for index, pdb in enumerate(pdb_dirs):
    if 'decoys.set1' in pdb:
        pdb_dirs[index] = pdb.replace('decoys.set1', 'decoys.set1.init')
    elif 'decoys.set2' in pdb:
        pdb_dirs[index] = pdb.replace('decoys.set2', 'decoys.set2.init')
    else:
        pdb_dirs[index] = pdb

# get min filenames
_min_files = [pdb_dir + '/no_restraint/' + 'min_NoH_' + x
              for pdb_dir, x in zip(pdb_dirs, df[2])]

end = '_0001'
min_files = []

for mf in _min_files:
    if '0001_0001' in mf:
        min_files.append(mf.replace('0001_0001', '0001') + '.rst7')
    elif '0002_0001' in mf:
        min_files.append(mf.replace('0002_0001', '0002') + '.rst7')
    else:
        min_files.append(mf)

epots = []

for pdb_dir, mf in zip(pdb_dirs, min_files):
    if os.path.exists(mf):
        parmfile = glob(pdb_dir + '/*.parm7')[0]
        traj = pt.iterload(mf, parmfile)
        epots.append(pt.energy_decomposition(traj, igb=8)['tot'][0])
    else:
        epots.append(None)
pt.to_pickle(epots, 'epots.pk')
