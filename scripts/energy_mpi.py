'''
Require: mpi4py, pytraj, libsander.
Use `conda install mpi4py` 

Example
-------
    mpirun -n 24  python energy_mpi.py

Note
----
- serial version is here: http://amber-md.github.io/pytraj/latest/tutorials/energy_decomposition.html
- make sure to build prmtop with ff14SB
'''
# load pytraj and mpi4py
import pytraj as pt
from glob import glob
from mpi4py import MPI

# create mpi handler to get cpu rank
comm = MPI.COMM_WORLD 

# load trajectory
# create filenames (could be a single filename or a list of filenames that cpptraj supported)
# (restart file, pdb, netcdf, mdcrd, dcd, ...)
# check more: http://amber-md.github.io/pytraj/latest/trajectory_exercise.html 

# get all minimized rst7 files
filenames = glob('min*rst7')
topology_name = '../1fna.parm7'

# load native struture
nat = pt.iterload('../../../Natives/1fna_0001.clean.pdb')

# create trajectory. Note: use iterload to save memory
traj = pt.iterload(filenames, top=topology_name)

# perform parallel calculation with igb=8: energy
data = pt.pmap_mpi(pt.energy_decomposition, traj, igb=8)

# perform parallel calculation: rmsd, use @CA mask
data_rmsd = pt.pmap_mpi(pt.rmsd, traj, ref=nat, mask='@CA')

# data is a Python dict, it's up to you to save the data
# you can use pt.to_pickle to save the dict to disk and then use pt.read_pickle to reload the dict

# use rank == 0 since pytraj sends output to first cpu.
if comm.rank == 0:
    #print(data)
    # add rmsd to data dict
    data.update(data_rmsd)
    pt.to_pickle(data, 'my_data.pk')

# reload for another analysis
# data = pt.read_pickle('my_data.pk')
# rmsd: data['RMSD_00001']
# potential energy: data['tot'] and so on.
# convert to panda's DataFrame: pd.DataFrame(data)
