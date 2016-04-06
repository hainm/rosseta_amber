#!/usr/bin/env python
import os
import pytraj as pt
from glob import iglob, glob

fns = iglob('min*rst7')

parmlist = glob('*.parm7') 

if not parmlist:
    parmlist = glob('../*.parm7')

top = pt.load_topology(parmlist[0])

failed = []

for fn in fns:
    traj = pt.iterload(fn, top)
    if traj.n_frames == 0:
        failed.append(traj.filename.split('/')[-1])

print('failed', failed)

try:
    os.mkdir('old/')
except OSError:
    pass

for fn in failed:
    os.system('mv {} old/'.format(fn))
