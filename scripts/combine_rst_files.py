#!/usr/bin/env python

'''combine a bunch of restart files to a single trajectory for mmgbsa (to do energy decomposition)
'''

import pytraj as pt

# add your files here
rstlist = ['f1.rst', 'f2.rst']

parm = 'f1.parm'

traj = pt.iterload(rstlist, parm)

# save to netcdf format
traj.save('traj.nc')
